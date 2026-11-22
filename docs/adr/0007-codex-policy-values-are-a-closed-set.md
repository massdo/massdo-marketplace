# Codex policy values are checked against a closed set

Codex parses its marketplace catalog into a Rust enum (`codex-rs/core-plugins/src/marketplace.rs`). An unknown variant makes Codex reject the whole file, so the marketplace stops being addable at all. The validator knows the policy values Codex accepts and refuses any other value in the Codex catalog.

A policy value outside `CODEX_POLICY` fails validation.

Code:

- `scripts/validate.py`: `CODEX_POLICY`
