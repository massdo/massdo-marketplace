// The address of Thoth, which Claude Code gives the hooks from the plugin's option server_url (userConfig).

/** The connection to Thoth, or null while the address is unset. */
export function thothConnection(env = process.env) {
  const url = env.CLAUDE_PLUGIN_OPTION_SERVER_URL;
  if (!url) return null;
  return { url: url.replace(/\/+$/, "") };
}

/** The header that authenticates a hook's call by the Claude Code session it runs for (ADR 0038). */
export const SESSION_HEADER = "x-thoth-session";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** A Claude Code session identifier: a UUID. */
export const isSessionId = (value) => typeof value === "string" && UUID.test(value);
