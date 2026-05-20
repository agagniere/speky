# Test plan style reference

Guidelines for writing Speky test plan steps. These conventions produce test
plans that are readable as documentation, runnable by a human operator, and
straightforward to automate.

## The `expected` field

`expected` holds a **literal excerpt** of the command's stdout or stderr output.
It is not an assertion, not a description, and not an exit code.

| Situation | What to do |
|-----------|------------|
| Command succeeds silently | Omit `expected` — success is exit code 0, there is nothing to match |
| Command produces meaningful output | Include a short excerpt: `expected = "/opt/datadog-packages/datadog-agent/[...]"` |
| Command fails with an error message | Include an excerpt of the error: `expected = "could not download package"` |
| Output contains variable parts | Use `[...]` as a placeholder: `expected = "/opt/packages/[...]/bin/agent"` |

**Never** write a prose description as expected output
(e.g. `expected = "A version directory"`). If you need to describe what the
operator should see, write it in the `action` field instead.

## The `action` field

Describes what the operator does and, when needed, what they should observe.
Keep it in imperative form. When a command is expected to fail or produce a
non-obvious result, say so here:

```toml
action = "Attempt to remove a package that is not installed. The command should fail."
```

```toml
action = "Verify the package is no longer installed. The command should exit with code 10."
```

## The `run` field

A shell command that the operator (or automation) executes. Follow these rules:

### One action per step

Break compound operations into separate steps rather than chaining them with
inline environment variables or command substitution:

```toml
# Good — three separate steps
[[tests.steps]]
action = "Export the API key."
run = "export DD_API_KEY=<API key>"

[[tests.steps]]
action = "Download the install script."
run = "curl --location --output install.sh https://example.com/install.sh"

[[tests.steps]]
action = "Run the install script."
run = "bash install.sh"
```

```toml
# Bad — everything crammed into one step
[[tests.steps]]
action = "Run the install script."
run = "DD_API_KEY=xxx bash -c \"$(curl -L https://example.com/install.sh)\""
```

### Use long-form CLI flags

Prefer `--location` over `-L`, `--output` over `-o`, `--force` over `-f`.
Test plans are documentation; readability matters more than brevity.

### Showing file contents

When a step is about writing or providing a file ("given this config:"), use
`run = "cat <file>"` with `sample` for the content. Do not use `expected` —
the sample is the file to create, not command output:

```toml
[[tests.steps]]
action = "Write the project configuration."
run = "cat config.yaml"
sample_lang = "yaml"
sample = """
name: my-project
version: 1.0
"""
```

### Portable idioms for file checks

Don't rely on the exact wording of error messages from `ls` or `stat` — they
differ across platforms. Use `test` with an explicit fallback:

```toml
[[tests.steps]]
action = "Verify the temporary file was cleaned up."
run = "test -f /tmp/bootstrap || echo 'No such file'"
expected = "No such file"
```

Use `test -f` for files, `test -d` for directories, `test -x` for executables.

### Placeholders for secrets and environment

When a value must be supplied by the operator (API keys, hostnames), use
angle-bracket placeholders:

```toml
run = "export DD_API_KEY=<API key>"
```

If the value is a precondition, list it in `initial` and reference it in
the step with a plain `export`:

```toml
initial = """
- A valid Datadog API key is available.
"""

[[tests.steps]]
action = "Export the API key."
run = "export DD_API_KEY=<API key>"
```

## Preconditions: `prereq` vs `initial`

- **`prereq`**: lists test IDs whose final state is the starting state for this
  test. Use this to build chains (e.g. T000 → T001 → T005 → T010).
- **`initial`**: free-text description of conditions not covered by prereqs
  (e.g. "A Linux host with no Datadog software installed").

Don't repeat in `initial` what a `prereq` already guarantees. Don't state a
precondition and then perform it as the first step — either it's a precondition
(in `initial`) or it's a step.

## Error and failure cases

When a command is expected to fail:

1. State the expectation in `action`:
   `"Attempt to install from an invalid URL. The command should fail."`
2. Include an excerpt of the error output in `expected`:
   `expected = "could not download package"`
3. Do **not** append `; echo $?` — the error message is more informative than
   an exit code.

## Complete example

```toml
kind = "tests"
category = "functional"

[[tests]]
id = "T003"
short = "Bootstrap fails gracefully when registry is unreachable"
long = '''
Validates that the bootstrap process fails cleanly when the OCI registry
cannot be reached, leaving no partial state on disk.
'''
ref = ["FUN-015"]
prereq = ["T000"]

[[tests.steps]]
action = "Point the installer at an unreachable registry."
run = "export DD_INSTALLER_REGISTRY_URL=https://unreachable.invalid"

[[tests.steps]]
action = "Run the bootstrap command. The command should fail."
run = "datadog-installer bootstrap"
expected = "could not download"

[[tests.steps]]
action = "Verify no installer package was left behind."
run = "test -d /opt/datadog-packages/datadog-installer/stable || echo 'No such directory'"
expected = "No such directory"
```
