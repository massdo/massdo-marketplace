# Contract tests check documented shapes, not server behavior

The skills of `nestor-beta` document JSON requests for the journal server; this repository ships no MCP implementation. The MCP schemas are captured from `client.listTools()` on an isolated Journal server and stored as fixtures. The Spec and Next-tasks tests validate the documented requests, and the Build tests the documented inputs and outputs, against a captured catalogue. `test_audit_contract.py` checks the audit skill's invocation policy, not the catalogue. These tests do not check selection, ownership, progression, approval or build policies: that behavior belongs to the Journal's own focused tests.

The Build and Spec checks share the captured schemas. `test_audit_contract.py` adds its own directory to `sys.path`, because `python3 -m unittest tests.test_audit_contract` runs from the root, where the sibling module it imports is not importable.

Code:

- `tests/test_build_contract.py`
- `tests/test_next_tasks_contract.py`
- `tests/test_spec_contract.py`
- `tests/test_audit_contract.py`
