# The standalone installers embed values that follow the distributed plugin

`install.sh`, `install.ps1` and `uninstall.sh` are downloaded and run on their own. They cannot read repository files at run time, so `install.sh` and `install.ps1` carry their own copy of the Nestor endpoint, its origin and the list of required skills, and `uninstall.sh` carries the endpoint. The values the installers embed must match the plugin this tree distributes: the endpoint and origin of `plugins/nestor/mcp.json`, and the skills of `plugins/nestor/skills`.

Validation fails when an embedded `endpoint`, `origin` or list of required skills differs from the plugin.

Code:

- `scripts/validate.py`: the block that reads `installers` and `uninstaller`
