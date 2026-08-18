---
name: check-for-updates
description: Check whether the Nestor plugin is up to date. Use when the user asks if Nestor is current, wants the latest changelog, or types /nestor:check-for-updates or /check-for-updates.
---

# Check for Nestor updates

Call `probe_plugin_version` with `{ "version": "0.1.6" }`. Report the result to the user in one short sentence, and add nothing else.

- `update_available`: give the published version, then the `action`.
- `up_to_date`: say the plugin is up to date and give the published version. Add the `changelog` verbatim on a second line when that field is present.
- `unknown`: say the check could not conclude.

Report only the fields that the response carries. Never mention an absent field. Never
explain why a field is absent. Never describe how the server decides to send it.

Never write on disk. Never invent a client identifier. This check does not replace a journal operation.
