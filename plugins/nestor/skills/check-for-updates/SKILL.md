---
name: check-for-updates
description: Check updates for the Nestor stable skill loaded in this client. Use when the user asks if Nestor stable is current, wants its latest changelog, or types /nestor:check-for-updates or /check-for-updates.
---

# Check for Nestor updates

Call `probe_plugin_version` with `{ "version_hash": "11043de0a13ba515a" }`.
Use this skill's declared hash exclusively, even when another plugin's skill is loaded.
This checks the Nestor stable skill loaded in this client only.

- `update_available`: say `Une mise à jour du plugin Nestor est disponible.` Only this status proves that an update is available. Report it on every manual check, including a second check after changelog acknowledgement.
- `up_to_date`: say `Le plugin Nestor est à jour.`
- `unknown`: say `La vérification du plugin Nestor est inconclusive.` When `diagnostic: hash_unrecognized` is present, explain that the server does not recognize this hash. A missing or unusable catalog (`catalog_unavailable`), or a catalog older than the known client (`catalog_behind`), also remains inconclusive. Never infer an update from an unknown hash or an unverified declared version.
- `INVALID_ARGUMENT`: report that the server refused the Nestor hash; do not announce an update.

If a returned `pluginName` differs from `nestor`, report an inconclusive Nestor check
and the identity mismatch. Do not announce an update for a different plugin.
When `changelog` is present on `update_available` or `up_to_date`, add a second line:
`new features: <changelog>`, replacing `<changelog>` with its content.
Do not add version, action, platform, installation, or automatic-update text.

Report only the fields that the response carries. Never mention an absent field. Never
explain why a field is absent. Never describe how the server decides to send it.

Never write on disk. Never invent a client identifier. This check does not replace a journal operation.
