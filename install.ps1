#requires -Version 5.1
param(
    [ValidateSet('codex', 'claude')][string]$Client,
    [switch]$Check,
    [switch]$NoLogin
)

$ErrorActionPreference = 'Stop'
$plugin = 'nestor@massdo-marketplace'
$endpoint = 'https://journal.mcp-marketplace.org/mcp'
$origin = 'https://journal.mcp-marketplace.org'
$requiredSkills = '["nestor","activity","tree","pause","resume","check-for-updates"]' | ConvertFrom-Json
$script:VerificationError = ''
$script:Installed = $false
$script:Enabled = $false
$script:Marketplace = $false
$processes = New-Object 'System.Collections.Generic.List[System.Diagnostics.Process]'
$scratch = $null
$previousEncoding = [Console]::OutputEncoding
$previousInputEncoding = [Console]::InputEncoding
$previousError = [Console]::Error

function Stop-Installer([string]$Message) {
    [Console]::Error.WriteLine($Message)
    exit 1
}

function Incomplete {
    Write-Output 'Plugin installé — connexion Nestor à terminer'
    if ($Client -ceq 'codex') { Write-Output 'Reprise : codex mcp login nestor' }
    else { Write-Output 'Reprise : claude mcp login plugin:nestor:nestor' }
    Write-Output 'Relancez ensuite cet installateur pour vérifier la connexion.'
    exit 2
}

function Abort-Installation([string]$Message) {
    Stop-Installer $Message
}

function Field($Object, [string]$Name) {
    if ($null -ne $Object) {
        $property = $Object.PSObject.Properties[$Name]
        if ($null -ne $property) { return ,$property.Value }
    }
    return $null
}

