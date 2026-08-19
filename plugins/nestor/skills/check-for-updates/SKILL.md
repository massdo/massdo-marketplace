---
name: check-for-updates
description: Check whether the Nestor plugin is up to date. Use when the user asks if Nestor is current, wants the latest changelog, or types /nestor:check-for-updates or /check-for-updates.
---

# Check for Nestor updates

Call `probe_plugin_version` with `{ "version_hash": "918aceaf0fa6e0b8" }`.

- `update_available`: say exactly `Une mise à jour est disponible.` When `changelog` is present, add a second line: `new features: <changelog>`, replacing `<changelog>` with its content. Do not report the version, action, platform, installation, or automatic-update text.
- `up_to_date`: say the plugin is up to date. When `changelog` is present, add a second line: `new features: <changelog>`, replacing `<changelog>` with its content.
- `unknown`: say the check could not conclude.

Report only the fields that the response carries. Never mention an absent field. Never
explain why a field is absent. Never describe how the server decides to send it.

Never write on disk. Never invent a client identifier. This check does not replace a journal operation.
