To enable checks for this repository simply add a `.checks.yml` file.
This file should contain a list of the check you want to run.

### Sample

You can [click here][template] to create a config file for your repository.

```yaml
- pyflakes
- bandit
```

Please note that all entries are case sensitive. If the check is not executed
please double check the correct spelling.

### Available Checks