function Quote-Argument([string]$Value) {
    # ProcessStartInfo.Arguments uses argv quoting, without a command shell.
    return '"' + [regex]::Replace([regex]::Replace($Value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
}

function New-ClientProcess([string[]]$Arguments, [switch]$Interactive) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $binary
    $info.Arguments = ($Arguments | ForEach-Object { Quote-Argument $_ }) -join ' '
    $info.UseShellExecute = $false
    $info.WorkingDirectory = $scratch
    $info.EnvironmentVariables['NO_COLOR'] = '1'
    $info.RedirectStandardInput = -not $Interactive
    $info.RedirectStandardOutput = -not $Interactive
    $info.RedirectStandardError = -not $Interactive
    if (-not $Interactive) {
        if ($null -ne $info.PSObject.Properties['StandardInputEncoding']) {
            $info.StandardInputEncoding = New-Object System.Text.UTF8Encoding($false)
        }
        $info.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
        $info.StandardErrorEncoding = New-Object System.Text.UTF8Encoding($false)
    }
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    [void]$process.Start()
    $processes.Add($process)
    return $process
}

function Stop-ClientProcess($Process) {
    if (-not $Process.HasExited) {
        try { $Process.Kill($true) } catch {
            if ($env:OS -eq 'Windows_NT') {
                & (Join-Path $env:SystemRoot 'System32/taskkill.exe') /PID $Process.Id /T /F *> $null
            } else { $Process.Kill() }
        }
        [void]$Process.WaitForExit(2000)
    }
    [void]$processes.Remove($Process)
    $Process.Dispose()
}

function Invoke-Client([string[]]$Arguments, [int]$Seconds = 30, [switch]$Interactive) {
    $process = New-ClientProcess $Arguments -Interactive:$Interactive
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    try {
        if (-not $Interactive) {
            $process.StandardInput.Close()
            $output = $process.StandardOutput.ReadToEndAsync()
            $errors = $process.StandardError.ReadToEndAsync()
        }
        if (-not $process.WaitForExit($Seconds * 1000)) {
            return [pscustomobject]@{ Code = 124; Text = '' }
        }
        $text = ''
        if (-not $Interactive) {
            $remaining = [Math]::Max(1, [int]($deadline - [DateTime]::UtcNow).TotalMilliseconds)
            if (-not $output.Wait($remaining)) { return [pscustomobject]@{ Code = 124; Text = '' } }
            $remaining = [Math]::Max(1, [int]($deadline - [DateTime]::UtcNow).TotalMilliseconds)
            if (-not $errors.Wait($remaining)) { return [pscustomobject]@{ Code = 124; Text = '' } }
            $text = $output.GetAwaiter().GetResult()
            [void]$errors.GetAwaiter().GetResult()
        }
        return [pscustomobject]@{ Code = $process.ExitCode; Text = $text }
    } finally { Stop-ClientProcess $process }
}

function Read-ClientJson([string[]]$Arguments, [switch]$Array) {
    $result = Invoke-Client $Arguments
    if ($result.Code -ne 0) { throw 'Client command failed.' }
    if ($Array -and -not $result.Text.TrimStart().StartsWith('[')) { throw 'Invalid array response.' }
    return ConvertFrom-Json -InputObject $result.Text
}

function Read-Plugins {
    $document = Read-ClientJson @('plugin', 'list', '--json') -Array:($Client -ceq 'claude')
    if ($Client -ceq 'codex') {
        $entries = Field $document 'installed'
        if ($entries -isnot [array]) { throw 'Invalid plugin inventory.' }
        $identities = @($entries | Where-Object { ([string](Field $_ 'pluginId')).StartsWith('nestor@') })
        if (@($identities | Where-Object { $_.pluginId -cne $plugin }).Count) {
            Stop-Installer "Collision : un plugin Nestor provient d’une autre marketplace."
        }
        $selected = @($identities | Where-Object { $_.pluginId -ceq $plugin })
    } else {
        $entries = @($document)
        $identities = @($entries | Where-Object {
            (Field $_ 'scope') -cne 'synced' -and ([string](Field $_ 'id')).StartsWith('nestor@')
        })
        if (@($identities | Where-Object { $_.id -cne $plugin -or $_.scope -cne 'user' }).Count) {
            Stop-Installer 'Collision : Nestor possède une autre source ou une autre portée.'
        }
        $selected = @($identities | Where-Object { $_.id -ceq $plugin })
    }
    if ($selected.Count -gt 1) { Stop-Installer 'Collision : plusieurs plugins portent le même nom.' }
    $script:Installed = $selected.Count -eq 1
    $flag = Field $selected[0] 'enabled'
    $script:Enabled = $script:Installed -and ($flag -is [bool]) -and $flag
}

function Read-Marketplace {
    $document = Read-ClientJson @('plugin', 'marketplace', 'list', '--json') -Array:($Client -ceq 'claude')
    if ($Client -ceq 'codex') {
        $entries = Field $document 'marketplaces'
        if ($entries -isnot [array]) { throw 'Invalid marketplace inventory.' }
    } else { $entries = @($document) }
    $selected = @($entries | Where-Object { $_.name -ceq 'massdo-marketplace' })
    if ($selected.Count -gt 1) { Stop-Installer 'Collision : plusieurs marketplaces portent le même nom.' }
    foreach ($entry in $selected) {
        if ($Client -ceq 'codex') {
            $source = Field $entry 'marketplaceSource'
            $valid = (Field $source 'sourceType') -ceq 'git' -and
                (Field $source 'source') -cin @('https://github.com/massdo/massdo-marketplace.git',
                                               'https://github.com/massdo/massdo-marketplace')
        } else {
            $valid = $entry.source -ceq 'github' -and $entry.repo -ceq 'massdo/massdo-marketplace'
        }
        if (-not $valid) { Stop-Installer 'Collision : la marketplace possède une autre source.' }
    }
    $script:Marketplace = $selected.Count -eq 1
}

function Test-ServerCollision {
    if ($Client -ceq 'codex') {
        $entries = @(Read-ClientJson @('mcp', 'list', '--json') -Array)
        $selected = @($entries | Where-Object { $_.name -ceq 'nestor' })
        if ($selected.Count -gt 1) { Stop-Installer 'Collision : plusieurs serveurs portent le nom nestor.' }
        foreach ($entry in $selected) {
            if (-not $script:Installed -or $entry.transport.url -cne $endpoint) {
                Stop-Installer 'Collision : le serveur nestor possède une configuration existante différente.'
            }
        }
    } else {
        if ((Invoke-Client @('mcp', 'get', 'nestor')).Code -eq 0) {
            Stop-Installer 'Collision : un serveur nestor existe hors du plugin.'
        }
        if (-not $script:Installed -and (Invoke-Client @('mcp', 'get', 'plugin:nestor:nestor')).Code -eq 0) {
            Stop-Installer 'Collision : un serveur possède déjà le nom du plugin.'
        }
    }
}

function Invoke-Rpc($Process, [int]$Id, [string]$Method, $Params) {
    $request = @{ id = $Id; method = $Method; params = $Params } | ConvertTo-Json -Compress -Depth 20
    $Process.StandardInput.WriteLine($request)
    $Process.StandardInput.Flush()
    $deadline = [DateTime]::UtcNow.AddSeconds(45)
    while ([DateTime]::UtcNow -lt $deadline) {
        $line = $Process.StandardOutput.ReadLineAsync()
        $remaining = [int]($deadline - [DateTime]::UtcNow).TotalMilliseconds
        if ($remaining -le 0 -or -not $line.Wait($remaining) -or $null -eq $line.Result) {
            throw 'MCP probe timed out or closed.'
        }
        $reply = ConvertFrom-Json -InputObject $line.Result
        if ((Field $reply 'id') -eq $Id) {
            if ($null -ne (Field $reply 'error') -or $null -eq (Field $reply 'result')) {
                throw 'MCP probe failed.'
            }
            return $reply.result
        }
    }
    throw 'MCP probe timed out.'
}

function Test-Codex {
    $script:VerificationError = 'Le serveur Nestor est introuvable ou son contrôle a échoué.'
    $server = Read-ClientJson @('mcp', 'get', 'nestor', '--json')
    $script:VerificationError = 'Le serveur Nestor est désactivé ou possède une autre URL.'
    if ($server.enabled -isnot [bool] -or -not $server.enabled -or $server.transport.url -cne $endpoint) { return 1 }
    $script:VerificationError = 'Le protocole de contrôle Codex a échoué.'
    $process = New-ClientProcess @('app-server', '--stdio')
    $errors = $process.StandardError.ReadToEndAsync()
    try {
        [void](Invoke-Rpc $process 1 'initialize' @{
            clientInfo = @{ name = 'nestor_installer'; version = '1.0.0' }
            capabilities = @{ experimentalApi = $true }
        })
        $process.StandardInput.WriteLine('{"method":"initialized"}')
        $process.StandardInput.Flush()
        $script:VerificationError = 'Les skills Nestor sont absents, désactivés ou illisibles.'
        $skills = Invoke-Rpc $process 2 'skills/list' @{ forceReload = $true }
        $names = @($skills.data | ForEach-Object { $_.skills } |
            Where-Object { $_.enabled -is [bool] -and $_.enabled } | ForEach-Object { $_.name })
        foreach ($skill in $requiredSkills) {
            if ('nestor:' + $skill -cnotin $names) { return 1 }
        }
        $script:VerificationError = 'Le contrôle du serveur Nestor a échoué.'
        $status = Invoke-Rpc $process 3 'mcpServerStatus/list' @{
            serverName = 'nestor'; detail = 'toolsAndAuthOnly'; limit = 100
        }
        $script:VerificationError = 'Le serveur Nestor est absent ou possède une identité différente.'
        $selected = @($status.data | Where-Object {
            $_.name -ceq 'nestor' -and $_.pluginId -ceq $plugin -and $_.httpOrigin -ceq $origin
        })
        if ($selected.Count -ne 1) { return 1 }
        $entry = $selected[0]
        $runtime = Field $entry 'runtimeStatus'
        if ($entry.authStatus -ceq 'notLoggedIn' -or $runtime -ceq 'authRequired') { return 2 }
        $script:VerificationError = "Le type ou l’état d’authentification Nestor ne permet pas le contrôle OAuth."
        if ($entry.authStatus -cne 'oAuth') { return 1 }
        $script:VerificationError = 'Le serveur Nestor est indisponible ou la découverte des outils a échoué.'
        if ($null -ne (Field $entry 'toolsError') -or ($null -ne $runtime -and $runtime -cne 'connected')) { return 1 }
        $script:VerificationError = 'Les outils Nestor requis sont absents de la réponse MCP.'
        $tools = @($entry.tools.PSObject.Properties | ForEach-Object { $_.Value.name })
        if ('get_item' -cnotin $tools) { return 1 }
        return 0
    } finally { Stop-ClientProcess $process }
}

function Plain-Text([string]$Text) { return [regex]::Replace($Text, '\x1B\[[0-9;]*m', '') }

function Test-Claude {
    $script:VerificationError = "L’inventaire des skills Nestor est indisponible."
    $inventory = Invoke-Client @('plugin', 'details', $plugin)
    if ($inventory.Code -ne 0) { return 1 }
    $text = Plain-Text $inventory.Text
    $line = [regex]::Match($text, '(?m)^\s*Skills \(\d+\)[^\r\n]*').Value
    $script:VerificationError = 'Les skills Nestor sont absents ou désactivés.'
    foreach ($skill in $requiredSkills) {
        if ($line -cnotmatch ('(^|[ ,])' + [regex]::Escape($skill) + '([ ,]|$)')) { return 1 }
    }
    $script:VerificationError = 'Le serveur Nestor est indisponible ou son contrôle a échoué.'
    $connection = Invoke-Client @('mcp', 'get', 'plugin:nestor:nestor') 45
    $text = Plain-Text $connection.Text
    $urls = [regex]::Matches($text, '(?m)^\s*URL: ([^\r\n]*)')
    if ($urls.Count -ne 1) { return 1 }
    if ($urls[0].Groups[1].Value.Trim() -cne $endpoint) {
        Stop-Installer 'Collision : le serveur du plugin possède une autre URL.'
    }
    if ([regex]::Matches($text, '(?m)^\s*Status:').Count -ne 1) { return 1 }
    if ($text -cmatch '(?m)^\s*Status: [^\r\n]*Needs authentication\s*$') { return 2 }
    if ($connection.Code -eq 0 -and $text -cmatch '(?m)^\s*Status: ✔ Connected\s*$') { return 0 }
    return 1
}

function Test-Installation {
    try {
        $script:VerificationError = 'Impossible de lire les plugins du client.'
        Read-Plugins
        $script:VerificationError = 'Le plugin Nestor est absent.'
        if (-not $script:Installed) { return 1 }
        $script:VerificationError = "Le plugin Nestor est désactivé. Relancez sans -Check pour l’activer."
        if (-not $script:Enabled) { return 1 }
        if ($Client -ceq 'codex') { return Test-Codex }
        return Test-Claude
    } catch { return 1 }
}

try {
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    # .NET Framework uses Console.InputEncoding when it creates the redirected writer.
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    $errorWriter = New-Object System.IO.StreamWriter([Console]::OpenStandardError(), [Console]::OutputEncoding)
    $errorWriter.AutoFlush = $true
    [Console]::SetError($errorWriter)
    $terminal = -not [Console]::IsInputRedirected -and -not [Console]::IsOutputRedirected
    if (-not $Client) {
        if (-not $terminal) { Stop-Installer 'Sans terminal, indiquez -Client codex ou -Client claude.' }
        $available = @('codex', 'claude') | Where-Object { Get-Command $_ -CommandType Application -ErrorAction SilentlyContinue }
        if (@($available).Count -eq 1) { $Client = @($available)[0] }
        elseif (@($available).Count -eq 2) {
            [Console]::Write('Client à utiliser (codex/claude) : ')
            $Client = [Console]::ReadLine()
        }
        else { Stop-Installer 'Installez Codex ou Claude Code, puis relancez cette commande.' }
    }
    if ($Client -cnotin @('codex', 'claude')) { Stop-Installer 'Client attendu : codex ou claude.' }
    $command = Get-Command $Client -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { Stop-Installer "Client absent : $Client." }
    $binary = $command.Source
    if ([IO.Path]::GetExtension($binary) -in @('.cmd', '.bat', '.ps1')) {
        Stop-Installer 'Utilisez le client natif exécutable, puis relancez cette commande.'
    }
    $scratch = Join-Path ([IO.Path]::GetTempPath()) ('nestor-install-' + [guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Path $scratch)
    foreach ($arguments in @(@('--version'), @('plugin', 'list', '--help'),
            @('plugin', 'marketplace', 'list', '--help'), @('plugin', 'marketplace', 'add', '--help'),
            @('mcp', 'login', '--help'))) {
        if ((Invoke-Client $arguments 15).Code -ne 0) { Stop-Installer 'Client incompatible : mettez le client à jour.' }
    }
    if ($Client -ceq 'codex') { $arguments = @('app-server', '--help') }
    else { $arguments = @('plugin', 'details', '--help') }
    if ((Invoke-Client $arguments 15).Code -ne 0) { Stop-Installer 'Client incompatible : contrôle natif indisponible.' }
    if ($Client -ceq 'codex') { $commands = @('add') }
    else { $commands = @('install', 'enable') }
    foreach ($name in $commands) {
        if ((Invoke-Client @('plugin', $name, '--help') 15).Code -ne 0) {
            Stop-Installer 'Client incompatible : installation ou activation native indisponible.'
        }
    }
    try { Read-Plugins } catch { Stop-Installer 'Impossible de lire les plugins du client.' }
    try { Read-Marketplace } catch { Abort-Installation 'Impossible de lire les marketplaces du client.' }
    try { Test-ServerCollision } catch { Abort-Installation 'Impossible de vérifier la configuration MCP.' }
    if (-not $Check) {
        if (-not $script:Marketplace) {
            if ((Invoke-Client @('plugin', 'marketplace', 'add', 'massdo/massdo-marketplace') 120).Code -ne 0) {
                Abort-Installation 'Ajout de la marketplace impossible. Relancez cette commande.'
            }
            Read-Marketplace
            if (-not $script:Marketplace) { Abort-Installation 'La marketplace ajoutée reste introuvable.' }
        }
        if (-not $script:Installed -or -not $script:Enabled) {
            if ($Client -ceq 'codex') { $arguments = @('plugin', 'add', $plugin, '--json') }
            elseif ($script:Installed) { $arguments = @('plugin', 'enable', $plugin, '--scope', 'user') }
            else { $arguments = @('plugin', 'install', $plugin, '--scope', 'user') }
            $result = Invoke-Client $arguments 120
            if ($result.Code -eq 0) { $script:Installed = $true }
            try { Read-Plugins } catch { Abort-Installation 'Impossible de vérifier le plugin après installation.' }
            if ($result.Code -ne 0 -or -not $script:Installed -or -not $script:Enabled) {
                Abort-Installation 'Installation du plugin impossible. Relancez cette commande.'
            }
        }
    }
    $verification = Test-Installation
    if ($verification -eq 0) { Write-Output 'Installation complète'; exit 0 }
    if ($verification -ne 2) { Stop-Installer $script:VerificationError }
    if ($Check -or $NoLogin -or -not $terminal) { Incomplete }
    [Console]::Write('Ouvrir la connexion Nestor dans le navigateur ? (o/N) : ')
    $answer = [Console]::ReadLine()
    if ($answer -cnotin @('o', 'O', 'oui', 'y', 'Y', 'yes')) { Incomplete }
    $server = 'nestor'
    if ($Client -ceq 'claude') { $server = 'plugin:nestor:nestor' }
    $result = Invoke-Client @('mcp', 'login', $server) 300 -Interactive
    if ($result.Code -ne 0) { Incomplete }
    $verification = Test-Installation
    if ($verification -eq 0) { Write-Output 'Installation complète'; exit 0 }
    if ($verification -eq 2) { Incomplete }
    Stop-Installer $script:VerificationError
} catch {
    Abort-Installation 'Le contrôle du client a échoué. Relancez cette commande.'
} finally {
    foreach ($process in @($processes.ToArray())) { Stop-ClientProcess $process }
    if ($scratch -and (Test-Path -LiteralPath $scratch)) { Remove-Item -LiteralPath $scratch -Recurse -Force }
    [Console]::OutputEncoding = $previousEncoding
    [Console]::InputEncoding = $previousInputEncoding
    [Console]::SetError($previousError)
}
