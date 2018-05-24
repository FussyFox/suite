# Getting started

To enable checks for this repository simply add a `.check_suite.yml` file.
This file should contain a list of the check you want to run.

### Sample

```yaml
- pyflakes
- bandit
```

Please note that all entries are case sensitive. If the check is not executed
please double check the correct spelling.

### Available Checks

