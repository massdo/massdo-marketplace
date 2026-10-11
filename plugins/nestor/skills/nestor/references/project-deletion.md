# Confirm project deletion

Pass the loaded Nestor skill's version_hash on every MCP call. Resolve the exact project
and keep its returned version. Do not authorize deletion from a fuzzy project match.

Call manage_project with action prepare_delete, projectId and expectedVersion. Present
the exact project and returned transmissionCount before asking for explicit deletion
confirmation. Keep the returned token and expiry. A preparation is not a deletion.

After the user's confirmation, call manage_project with action confirm_delete, the same
projectId, expectedVersion and token. Report only the confirmed deletedProjectId and
transmissionCount. Do not verify success with an unnecessary read.

If the server returns CONFLICT because captures changed, obtain a new preparation,
present its new transmissionCount and request confirmation of that preparation. Never
reuse approval of an earlier set of captures. A failure or expired token is not success.

Archive is a separate manage_project action. It preserves captures for read-only resume.
The pause and resume skills never invoke this deletion procedure automatically.
