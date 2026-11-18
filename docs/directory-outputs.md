# Directory outputs

A step output may be a regular file or a directory below the item's build
directory.

Example:

```yaml
steps:
  - id: collect-results
    run: [python, collect.py]
    outputs:
      - results
```

When `results` is a directory, `tool.cad.ci` hashes every regular file below
it. Relative file paths are sorted before hashing, so filesystem walk order does
not change the result.

Reuse is valid only while:

- the directory still exists;
- every file path in it is unchanged;
- every file content hash is unchanged;
- the step/item inputs are still current.

A symlink anywhere inside a declared output directory is rejected. Declared
output belongs to the item's build tree and may not silently depend on data
outside that tree.

Regular file output hashing is unchanged from v0.2.
