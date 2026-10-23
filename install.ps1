#requires -Version 5.1
param(
    [ValidateSet('codex', 'claude', 'claude-ai', 'chatgpt')][string]$Client,
    [switch]$Check,
    [switch]$NoLogin
)

$ErrorActionPreference = 'Stop'
$plugin = 'nestor@massdo-marketplace'
$endpoint = 'https://journal.mcp-marketplace.org/mcp'
$origin = 'https://journal.mcp-marketplace.org'
# claude.ai and ChatGPT have no command line: Nestor is added from these pages.
$claudeAiPage = 'https://claude.ai/customize/connectors'
$chatGptPage = 'https://chatgpt.com/plugins'
$requiredSkills = '["nestor","activity","tree","pause","resume","check-for-updates"]' | ConvertFrom-Json
$script:VerificationError = ''
$script:ClientError = ''
$script:Installed = $false
$script:Enabled = $false
$script:Marketplace = $false
$processes = New-Object 'System.Collections.Generic.List[System.Diagnostics.Process]'
$scratch = $null
$previousEncoding = [Console]::OutputEncoding
$previousInputEncoding = [Console]::InputEncoding
$previousError = [Console]::Error

function Write-ClientError {
    if ($script:ClientError) {
        foreach ($line in @($script:ClientError.TrimEnd() -split '\r?\n' | Select-Object -Last 12)) {
            [Console]::Error.WriteLine($line)
        }
    }
}

function Stop-Installer([string]$Message) {
    [Console]::Error.WriteLine($Message)
    Write-ClientError
    exit 1
}

