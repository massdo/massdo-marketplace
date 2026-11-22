# Spinners stop through a flag file, and processes stop quietly

A spinner is `gum spin` running a command. It may have to be stopped from a shell that is not its parent. When a shell kills a background job, it prints its own "Terminated" notice. A spinner is `gum spin` waiting for a flag file; stopping it creates the file, so it ends cleanly even from a shell that is not its parent. `stop_process` wraps its `kill` and `wait` calls in braces with stderr discarded, which also silences the shell's notice for the job.

The shell prints no "Terminated" notice for a job that `stop_process` stops.

Code:

- `install.sh`: `stop_process`, `spinner_start`
- `uninstall.sh`: `spinner_start`
