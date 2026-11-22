# The Windows installer starts processes without a command shell

`install.ps1` starts the client through `ProcessStartInfo`, whose `Arguments` string uses argv quoting and involves no command shell. `Quote-Argument` quotes each argument under the argv rules. The Windows tests use a native executable as the client double, because production never invokes a shell shim.

A `.cmd` or `.ps1` shim cannot stand in for a client in the Windows tests.

Code:

- `install.ps1`: `Quote-Argument`
- `tests/fixtures/installer_client_launcher.cs`: `InstallerClientLauncher`
