using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text.RegularExpressions;
using System.Threading;

// Windows tests need native executables because production never invokes a shell shim.
class InstallerClientLauncher
{
    static string Quote(string value)
    {
        return "\"" + Regex.Replace(Regex.Replace(value, "(\\\\*)\"", "$1$1\\\""), "(\\\\+)$", "$1$1") + "\"";
    }

    static int Main(string[] args)
    {
        var info = new ProcessStartInfo();
        info.FileName = Environment.GetEnvironmentVariable("NESTOR_TEST_PYTHON");
        var client = Path.GetFileNameWithoutExtension(Assembly.GetExecutingAssembly().Location);
        info.Arguments = Quote(Environment.GetEnvironmentVariable("NESTOR_TEST_FIXTURE")) +
            " --fixture-client " + Quote(client);
        foreach (var arg in args) info.Arguments += " " + Quote(arg);
        info.UseShellExecute = false;
        info.RedirectStandardInput = true;
        info.RedirectStandardOutput = true;
        info.RedirectStandardError = true;
        using (var process = Process.Start(info))
        {
            var input = new Thread(() => {
                try { Console.OpenStandardInput().CopyTo(process.StandardInput.BaseStream); process.StandardInput.Close(); }
                catch (IOException) { }
                catch (ObjectDisposedException) { }
            });
            input.IsBackground = true;
            input.Start();
            var output = process.StandardOutput.BaseStream.CopyToAsync(Console.OpenStandardOutput());
            var error = process.StandardError.BaseStream.CopyToAsync(Console.OpenStandardError());
            process.WaitForExit();
            output.Wait();
            error.Wait();
            return process.ExitCode;
        }
    }
}
