// Hook PreToolUse on the tools of Thoth: adds the session and the plugin fingerprint to the call, and approves it: in
// the auto permission mode, Claude Code denies a call that a hook changes without deciding on it.
import path from "node:path";

import { pluginFingerprint } from "./fingerprint.mjs";
import { readHookInput, readJson, sessionDir } from "./session-state.mjs";

const input = await readHookInput();
const known = readJson(path.join(sessionDir(input.session_id), "plugin.json"), null);
const fingerprint = typeof known?.fingerprint === "string" ? known.fingerprint : pluginFingerprint();
process.stdout.write(
  JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      updatedInput: { ...input.tool_input, sessionId: input.session_id, pluginFingerprint: fingerprint },
    },
  }),
);
