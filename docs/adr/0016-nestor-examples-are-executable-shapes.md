# Nestor examples in Markdown are checked as executable shapes

This repository ships no MCP implementation, yet the Markdown of the journal plugins holds JSON examples that are executable input shapes. Every JSON block in the distributed Markdown of `nestor` and `nestor-beta`, references included, must parse. A `{tool, arguments}` block is checked as a call of that tool and a bare object with `ref` as a `get_item` call; a `{tool, result}` block is a response and is not checked as a call.

Validation catches obsolete tools and malformed conditional reads in every distributed Markdown resource.

Code:

- `scripts/validate.py`: the loop over the `*.md` files of `nestor` and `nestor-beta`
