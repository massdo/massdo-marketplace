// Hook SessionStart: checks Node, writes the plugin fingerprint of the session, sends the pending usage reports.
// Nothing is written on the standard output, which Claude Code would add to the conversation.
const MIN_NODE = 22;

const major = Number(process.versions.node.split(".")[0]);
if (major < MIN_NODE) {
  process.stderr.write(
    `Thoth : Node ${String(MIN_NODE)} au moins est requis (version ${process.versions.node}) ; les hooks du plugin restent inactifs.\n`,
  );
  process.exit(0);
}

const path = await import("node:path");
const { PLUGIN_ROOT, pluginFingerprint } = await import("./fingerprint.mjs");
const { readHookInput, readJson, sessionDir, writeJson } = await import("./session-state.mjs");
const { sendPending } = await import("./telemetry.mjs");

const input = await readHookInput();
const manifest = readJson(path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json"), {});
writeJson(path.join(sessionDir(input.session_id), "plugin.json"), {
  fingerprint: pluginFingerprint(),
  version: manifest.version ?? null,
});
await sendPending();
