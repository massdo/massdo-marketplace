---
name: check-for-updates
description: Check whether the Nestor plugin is up to date. Use when the user asks if Nestor is current, wants the latest changelog, or types /nestor:check-for-updates or /check-for-updates.
---

# Check for Nestor updates

Call `probe_plugin_version` with `{ "version": "0.1.5" }`. Always report the result to the user.

- `update_available`: tell the published version and the `action`.
- `up_to_date`: tell the published version. Quote the `changelog` when present.
- `unknown`: say the check could not conclude.

Never write on disk. Never invent a client identifier. This check does not replace a journal operation.
