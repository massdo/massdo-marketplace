// Test support: runs a hook script as Claude Code does, its JSON input on the standard input.
import { spawn } from "node:child_process";
import path from "node:path";

/** Runs plugin/hooks/<script> with the input and the environment given; the plugin's option is cleared. */
export function runHook(script, input, env = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [path.join(import.meta.dirname, script)], {
      env: { ...process.env, CLAUDE_PLUGIN_OPTION_SERVER_URL: "", ...env },
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => (stdout += chunk));
    child.stderr.on("data", (chunk) => (stderr += chunk));
    child.on("error", reject);
    child.on("close", (status) => resolve({ status, stdout, stderr }));
    child.stdin.end(JSON.stringify(input));
  });
}
