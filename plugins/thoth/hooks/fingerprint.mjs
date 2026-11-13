// The fingerprint of the plugin, which every call to Thoth carries and each release registers.
import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

/** The plugin folder: the one above hooks/. */
export const PLUGIN_ROOT = path.resolve(import.meta.dirname, "..");

/** Git and the hidden files that operating systems add are left out. */
const IGNORED = new Set([".git", ".DS_Store", "Thumbs.db", "desktop.ini"]);
const ignored = (name) => IGNORED.has(name) || name.startsWith("._");

/**
 * At the root, the only hidden entries of the plugin: Claude Code writes its own markers there in the installed
 * folder (`.in_use`, `.orphaned_at`), which must not change the fingerprint registered at release.
 */
const ROOT_HIDDEN_KEPT = new Set([".claude-plugin", ".mcp.json"]);
const ignoredAtRoot = (name) => name.startsWith(".") && !ROOT_HIDDEN_KEPT.has(name);

/** The files of a folder, as sorted POSIX paths relative to it. */
export function pluginFiles(root) {
  const files = [];
  const walk = (folder) => {
    for (const entry of readdirSync(folder, { withFileTypes: true })) {
      if (ignored(entry.name) || (folder === root && ignoredAtRoot(entry.name))) continue;
      const full = path.join(folder, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.isFile()) files.push(path.relative(root, full).split(path.sep).join("/"));
    }
  };
  walk(root);
  return files.sort();
}

/** « sha256:<hex> » over the sorted relative paths and the contents of every file of the plugin. */
export function pluginFingerprint(root = PLUGIN_ROOT) {
  const hash = createHash("sha256");
  for (const file of pluginFiles(root)) {
    const content = readFileSync(path.join(root, file));
    hash.update(`${file}\0${String(content.length)}\0`);
    hash.update(content);
  }
  return `sha256:${hash.digest("hex")}`;
}
