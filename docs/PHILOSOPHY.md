# Basher Philosophy: Command Equivalence

## Core Principle

**When Python code is used instead of shell commands, the output and behavior must match the Linux command analog—so that copying the output allows reproduction without Python.**

## Rationale

Basher wraps common Unix commands. Some operations use Python I/O (e.g. `read_file`, `write_to_file`) for safety or convenience. Regardless of implementation, the user must be able to:

1. **Copy output** from Basher and paste it into a shell
2. **Reproduce the same result** using only native commands
3. **Debug** by comparing Basher output with manual `cat`, `grep`, `find`, etc.

## Command Equivalence Rules

### Output Format = Command Output

| Basher Method        | Linux Analog        | Output Rule                                                                 |
|----------------------|---------------------|-----------------------------------------------------------------------------|
| `read_file(path)`    | `cat path`          | Same string: same bytes, newlines, no extra decoration                     |
| `find(dir, pattern)` | `find dir -name pattern` | Same format: one path per line, newline-separated                          |
| `tail(path, n)`      | `tail -n N path`    | Same output as native `tail`                                                |
| `string_in_file()`   | `grep -q pattern path` | Same exit semantics (True/False → 0/1)                                   |

### Side Effects = Command Side Effects

| Basher Method        | Linux Analog                    | Behavior Rule                                                              |
|----------------------|----------------------------------|----------------------------------------------------------------------------|
| `write_to_file(path, content)` | `printf '%s' "$content" > path` | Same file contents, including newlines and special chars                   |
| `write_to_file(path, content, 'a')` | `printf '%s' "$content" >> path` | Append exactly as shell would                                              |
| `replace_in_file()`  | `sed -i 's|pattern|replacement|' path` | Same line replacement behavior                                            |
| `chmod()`, `chown()` | `chmod`, `chown`                | Same permissions/ownership                                                 |

### Return Values = Exit Codes

- `True` → success (exit code 0)
- `False` → failure (non-zero exit code)
- `None` → command not run or invalid (e.g. file not found)

## Implementation Guidelines

1. **Prefer native commands** when output must be identical to the tool (e.g. `find`, `tail`, `grep`).
2. **Use Python I/O only when necessary** (safety, quoting, complex content)—but ensure output/behavior matches the command analog.
3. **Never add decorations** (e.g. "Found", "No Found", search logs) to return values that are meant to mirror command output.
4. **Quote all user input** passed to shell commands via `shlex.quote()` to prevent injection while preserving equivalence.

## Examples

### Good: Copy-pasteable output

```python
content = bash.read_file("/etc/hosts")
# content is identical to: cat /etc/hosts
# User can copy content and: echo "$content" > /tmp/hosts
```

```python
files = bash.find("/var/log", "*.log")
# files format matches: find /var/log -name "*.log" | cat
# User can pipe to xargs, grep, etc.
```

### Bad: Output that breaks equivalence

```python
# If read_file returned: "=== /etc/hosts ===\n" + content
# User could not re-create the file with a simple: cat > file
```

## Summary

**Basher methods are thin wrappers.** Their output and side effects must be reproducible using only standard Unix commands. If you copy Basher output, you can reproduce it without Python.
