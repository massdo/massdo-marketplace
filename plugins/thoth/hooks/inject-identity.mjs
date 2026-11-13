// Hook PreToolUse on the tools of Thoth: adds the session and the plugin fingerprint to the call.
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
      updatedInput: { ...input.tool_input, sessionId: input.session_id, pluginFingerprint: fingerprint },
    },
  }),
);
