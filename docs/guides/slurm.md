# From a Laptop to Slurm: UNC Longleaf

This guide moves the SIR simulation from [Batch Jobs](batch-jobs.md) to UNC
Longleaf. You will transfer the project, recreate its environment, update its
job configuration, and compare the cluster output with a local baseline.

The `flepimop2-slurm` provider submits work to Slurm from the cluster. It does
not connect over SSH or transfer files for you. Slurm chooses a compute node
and runs the simulation there after resources become available.

## Prerequisites

- A working local environment from the [Batch Jobs guide](batch-jobs.md), using
  its `batch-jobs-guide.zip` project and `configs/config.yaml`.
- An active Longleaf account, SSH, and a file-transfer tool such as `rsync`.
  An ONYEN alone is not cluster access: follow the
  [account request instructions](https://help.rc.unc.edu/request-a-cluster-account/)
  and wait for the account-ready email.
- Git on Longleaf to install the Slurm provider from its repository.
- Bash for the cluster shell commands and generated job scripts. If your login
  shell is different, start `bash` after connecting, before running setup commands.
  If you start a nested shell, exit it and then exit the SSH session when returning
  to your laptop. No permanent login-shell change is needed.
- A writable project directory on a filesystem accessible from login, data-mover,
  and compute nodes. `ONYEN` and `/absolute/shared/path` below are placeholders:
  replace them with your username and confirmed full project path before running
  any command. Do not type `/absolute/shared/path` literally.

Follow UNC's [Longleaf setup instructions](https://help.rc.unc.edu/getting-started-on-longleaf/)
for VPN requirements when off campus and cluster access.

### Choose storage and check permissions

UNC's [September 2026 migration guidance](https://help.rc.unc.edu/storage-migrations-2026)
directs active work toward `/hickory`. Personal storage is normally under
`/hickory/users/{o}/{n}/{onyen}`, where `{o}` and `{n}` are the first two letters
of your ONYEN. Confirm the directory assigned to your account before creating
the project. Lab storage may be under `/hickory/proj` or `/vast/som`; ask your
lab for its current path. Older examples showing `/work`, `/users`, or `/proj`
may not match your account's migration status.

Here, a filesystem accessible across cluster nodes does not mean a directory
shared with other researchers. Use personal storage for your own test and a
lab-managed location for collaborative data, following UNC's
[storage guidance](https://help.rc.unc.edu/storage).

Slurm account membership and lab filesystem access are separate permissions.
Being affiliated with a PI for job submission does not grant access to that
PI's files. Follow the [group-access guidance](https://help.rc.unc.edu/cluster-group-management/)
if you cannot write to the lab's directory. Keep important results in backed-up
storage after retrieving them.

Use login nodes for editing, file management, and submission. Run research
computations through Slurm, including small cluster test simulations.

## 1. Save a local baseline

**On your laptop**, enter the existing example project and activate its environment:

If you use an IDE with a remote-development extension for Longleaf, switch to a
local IDE window for this step. The baseline and its `venv` must be on your
laptop.

```bash
cd batch-jobs-guide
conda activate ./venv
cp configs/config.yaml configs/local.yaml
mkdir -p model_output/local
```

In `configs/local.yaml`, change only the CSV backend's output directory:

```yaml
backends:
  - module: csv
    root: model_output/local
```

Keep the model, solver, parameters, and `demo` simulation target unchanged. Run:

```bash
flepimop2 simulate --target demo configs/local.yaml
python --version
```

`python --version` confirms the local Python version. Use the same major and
minor version when creating the Longleaf environment; this bundle uses Python
3.13.

The example starts with 990 susceptible and 10 infectious people and produces
daily output from day 0 through day 60. Expect one CSV in `model_output/local`,
with 61 rows and four columns: time, susceptible, infectious, and recovered.
The CSV has no header and its filename contains a timestamp. Keep this output
for comparison; use an empty directory for each new baseline run.

Create a small requirements file with the versions of the three main Python
packages used by this example. Longleaf setup installs from it and uses it to
keep the Slurm provider compatible. It pins these packages, not every
transitive dependency in the environment:

```bash
python -c 'from importlib.metadata import version; print("\n".join(f"{name}=={version(name)}" for name in ("flepimop2", "numpy", "scipy")))' > requirements-simulation.txt
```

!!! note "Adapting this guide to another project"
    If flepimop2 comes from a Git checkout or an unpublished development
    version, replace its line with a direct reference to that exact commit,
    such as `flepimop2 @ git+https://github.com/ACCIDDA/flepimop2.git@COMMIT_SHA`.
    Use the full commit hash rather than `main`. For a different model, also
    include its additional dependencies and record the provider version used.

## 2. Transfer the project

**From your laptop**, connect to Longleaf, create the destination, and log out:

```bash
ssh ONYEN@longleaf.unc.edu
mkdir -p /absolute/shared/path/batch-jobs-guide
exit
```

Back in the local `batch-jobs-guide` directory, transfer through UNC's data-mover
host, `rc-dm.its.unc.edu`, using the same destination path:

```bash
rsync -av --exclude='venv/' --exclude='.venv/' --exclude='__pycache__/' \
  --exclude='model_output/' --exclude='.flepimop2_cache/' \
  ./ ONYEN@rc-dm.its.unc.edu:/absolute/shared/path/batch-jobs-guide/
```

UNC recommends data-mover nodes for command-line transfers rather than tying up
login nodes. The [transfer guide](https://help.rc.unc.edu/transferring-files/)
also recommends the [Open OnDemand file browser](https://help.rc.unc.edu/ondemand/)
for files under 10 GB, and [Globus](https://help.rc.unc.edu/Getting-Started-with-Globus-Connect/)
for large transfers. Use the method appropriate to your dataset; log into
`longleaf.unc.edu` for the setup and submission steps below.

Include configuration, plugin scripts, input data, and any post-processing
scripts. The existing downloadable bundle includes the wrapper model and solver
as ordinary files. If transferring your own project with symlinks, ensure their
targets are also available on the cluster. Recreate the environment on Linux;
do not copy the laptop's `venv` directory.

### Optional: edit the Longleaf files from an IDE

If your IDE supports remote development, install its relevant SSH or remote-host
extension and connect to `ONYEN@longleaf.unc.edu`. Open the project using its
full path on Longleaf, then confirm the IDE indicates an active remote session
and its file browser shows the remote project before editing
`configs/longleaf.yaml`. Opening an SSH terminal in a local IDE window alone
does not make the IDE's file browser point to the cluster copy. The remote IDE
session is on a login node: use it to edit files and submit
`flepimop2 job ...` commands through Slurm, but do not run `flepimop2 simulate`
directly there. UNC also provides a browser-based shell and file browser through
[Open OnDemand](https://help.rc.unc.edu/ondemand/).

## 3. Set up the cluster environment

**On Longleaf**, enter the transferred project. UNC's
[Slurm examples](https://help.rc.unc.edu/longleaf-slurm-examples/) use
`anaconda/2024.02`. Check `module avail anaconda` and use an available module
consistently here and in the job configuration in the next section.

```bash
ssh ONYEN@longleaf.unc.edu
cd /absolute/shared/path/batch-jobs-guide
module purge
module load anaconda/2024.02
source "$(conda info --base)/etc/profile.d/conda.sh"
conda create --prefix "$PWD/venv" python=3.13 pip -y
conda activate "$PWD/venv"
python -c 'import sys; print(sys.executable); print(sys.version)'
python -m pip install -r requirements-simulation.txt
python -m pip install -c requirements-simulation.txt \
  "flepimop2-slurm @ git+https://github.com/ACCIDDA/flepimop2-extras.git@3ae75a2937eb093e8b7b3e6113fa808ccb0f2ec8#subdirectory=packages/flepimop2-slurm"
python -m pip check
mkdir -p model_output/longleaf logs batch_scripts
```

Before installing, confirm the printed interpreter is in this project's
`venv/bin` directory. After installation, check `command -v flepimop2` too;
it should point into the same environment. If either points elsewhere, fix
activation before continuing.

Follow site policy for package installation and use an allocated session if
substantial compilation is required. This example needs NumPy and SciPy but
does not run the bundle's R post-processing.

UNC's [Python environment guide](https://help.rc.unc.edu/python-packages/)
recommends isolated environments and warns against loading Python and Anaconda
modules together. Install conda-managed dependencies before using pip; avoid
later conda package changes in that environment. The job must explicitly load
its modules and activate its environment as well.

The provider revision above is pinned to the source reviewed for this guide.
Its declared core dependency is `flepimop2>=0.3.0,<1.0.0`. The constraints prevent
installation from silently replacing the local simulation's package versions.
If dependency resolution fails, select a compatible core/provider pair, update
both environments, and regenerate the local baseline.

On subsequent logins, repeat the module loading, shell initialization, and
environment activation commands. Create and install the environment only once.

## 4. Update the configuration for Longleaf

**On Longleaf**, copy the local configuration:

```bash
cp configs/local.yaml configs/longleaf.yaml
```

Make Longleaf-specific changes only in `configs/longleaf.yaml`; keep
`configs/config.yaml` and the local baseline configuration separate. Change the
backend root to `model_output/longleaf`. Replace the existing `jobs` block with
the following named job; do not add a second top-level `jobs` key:

```yaml
jobs:
  longleaf:
    module: slurm
    nodes: 1
    ntasks: 1
    cpus-per-task: 1
    memory: 2G
    time: '00:05:00'
    sbatch-directory: batch_scripts
    sbatch-options:
      output: logs/%j.out
      error: logs/%j.err
    pre-commands:
      - set -e
      - module purge
      - module load anaconda/2024.02
      - source "$(conda info --base)/etc/profile.d/conda.sh"
      - conda activate "$PWD/venv"
      - command -v flepimop2
      - export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
```

| Setting | Local run | Longleaf run |
| --- | --- | --- |
| Model, solver, parameters, time grid | Existing SIR example | Unchanged |
| Backend output root | `model_output/local` | `model_output/longleaf` |
| Job backend | Direct execution, or local `shell` | `slurm` |
| Environment | Laptop environment | Recreated Linux environment |
| Input/plugin paths | Relative to project root | Same paths after transfer |
| Logs | Terminal | `logs/JOB_ID.out` and `logs/JOB_ID.err` |

Use `jobs`, as in the core [Batch Jobs guide](batch-jobs.md); some provider README
examples use the singular `job`. The provider uses hyphenated resource keys,
including `cpus-per-task`, and accepts resource values such as `memory: 2G`.

The example requests one task with one CPU on one node, 2 GB RAM, and five
minutes. This is a small submission-validation exercise, not a production sizing
recommendation. UNC's [workload guidance](https://help.rc.unc.edu/workload-management/)
discourages short-running jobs, especially large numbers of them. For repeated
tests, use an allocated interactive session; for production, combine useful work
within an allocation rather than submitting a separate job for every tiny run.
Do not add artificial delays just to lengthen jobs. Requesting extra CPUs does
not automatically make this solver parallel. The thread environment variables
keep numerical libraries within the single-CPU allocation.

Leave the partition unspecified for this Longleaf example unless your
allocation instructions say otherwise. UNC's guide describes `general` as the
default for ordinary CPU work, but the tested account's job was assigned to
`spill` with no partition requested. Check the `Partition` field in
`scontrol show job` rather than assuming which partition Slurm selected. If
your allocation requires an account, add `account: YOUR_ACCOUNT` under
`sbatch-options`; for another cluster, add its required `partition` there.
Keep `memory`, `time`, and other dedicated resource fields outside
`sbatch-options`.

Always submit from the project root with the cluster environment active. The
provider uses the submission directory as its default working directory and
renders the command using the submitting environment's executable. Both must
remain accessible from compute nodes. `set -e` makes setup failures stop the
job. Create log directories before submission because Slurm opens logs before
running `pre-commands`. The `command -v flepimop2` line records the executable
path in stdout; it should point into `venv/bin`.

## 5. Inspect and submit

**On Longleaf**, from the project root:

```bash
flepimop2 job simulate --job-target longleaf --target demo \
  -vvv --dry-run configs/longleaf.yaml
ls batch_scripts/
```

Open the generated `.batch` file reported by the dry run. Check its resource
directives, paths, activation commands, and final simulation command. Dry run
requires `sbatch` on `PATH`, so run it on the cluster. It writes the script but
does not submit a job, verify allocation access, or test compute-node execution.

Do not submit the dry-run script manually: its inner command can retain
`--dry-run`. Submit through flepimop2 again without that flag:

```bash
flepimop2 job simulate --job-target longleaf --target demo \
  -vv configs/longleaf.yaml
```

Record the returned handle, such as `slurm-123456`. Submission success means
Slurm accepted the job; it does not mean the simulation completed. Keep the
configuration, environment, and input files unchanged while the job is queued
or running.

## 6. Monitor and troubleshoot

Replace `123456` with your numeric job ID. UNC's
[Slurm guide](https://help.rc.unc.edu/slurm-guide/) explains these commands:

```bash
squeue -j 123456
scontrol show job 123456
sacct -j 123456 --format=JobID,State,ExitCode,Elapsed,MaxRSS
cat logs/123456.out
cat logs/123456.err
```

`PENDING` means the job is waiting; check the reason before resubmitting. A job
disappearing from `squeue` does not prove success. Check for `COMPLETED`, exit
code `0:0`, and a new CSV in `model_output/longleaf`.

The submitting project also records the job in `.flepimop2_cache`. From that
same directory on Longleaf, you can use:

```bash
flepimop2 job list
flepimop2 job status slurm-123456
seff 123456
```

The provider uses `seff` for status. Use `squeue` for live queue state and inspect
resource efficiency after completion; running-job efficiency figures may be
incomplete. If `seff` is unavailable, use the native scheduler commands above.
These commands do not remotely query Longleaf when run on your laptop.

To cancel your job, run `scancel 123456`. Partial outputs remain; use a fresh
output directory when rerunning.

| Symptom | What to check |
| --- | --- |
| Unknown `slurm` module | Install the provider in the environment used by the submitting CLI. |
| `sbatch` missing, including on dry run | Submit on Longleaf with its scheduler commands available. |
| Module or executable missing in logs | Use the same available Anaconda module in setup and `pre-commands`; check the environment path. |
| Configuration, plugin, or data not found | Transfer all required files; submit from the project root and replace laptop absolute paths. |
| Output or log permission error | Create directories first; check permissions and storage quota. |
| Invalid account or partition | Use your allocation settings and remove unneeded placeholders. |
| `OUT_OF_MEMORY` or `TIMEOUT` | Inspect accounting and adjust `memory` or `time` before a fresh run. |
| Submission succeeded but no output appeared | Inspect the job state and stderr; verify submission omitted `--dry-run`. |

## 7. Retrieve and compare results

**On your laptop**, from the original project directory:

```bash
mkdir -p model_output/longleaf
rsync -av ONYEN@rc-dm.its.unc.edu:/absolute/shared/path/batch-jobs-guide/model_output/longleaf/ \
  model_output/longleaf/
conda activate ./venv
```

Run the following block in a shell terminal from the project root, not at the
Python `>>>` prompt. Keep the opening and closing `PY` markers at the far left.
It requires exactly one CSV in each directory so runs cannot be mixed silently.

```bash
python - <<'PY'
from pathlib import Path

import numpy as np

local_files = list(Path("model_output/local").glob("*.csv"))
cluster_files = list(Path("model_output/longleaf").glob("*.csv"))
assert len(local_files) == len(cluster_files) == 1, "Select one run per directory"
local = np.loadtxt(local_files[0], delimiter=",")
cluster = np.loadtxt(cluster_files[0], delimiter=",")
assert local.shape == cluster.shape == (61, 4)
assert np.isfinite(local).all() and np.isfinite(cluster).all()
np.testing.assert_allclose(local[:, 0], np.arange(61), rtol=0, atol=0)
np.testing.assert_allclose(cluster[:, 0], local[:, 0], rtol=0, atol=0)
np.testing.assert_allclose(cluster[:, 1:], local[:, 1:], rtol=1e-6, atol=1e-8)
print("Local and Longleaf trajectories agree within tolerance.")
PY
```

This is a proposed tolerance for the deterministic example, allowing small
floating-point differences. If comparison fails, check configuration, plugin
files, solver settings, and the pinned direct package versions before changing
the tolerance.
Stochastic models require seeds and model-appropriate statistical comparisons.
Use your usual local plotting tools to inspect the returned trajectories.

## Moving to larger workflows

Use a small cluster run to measure elapsed time and memory before scaling up.
For many short simulations, use job packing or an interactive allocation as
described in UNC's workload guidance; the Slurm provider does not automatically
pack separate submissions together.
Give concurrent jobs separate output directories. Preserve the configuration,
input files, package manifests, generated scripts, logs, and job ID with results.

For configured post-processing, submit `flepimop2 job process` with the same job
target after the simulation has successfully completed, and install any required
Python/R dependencies in the cluster environment. Two independent submissions
do not automatically establish a Slurm dependency. Inference workflows need
their actual fitting entry point and dependencies; moving to a cluster does not
introduce an inference command, automatic parallelism, or resumable execution.

For other Slurm clusters, adapt the hostname, shared storage location, modules,
activation, account, and partition using that site's instructions and the
[Slurm provider reference](https://github.com/ACCIDDA/flepimop2-extras/tree/main/packages/flepimop2-slurm).
