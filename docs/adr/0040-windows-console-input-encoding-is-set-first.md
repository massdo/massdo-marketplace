# The Windows installer sets the console input encoding to UTF-8

.NET Framework uses `Console.InputEncoding` when it creates the redirected writer of a child process. `install.ps1` sets `[Console]::InputEncoding` to UTF-8 without a byte order mark, next to `OutputEncoding`, before it starts any client.

On .NET Framework the redirected standard-input writer of a client takes this encoding; where `ProcessStartInfo` has `StandardInputEncoding`, `New-ClientProcess` sets it as well.

Code:

- `install.ps1`: the start of the main `try` block