function Incomplete([switch]$Retry) {
    Write-Output 'Nestor is installed — finish connecting your account'
    $command = 'codex mcp login nestor'
    if ($Client -cne 'codex') { $command = 'claude mcp login plugin:nestor:nestor' }
    if ($Retry) {
        [Console]::Error.WriteLine($script:VerificationError)
        Write-ClientError
        Write-Output "Try again: restore your connection to Nestor, then run this setup command again."
        Write-Output "If you are asked to sign in afterward, run: $command"
        exit 2
    }
    Write-Output "To continue, run: $command"
    Write-Output 'Then run this setup command again to check the connection.'
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

function Stop-ClientProcess($Process, $Errors = $null) {
    if (-not $Process.HasExited) {
        try { $Process.Kill($true) } catch {
            if (-not $Process.HasExited) {
                if ($env:OS -eq 'Windows_NT') {
                    & {
                        $ErrorActionPreference = 'SilentlyContinue'
                        & (Join-Path $env:SystemRoot 'System32/taskkill.exe') /PID $Process.Id /T /F *> $null
                    }
                } else { $Process.Kill() }
            }
        }
        [void]$Process.WaitForExit(2000)
    }
    if ($null -ne $Errors -and $Errors.Wait(1000)) {
        $errorText = $Errors.GetAwaiter().GetResult()
        if ($errorText) { $script:ClientError = $errorText }
    }
    [void]$processes.Remove($Process)
    $Process.Dispose()
}

function Invoke-Client([string[]]$Arguments, [int]$Seconds = 30, [switch]$Interactive) {
    $script:ClientError = ''
    $process = New-ClientProcess $Arguments -Interactive:$Interactive
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    try {
        if (-not $Interactive) {
            $process.StandardInput.Close()
            $output = $process.StandardOutput.ReadToEndAsync()
            $errors = $process.StandardError.ReadToEndAsync()
        }
        if (-not $process.WaitForExit($Seconds * 1000)) {
            $script:ClientError = "The app did not respond in time ($Seconds s)."
            return [pscustomobject]@{ Code = 124; Text = '' }
        }
        $text = ''
        if (-not $Interactive) {
            $remaining = [Math]::Max(1, [int]($deadline - [DateTime]::UtcNow).TotalMilliseconds)
            if (-not $output.Wait($remaining)) {
                $script:ClientError = "The app did not respond in time ($Seconds s)."
                return [pscustomobject]@{ Code = 124; Text = '' }
            }
            $remaining = [Math]::Max(1, [int]($deadline - [DateTime]::UtcNow).TotalMilliseconds)
            if (-not $errors.Wait($remaining)) {
                $script:ClientError = "The app did not respond in time ($Seconds s)."
                return [pscustomobject]@{ Code = 124; Text = '' }
            }
            $text = $output.GetAwaiter().GetResult()
            $errorText = $errors.GetAwaiter().GetResult()
            if ($process.ExitCode -ne 0) { $script:ClientError = $errorText }
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
    if ($Client -ceq 'codex') {
        # Without a marketplace name, Codex also refreshes its remote plugin
        # catalog, which can take longer than the time budget on a cold cache.
        $document = Read-ClientJson @('plugin', 'list', '--json', '-m', 'massdo-marketplace')
        $entries = Field $document 'installed'
        if ($entries -isnot [array]) { throw 'Invalid plugin inventory.' }
        $selected = @($entries | Where-Object { ([string](Field $_ 'pluginId')) -ceq $plugin })
    } else {
        $document = Read-ClientJson @('plugin', 'list', '--json') -Array
        $entries = @($document)
        $identities = @($entries | Where-Object {
            (Field $_ 'scope') -cne 'synced' -and ([string](Field $_ 'id')).StartsWith('nestor@')
        })
        if (@($identities | Where-Object { $_.id -cne $plugin -or $_.scope -cne 'user' }).Count) {
            Stop-Installer 'Collision: an existing Nestor installation has a different source or scope.'
        }
        $selected = @($identities | Where-Object { $_.id -ceq $plugin })
    }
    if ($selected.Count -gt 1) { Stop-Installer 'Collision: multiple plugins have the same name.' }
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
    if ($selected.Count -gt 1) { Stop-Installer 'Collision: multiple marketplaces have the same name.' }
    foreach ($entry in $selected) {
        if ($Client -ceq 'codex') {
            $source = Field $entry 'marketplaceSource'
            $valid = (Field $source 'sourceType') -ceq 'git' -and
                (Field $source 'source') -cin @('https://github.com/massdo/massdo-marketplace.git',
                                               'https://github.com/massdo/massdo-marketplace')
        } else {
            $valid = $entry.source -ceq 'github' -and $entry.repo -ceq 'massdo/massdo-marketplace'
        }
        if (-not $valid) { Stop-Installer 'Collision: the marketplace uses a different source.' }
    }
    $script:Marketplace = $selected.Count -eq 1
}

function Test-ServerCollision {
    if ($Client -ceq 'codex') {
        $entries = @(Read-ClientJson @('mcp', 'list', '--json') -Array)
        $selected = @($entries | Where-Object { $_.name -ceq 'nestor' })
        if ($selected.Count -gt 1) { Stop-Installer 'Collision: multiple servers use the name nestor.' }
        foreach ($entry in $selected) {
            if (-not $script:Installed -or $entry.transport.url -cne $endpoint) {
                Stop-Installer 'Collision: the existing nestor server has a different configuration.'
            }
        }
    } else {
        if ((Invoke-Client @('mcp', 'get', 'nestor')).Code -eq 0) {
            Stop-Installer 'Collision: a nestor server already exists outside the plugin.'
        }
        if (-not $script:Installed -and (Invoke-Client @('mcp', 'get', 'plugin:nestor:nestor')).Code -eq 0) {
            Stop-Installer 'Collision: an existing server already uses the plugin name.'
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
    $script:VerificationError = 'Cannot find or check the Nestor server.'
    $server = Read-ClientJson @('mcp', 'get', 'nestor', '--json')
    $script:VerificationError = 'The Nestor server is disabled or uses a different URL.'
    if ($server.enabled -isnot [bool] -or -not $server.enabled -or $server.transport.url -cne $endpoint) { return 1 }
    $script:VerificationError = 'Cannot communicate with Codex to check Nestor.'
    $process = New-ClientProcess @('app-server', '--stdio')
    $errors = $process.StandardError.ReadToEndAsync()
    try {
        [void](Invoke-Rpc $process 1 'initialize' @{
            clientInfo = @{ name = 'nestor_installer'; version = '1.0.0' }
            capabilities = @{ experimentalApi = $true }
        })
        $process.StandardInput.WriteLine('{"method":"initialized"}')
        $process.StandardInput.Flush()
        $script:VerificationError = 'Nestor skills are missing, disabled or unreadable.'
        $skills = Invoke-Rpc $process 2 'skills/list' @{ forceReload = $true }
        $names = @($skills.data | ForEach-Object { $_.skills } |
            Where-Object { $_.enabled -is [bool] -and $_.enabled } | ForEach-Object { $_.name })
        foreach ($skill in $requiredSkills) {
            if ('nestor:' + $skill -cnotin $names) { return 1 }
        }
        $script:VerificationError = 'Cannot check the Nestor server.'
        $status = Invoke-Rpc $process 3 'mcpServerStatus/list' @{
            serverName = 'nestor'; detail = 'toolsAndAuthOnly'; limit = 100
        }
        $script:VerificationError = 'The Nestor server is missing or has an unexpected identity.'
        $selected = @($status.data | Where-Object {
            $_.name -ceq 'nestor' -and $_.pluginId -ceq $plugin -and $_.httpOrigin -ceq $origin
        })
        if ($selected.Count -ne 1) { return 1 }
        $entry = $selected[0]
        $runtime = Field $entry 'runtimeStatus'
        if ($entry.authStatus -ceq 'notLoggedIn' -or $runtime -ceq 'authRequired') { return 2 }
        $script:VerificationError = "Cannot verify the Nestor sign-in status."
        if ($entry.authStatus -cne 'oAuth') { return 1 }
        $script:VerificationError = 'Cannot reach Nestor or load its tools.'
        if ($null -ne (Field $entry 'toolsError') -or ($null -ne $runtime -and $runtime -cne 'connected')) { return 3 }
        $script:VerificationError = 'Required Nestor tools are missing from the server response.'
        $toolEntries = $entry.tools
        if ($toolEntries -isnot [array]) { $toolEntries = @($toolEntries.PSObject.Properties | ForEach-Object { $_.Value }) }
        $tools = @($toolEntries | ForEach-Object { $_.name })
        if ('get_item' -cnotin $tools) { return 1 }
        return 0
    } finally { Stop-ClientProcess $process $errors }
}

function Plain-Text([string]$Text) { return [regex]::Replace($Text, '\x1B\[[0-9;]*m', '') }

function Test-Claude {
    $script:VerificationError = "Cannot read the list of Nestor skills."
    $inventory = Invoke-Client @('plugin', 'details', $plugin)
    if ($inventory.Code -ne 0) { return 1 }
    $text = Plain-Text $inventory.Text
    $line = [regex]::Match($text, '(?m)^\s*Skills \(\d+\)[^\r\n]*').Value
    $script:VerificationError = 'Nestor skills are missing or disabled.'
    foreach ($skill in $requiredSkills) {
        if ($line -cnotmatch ('(^|[ ,])' + [regex]::Escape($skill) + '([ ,]|$)')) { return 1 }
    }
    $script:VerificationError = 'Cannot reach or check the Nestor server.'
    $connection = Invoke-Client @('mcp', 'get', 'plugin:nestor:nestor') 45
    $text = Plain-Text $connection.Text
    $urls = [regex]::Matches($text, '(?m)^\s*URL: ([^\r\n]*)')
    if ($urls.Count -ne 1) { return 1 }
    if ($urls[0].Groups[1].Value.Trim() -cne $endpoint) {
        Stop-Installer 'Collision: the plugin server uses a different URL.'
    }
    if ([regex]::Matches($text, '(?m)^\s*Status:').Count -ne 1) { return 1 }
    if ($text -cmatch '(?m)^\s*Status: [^\r\n]*Needs authentication\s*$') { return 2 }
    if ($text -cmatch '(?m)^\s*Status: ([^\r\n]*Failed to connect|[^\r\n]*Connected · tools fetch failed)\s*$') { return 3 }
    if ($connection.Code -eq 0 -and $text -cmatch '(?m)^\s*Status: ✔ Connected\s*$') { return 0 }
    return 1
}

# claude.ai and ChatGPT have no command line: Nestor is added from their own
# page, so the wizard shows the steps, offers to open that page, and cannot
# check what the browser did.
function Show-Guide([bool]$Terminal) {
    if ($Client -ceq 'claude-ai') {
        $label = 'claude.ai'
        $page = $claudeAiPage
        Write-Output 'Nestor is added to claude.ai from its Connectors page. The steps:'
        Write-Output "1. Open $page and sign in."
        Write-Output '2. Click Add, then Add custom connector.'
        Write-Output "3. Name: Nestor — URL: $endpoint — then click Continue."
        Write-Output '4. Keep the sign-in settings Claude detected and click Continue, then Add.'
        Write-Output '5. Sign in to Nestor when asked and allow the connection.'
        Write-Output '6. In a conversation, click +, then Connectors, and turn Nestor on.'
    } else {
        $label = 'ChatGPT'
        $page = $chatGptPage
        Write-Output 'Nestor is added to ChatGPT from its Plugins page. The steps:'
        Write-Output "1. Open $page and sign in."
        Write-Output '2. Click +, then Add custom MCP server.'
        Write-Output "3. Name: Nestor — under Connection, URL: $endpoint"
        Write-Output '4. Keep the OAuth sign-in, accept the warning, then click Create as a plugin.'
        Write-Output '5. Install the plugin, then sign in to Nestor when asked and allow the connection.'
        Write-Output '6. In a new conversation, type @ and pick Nestor.'
    }
    if ($Terminal -and -not $Check -and -not $NoLogin) {
        [Console]::Write("Open $label in your browser now? (y/N): ")
        $answer = [Console]::ReadLine()
        if ($answer -cin @('o', 'O', 'oui', 'y', 'Y', 'yes')) {
            try {
                Start-Process $page
                Write-Output 'Opening your browser. Follow the steps above, then come back to this window.'
            } catch {
                Write-Output "Cannot open a browser from here. Open $page yourself."
            }
        }
    }
    Write-Output "Finish the steps above in your browser, then open a new conversation in $label and type: Show my tasks."
    exit 0
}

function Test-Installation {
    try {
        $script:VerificationError = 'Cannot read the installed plugins in your app.'
        Read-Plugins
        $script:VerificationError = 'The Nestor plugin is not installed.'
        if (-not $script:Installed) { return 1 }
        $script:VerificationError = "The Nestor plugin is disabled. Run setup without -Check to enable it."
        if (-not $script:Enabled) { return 1 }
        if ($Client -ceq 'codex') { return Test-Codex }
        return Test-Claude
    } catch {
        if (-not $script:ClientError) { $script:ClientError = $_.Exception.Message }
        return 1
    }
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
        if (-not $terminal) { Stop-Installer 'Without a terminal, specify -Client codex, claude, claude-ai or chatgpt.' }
        # The browser apps are always offered: their state cannot be read.
        $choices = @(@('codex', 'claude') | Where-Object { Get-Command $_ -CommandType Application -ErrorAction SilentlyContinue }) + @('claude-ai', 'chatgpt')
        [Console]::Write("Choose your app ($($choices -join '/')): ")
        $Client = [Console]::ReadLine()
        if ($Client -ceq 'claude.ai') { $Client = 'claude-ai' }
    }
    if ($Client -cnotin @('codex', 'claude', 'claude-ai', 'chatgpt')) { Stop-Installer 'Choose codex, claude, claude-ai or chatgpt.' }
    if ($Client -cin @('claude-ai', 'chatgpt')) { Show-Guide $terminal }
    $command = Get-Command $Client -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { Stop-Installer "Client not found: $Client." }
    $binary = $command.Source
    if ([IO.Path]::GetExtension($binary) -in @('.cmd', '.bat', '.ps1')) {
        Stop-Installer 'Use the native app executable, then run this setup command again.'
    }
    $scratch = Join-Path ([IO.Path]::GetTempPath()) ('nestor-install-' + [guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Path $scratch)
    foreach ($arguments in @(@('--version'), @('plugin', 'list', '--help'),
            @('plugin', 'marketplace', 'list', '--help'), @('plugin', 'marketplace', 'add', '--help'),
            @('mcp', 'login', '--help'))) {
        if ((Invoke-Client $arguments 15).Code -ne 0) { Stop-Installer 'This app version is not supported. Update your app, then run this setup command again.' }
    }
    if ($Client -ceq 'codex') { $arguments = @('app-server', '--help') }
    else { $arguments = @('plugin', 'details', '--help') }
    if ((Invoke-Client $arguments 15).Code -ne 0) { Stop-Installer 'This app version cannot check Nestor. Update your app and try again.' }
    if ($Client -ceq 'codex') { $commands = @('add') }
    else { $commands = @('install', 'enable') }
    foreach ($name in $commands) {
        if ((Invoke-Client @('plugin', $name, '--help') 15).Code -ne 0) {
            Stop-Installer 'This app version cannot install or enable plugins. Update your app and try again.'
        }
    }
    try { Read-Plugins } catch { Stop-Installer 'Cannot read the installed plugins in your app.' }
    try { Read-Marketplace } catch { Abort-Installation 'Cannot read the marketplaces in your app.' }
    try { Test-ServerCollision } catch { Abort-Installation 'Cannot check the MCP server configuration.' }
    if (-not $Check) {
        if (-not $script:Marketplace) {
            if ((Invoke-Client @('plugin', 'marketplace', 'add', 'massdo/massdo-marketplace') 120).Code -ne 0) {
                Abort-Installation 'Cannot add the marketplace. Check the error below, then run this setup command again.'
            }
            Read-Marketplace
            if (-not $script:Marketplace) { Abort-Installation 'The marketplace is still missing after setup tried to add it.' }
        }
        if (-not $script:Installed -or -not $script:Enabled) {
            if ($Client -ceq 'codex') { $arguments = @('plugin', 'add', $plugin, '--json') }
            elseif ($script:Installed) { $arguments = @('plugin', 'enable', $plugin, '--scope', 'user') }
            else { $arguments = @('plugin', 'install', $plugin, '--scope', 'user') }
            $result = Invoke-Client $arguments 120
            if ($result.Code -ne 0) { Abort-Installation 'Cannot install or enable Nestor. Check the error below, then run this setup command again.' }
            $script:Installed = $true
            try { Read-Plugins } catch { Abort-Installation 'Cannot check Nestor after installing it.' }
            if (-not $script:Installed -or -not $script:Enabled) {
                Abort-Installation 'Cannot install or enable Nestor. Check the error below, then run this setup command again.'
            }
        }
    }
    $verification = Test-Installation
    if ($verification -eq 0) { Write-Output 'Installation complete'; exit 0 }
    if ($verification -eq 3) { Incomplete -Retry }
    if ($verification -ne 2) { Stop-Installer $script:VerificationError }
    if ($Check -or $NoLogin -or -not $terminal) { Incomplete }
    [Console]::Write('Open your browser to connect Nestor? (y/N): ')
    $answer = [Console]::ReadLine()
    if ($answer -cnotin @('o', 'O', 'oui', 'y', 'Y', 'yes')) { Incomplete }
    $server = 'nestor'
    if ($Client -ceq 'claude') { $server = 'plugin:nestor:nestor' }
    $result = Invoke-Client @('mcp', 'login', $server) 300 -Interactive
    if ($result.Code -ne 0) { Incomplete }
    $verification = Test-Installation
    if ($verification -eq 0) { Write-Output 'Installation complete'; exit 0 }
    if ($verification -eq 3) { Incomplete -Retry }
    if ($verification -eq 2) { Incomplete }
    Stop-Installer $script:VerificationError
} catch {
    Abort-Installation ('Client check failed: ' + $_.Exception.Message)
} finally {
    foreach ($process in @($processes.ToArray())) { Stop-ClientProcess $process }
    if ($scratch -and (Test-Path -LiteralPath $scratch)) { Remove-Item -LiteralPath $scratch -Recurse -Force }
    [Console]::OutputEncoding = $previousEncoding
    [Console]::InputEncoding = $previousInputEncoding
    [Console]::SetError($previousError)
}
