# Batch Jobs

This guide shows how to use `flepimop2 job` to dispatch a `simulate` or `process` command to a configured job backend instead of executing it locally. The core idea is simple: rather than running the command directly, you describe *where* to run it in the `jobs` section of your configuration file, then call `flepimop2 job <subcommand>` in place of the subcommand alone.

This guide uses the built-in `shell` job module throughout. The `shell` module is intended for **local testing and debugging only** - it simply spawns a subprocess on the same machine. For real-world workloads you should use a job module suited to your computing environment (for example, one that submits to a Slurm cluster or an HPC queue). The `shell` module is a useful starting point because it requires no external infrastructure: you can confirm that the job plumbing works end-to-end before connecting it to a remote backend.

## 1. Start from the Example Bundle

Download [batch-jobs-guide.zip](../downloads/batch-jobs-guide.zip), unzip it, and enter the project:

```bash
unzip batch-jobs-guide.zip
cd batch-jobs-guide
```

Then create and activate the environment:

```bash
just venv
conda activate ./venv
```

The bundle already includes the wrapper-based SIR model from the quickstart example, a scipy engine plugin, and a ready-to-run configuration with a `shell` job backend.

## 2. Add a `jobs` Block to Your Configuration

A job backend is defined in the top-level `jobs` section, alongside `engines`, `systems`, and `backends`. The simplest form is a single unnamed entry, which flepimop2 selects automatically when no target is specified:

```yaml
jobs:
- module: shell
  detach: false
```

The `shell` module accepts two optional fields:

| Field | Default | Description |
|---|---|---|
| `detach` | `true` | If `true`, the subprocess runs detached in a new session and control returns immediately. If `false`, the call blocks until the subprocess exits. |
| `cwd` | *(inherit)* | Working directory for the subprocess. |
| `env` | *(inherit)* | Environment variables for the subprocess. If omitted, the current process environment is inherited. |

Setting `detach: false` is recommended during testing so that output appears inline and the command does not return until the job finishes.

## 3. A Minimal Configuration

Below is a complete, self-contained configuration that includes both a simulation target and a job entry:

```yaml
--8<-- "assets/batch-jobs-guide/configs/config.yaml"
```

## 4. Run the Command via `flepimop2 job`

To dispatch the `simulate` command through the configured job backend instead of running it directly, prefix the subcommand with `flepimop2 job`:

```bash
# Direct execution (runs locally, as before)
flepimop2 simulate -vv configs/config.yaml

# Dispatched through the job backend
flepimop2 job simulate -vv configs/config.yaml
```

Both commands produce the same result with the `shell` module. The difference is that `flepimop2 job simulate` builds a `SimulateCommand` instance, hands it to the configured job backend, and the backend re-invokes `flepimop2 simulate` as a subprocess rather than running the simulation inline.

When the job is submitted, `flepimop2 job` prints a handle that identifies the submitted work unit:

```text
2026-05-26 16:56:24,480:INFO> Job submitted: shell/0 submitted_at=2026-05-26T20:56:24.
```

The token before the `/` is the backend name; the token after is the job identifier (a PID for the `shell` module). More capable backends replace the PID with their own opaque identifier (a Slurm job id, an AWS Batch ARN, etc.).

## 5. Select a Named Job Target

If your configuration defines more than one job backend you can give each a name and select among them with `-j` / `--job-target`:

```yaml
jobs:
  local:
    module: shell
    detach: false
  detached_local:
    module: shell
    detach: true
```

```bash
# Use the 'detached_local' entry
flepimop2 job simulate --job-target detached_local configs/extra-jobs.yaml
```

When exactly one job backend is defined (including the list shorthand form), `-j` can be omitted and the default entry is used automatically.

## 6. Combine with Inner Command Options

All options accepted by the inner command (`simulate` or `process`) work normally when dispatched through `flepimop2 job`. The `--target` flag, for example, selects the simulation target as usual:

```bash
flepimop2 job simulate --target hires configs/config.yaml
flepimop2 job simulate --job-target local --target hires configs/config.yaml
```

## 7. Validate with `--dry-run`

The `--dry-run` flag runs the job backend's preflight checks — for example, verifying that the `flepimop2` executable is on `PATH` — without actually submitting anything. The inner command is never executed:

```bash
flepimop2 job simulate -vvv --dry-run configs/config.yaml
```

Example output:

```text
2026-05-26 16:59:43,433:INFO> Job backend: flepimop2.job.shell.
2026-05-26 16:59:43,433:INFO> Command: simulate /Users/twillard/Downloads/batch-jobs-guide/configs/config.yaml --dry-run -vvv.
2026-05-26 16:59:43,433:INFO> Dry run: preflight checks only, no submission.
```

Without `--dry-run`, the same `-v` output appears before the job handle is printed, letting you verify the backend and reconstructed command on every real submission too.

## 8. Summary

- Add a `jobs:` block to your configuration file to define one or more job backends.
- Replace `flepimop2 <subcommand>` with `flepimop2 job <subcommand>` to dispatch through a backend.
- Use `-j` / `--job-target` to select a named backend when more than one is defined.
- Use `--dry-run` to validate the job setup without submitting.
- The `shell` module is the right tool for local testing; use a purpose-built module for remote or production workloads.

For a full list of options run `flepimop2 job --help` or see the [CLI reference](../reference/cli.md#flepimop2-job).
