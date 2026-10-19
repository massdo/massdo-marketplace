#requires -Version 5.1
param(
    [ValidateSet('codex', 'claude')][string]$Client,
    [switch]$Check,
    [switch]$NoLogin
)

$ErrorActionPreference = 'Stop'
$plugin = 'nestor@massdo-marketplace'
$endpoint = 'https://journal.mcp-marketplace.org/mcp'
$script:Installed = $false
$script:Enabled = $false
$script:Marketplace = $false
$processes = New-Object 'System.Collections.Generic.List[System.Diagnostics.Process]'
$scratch = $null
$previousEncoding = [Console]::OutputEncoding

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
    if ($script:Installed) { Incomplete }
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
        $identities = @($entries | Where-Object { ([string](Field $_ 'id')).StartsWith('nestor@') })
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
    $server = Read-ClientJson @('mcp', 'get', 'nestor', '--json')
    if ($server.enabled -isnot [bool] -or -not $server.enabled -or $server.transport.url -cne $endpoint) { return $false }
    $process = New-ClientProcess @('app-server', '--stdio')
    $errors = $process.StandardError.ReadToEndAsync()
    try {
        [void](Invoke-Rpc $process 1 'initialize' @{
            clientInfo = @{ name = 'nestor_installer'; version = '1.0.0' }
            capabilities = @{ experimentalApi = $true }
        })
        $process.StandardInput.WriteLine('{"method":"initialized"}')
        $process.StandardInput.Flush()
        $skills = Invoke-Rpc $process 2 'skills/list' @{ forceReload = $true }
        $names = @($skills.data | ForEach-Object { $_.skills } |
            Where-Object { $_.enabled -is [bool] -and $_.enabled } | ForEach-Object { $_.name })
        foreach ($skill in @('nestor', 'activity', 'tree', 'pause', 'resume', 'check-for-updates')) {
            if ('nestor:' + $skill -cnotin $names) { return $false }
        }
        $status = Invoke-Rpc $process 3 'mcpServerStatus/list' @{
            serverName = 'nestor'; detail = 'toolsAndAuthOnly'; limit = 100
        }
        foreach ($entry in $status.data) {
            $runtime = Field $entry 'runtimeStatus'
            $tools = @($entry.tools.PSObject.Properties | ForEach-Object { $_.Value.name })
            if ($entry.name -ceq 'nestor' -and $entry.pluginId -ceq $plugin -and
                $entry.httpOrigin -ceq 'https://journal.mcp-marketplace.org' -and
                $entry.authStatus -ceq 'oAuth' -and $null -eq (Field $entry 'toolsError') -and
                ($null -eq $runtime -or $runtime -ceq 'connected') -and 'get_item' -cin $tools) {
                return $true
            }
        }
        return $false
    } finally { Stop-ClientProcess $process }
}

function Plain-Text([string]$Text) { return [regex]::Replace($Text, '\x1B\[[0-9;]*m', '') }

function Test-Claude {
    $inventory = Invoke-Client @('plugin', 'details', $plugin)
    if ($inventory.Code -ne 0) { return $false }
    $text = Plain-Text $inventory.Text
    $line = [regex]::Match($text, '(?m)^\s*Skills \(\d+\)[^\r\n]*').Value
    foreach ($skill in @('nestor', 'activity', 'tree', 'pause', 'resume', 'check-for-updates')) {
        if ($line -cnotmatch ('(^|[ ,])' + [regex]::Escape($skill) + '([ ,]|$)')) { return $false }
    }
    $connection = Invoke-Client @('mcp', 'get', 'plugin:nestor:nestor') 45
    $text = Plain-Text $connection.Text
    return $connection.Code -eq 0 -and $text -cmatch '(?m)^\s*Status: ✔ Connected\s*$' -and
        $text -cmatch '(?m)^\s*URL: https://journal[.]mcp-marketplace[.]org/mcp\s*$'
}

function Test-Installation {
    try {
        Read-Plugins
        if (-not $script:Installed -or -not $script:Enabled) { return $false }
        if ($Client -ceq 'codex') { return Test-Codex }
        return Test-Claude
    } catch { return $false }
}

try {
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
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
            @('plugin', 'marketplace', 'list', '--help'), @('mcp', 'login', '--help'))) {
        if ((Invoke-Client $arguments 15).Code -ne 0) { Stop-Installer 'Client incompatible : mettez le client à jour.' }
    }
    if ($Client -ceq 'codex') { $arguments = @('app-server', '--help') }
    else { $arguments = @('plugin', 'details', '--help') }
    if ((Invoke-Client $arguments 15).Code -ne 0) { Stop-Installer 'Client incompatible : contrôle natif indisponible.' }
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
    if (Test-Installation) { Write-Output 'Installation complète'; exit 0 }
    if (-not $script:Installed) { Stop-Installer 'Nestor doit être installé avant ce contrôle.' }
    if ($Check -or $NoLogin -or -not $terminal) { Incomplete }
    [Console]::Write('Ouvrir la connexion Nestor dans le navigateur ? (o/N) : ')
    $answer = [Console]::ReadLine()
    if ($answer -cnotin @('o', 'O', 'oui', 'y', 'Y', 'yes')) { Incomplete }
    $server = 'nestor'
    if ($Client -ceq 'claude') { $server = 'plugin:nestor:nestor' }
    $result = Invoke-Client @('mcp', 'login', $server) 300 -Interactive
    if ($result.Code -ne 0) { Incomplete }
    if (Test-Installation) { Write-Output 'Installation complète'; exit 0 }
    Incomplete
} catch {
    Abort-Installation 'Le contrôle du client a échoué. Relancez cette commande.'
} finally {
    foreach ($process in @($processes.ToArray())) { Stop-ClientProcess $process }
    if ($scratch -and (Test-Path -LiteralPath $scratch)) { Remove-Item -LiteralPath $scratch -Recurse -Force }
    [Console]::OutputEncoding = $previousEncoding
}
