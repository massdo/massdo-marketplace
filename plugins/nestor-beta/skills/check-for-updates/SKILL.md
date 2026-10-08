---
name: check-for-updates
description: Manually check updates for the Nestor Beta skill loaded in this client. Run only on a direct user invocation of /nestor-beta:check-for-updates or $nestor-beta:check-for-updates.
disable-model-invocation: true
---

# Check for Nestor Beta updates

Run only after a direct user invocation.

Call `probe_plugin_version` with `{ "version_hash": "2a2cc476ca4c165c2" }`.
Use this skill's declared hash exclusively, even when another plugin's skill is loaded.
This checks the Nestor Beta skill loaded in this client only.

- `update_available`: tell the user that an update for the Nestor Beta plugin is available. Only this status proves that an update is available. Report it on every manual check, including a second check after changelog acknowledgement.
- `up_to_date`: tell the user that the Nestor Beta plugin is up to date.
- `unknown`: tell the user that the Nestor Beta update check is inconclusive. When `diagnostic: hash_unrecognized` is present, explain that the server does not recognize this hash. A missing or unusable catalog (`catalog_unavailable`), or a catalog older than the known client (`catalog_behind`), also remains inconclusive. Never infer an update from an unknown hash or an unverified declared version.
- `INVALID_ARGUMENT`: report that the server refused the Nestor Beta hash; do not announce an update.

If a returned `pluginName` differs from `nestor-beta`, report an inconclusive Nestor Beta
check and the identity mismatch. Do not announce an update for a different plugin.
When `changelog` is present on `update_available` or `up_to_date`, also report its content:
it describes what is new in the published release.
When `action` is present, do what it asks.

Report only the fields that the response carries. Never mention an absent field. Never
explain why a field is absent. Never describe how the server decides to send it.

Never write on disk, except to run the plugin update the user accepted. Never invent a client identifier. This check does not replace a journal operation.
