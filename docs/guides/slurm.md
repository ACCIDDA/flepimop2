# Move a flepimop2 workflow from a laptop to Slurm

This guide moves the SIR simulation from [Batch Jobs](batch-jobs.md) to an HPC
cluster that uses Slurm. It walks through a local baseline, project transfer,
cluster environment, configuration, submission, monitoring, and result
comparison. The example was tested on UNC Longleaf; the workflow applies to
other Slurm clusters, but account access, hostnames, storage, software modules,
and scheduler requirements are site-specific. Use your cluster's documentation
for those values.

The `flepimop2-slurm` provider submits jobs to Slurm from the cluster. It does
not connect over SSH or transfer files for you. Slurm schedules the job on a
compute node after resources become available.

## Prerequisites

- A working local environment from the [Batch Jobs guide](batch-jobs.md), using
  its `batch-jobs-guide.zip` project and `configs/config.yaml`.
- An active account and allocation on a Slurm cluster, SSH access (and VPN if
  required by your site), and a file-transfer tool such as `rsync`.
- Git on the cluster to install the Slurm provider from its repository.
- Bash for the cluster shell commands and generated job scripts. If your login
  shell is different, start `bash` after connecting, before running setup commands.
  If you start a nested shell, exit it and then exit the SSH session when returning
  to your laptop. No permanent login-shell change is needed.
- A writable project directory on storage accessible from the login, transfer,
  and compute nodes. Before starting, find your site's login hostname, any
  recommended transfer host, your project storage path, and the Python module
  or environment manager used on compute nodes. Replace the uppercase
  placeholders in commands with values from your cluster's documentation.

!!! note "Longleaf example"
    The tested site is UNC Longleaf. Its account and VPN requirements are in the
    [Longleaf setup guide](https://help.rc.unc.edu/getting-started-on-longleaf/)
    and [account request instructions](https://help.rc.unc.edu/request-a-cluster-account/).
    Here `ONYEN` means your UNC username.

### Choose cluster storage and check permissions

Choose a filesystem according to your cluster's storage policy. Confirm that
the path is writable and visible from compute nodes; login and transfer hosts
may use different filesystems. Check quotas, cleanup rules, and whether the
location is backed up. Access to a job allocation and access to a lab directory
can be separate permissions.

!!! note "Longleaf storage example"
    UNC's [storage migration guide](https://help.rc.unc.edu/storage-migrations-2026)
    directs active work toward `/hickory`. Personal paths are commonly under
    `/hickory/users/{first-letter}/{second-letter}/{ONYEN}`; confirm your assigned
    path before creating the project. For shared work, ask your lab about its
    `/hickory/proj` or `/vast/som` location and [group permissions](https://help.rc.unc.edu/cluster-group-management/).

### Values that vary by cluster

The commands below use the tested Longleaf values. For another site, substitute
its login and transfer hosts, assigned project path, software module or
environment manager, and any required Slurm account or partition. Resource
names and limits can also vary; check the local Slurm documentation before
requesting production resources.

Use login nodes for editing, file management, and submission. Run research
computations through Slurm, including small cluster test simulations.

## 1. Save a local baseline

**On your laptop**, enter the existing example project and activate its environment:

If you use an IDE with a remote-development extension for the cluster, switch to a
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

`python --version` records the local Python version. Use a compatible Python
version on the cluster; this bundle was tested with Python 3.13.

The example starts with 990 susceptible and 10 infectious people and produces
daily output from day 0 through day 60. Expect one CSV in `model_output/local`,
with 61 rows and four columns: time, susceptible, infectious, and recovered.
The CSV has no header and its filename contains a timestamp. Keep this output
for comparison; use an empty directory for each new baseline run.

Create a small requirements file with the versions of the three main Python
packages used by this example. The cluster setup installs from it and uses it to
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

Use your cluster's recommended transfer method and a destination on storage
available to compute nodes. Some centers provide a separate data-transfer host;
others support transfers through the login host or a web portal. From your
laptop, create the destination on the cluster and transfer the project, excluding
the laptop environment and generated outputs:

```bash
ssh YOUR_USER@YOUR_LOGIN_HOST
mkdir -p YOUR_PROJECT_PATH
exit

rsync -av --exclude='venv/' --exclude='.venv/' --exclude='__pycache__/' \
  --exclude='model_output/' --exclude='.flepimop2_cache/' \
  ./ YOUR_USER@YOUR_TRANSFER_HOST:YOUR_PROJECT_PATH/
```

Replace every uppercase placeholder with the actual value supplied by your
cluster. `YOUR_PROJECT_PATH` must be the same absolute path in the `mkdir`,
`rsync`, and later `cd` commands. If your site has no transfer host or prohibits
this method, follow its documented alternative. Include configuration, plugin
scripts, input data, and post-processing scripts. If transferring your own
project with symlinks, ensure their targets are also available on the cluster.
Recreate the environment on Linux; do not copy the laptop's `venv` directory.

!!! note "Longleaf transfer example"
    On Longleaf, connect to `longleaf.unc.edu` to create the destination, then
    use UNC's data-mover host `rc-dm.its.unc.edu` for `rsync`. UNC recommends
    the [Open OnDemand file browser](https://help.rc.unc.edu/ondemand/) for files
    under 10 GB and [Globus](https://help.rc.unc.edu/Getting-Started-with-Globus-Connect/)
    for large transfers. See the [transfer guide](https://help.rc.unc.edu/transferring-files/).

### Optional: edit cluster files from an IDE

If your IDE supports remote development, install its relevant SSH or remote-host
extension and connect to `YOUR_USER@YOUR_LOGIN_HOST`. Open the project using its
full path on the cluster, then confirm the IDE indicates an active remote session
and its file browser shows the remote project before editing
`configs/longleaf.yaml` (the example's cluster configuration). Opening an SSH
terminal in a local IDE window alone does not make the IDE's file browser point
to the cluster copy. The remote IDE session is on a login node: use it to edit
files and submit
`flepimop2 job ...` commands through Slurm, but do not run `flepimop2 simulate`
directly there. Use your cluster's remote shell or file browser if available.
On Longleaf, those tools are available through
[Open OnDemand](https://help.rc.unc.edu/ondemand/).

## 3. Set up the cluster environment

Use the Python version recorded for the local baseline and your cluster's
supported environment tools. If the site uses environment modules, inspect its
module list and use the same Python module when creating the environment and in
the job's setup commands. Install the pinned example dependencies and the Slurm
provider in a Linux environment; do not reuse the laptop's environment.

The following commands are the tested Longleaf setup. For another cluster,
replace the hostname, module name, and environment setup according to its user
guide. The cluster may recommend containers or another environment manager.

```bash
ssh YOUR_USER@YOUR_LOGIN_HOST
cd YOUR_PROJECT_PATH
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

The general practice is to use an isolated, reproducible environment and to
load or activate it explicitly in every batch job. Follow your cluster's policy
for packages, compilation, and interactive allocations.

!!! note "Longleaf environment example"
    UNC's [Python environment guide](https://help.rc.unc.edu/python-packages/)
    recommends isolated environments and warns against loading Python and
    Anaconda modules together. On Longleaf, install conda-managed dependencies
    before pip dependencies and avoid later conda package changes in that environment.

The provider revision above is pinned to the source reviewed for this guide.
Its declared core dependency is `flepimop2>=0.3.0,<1.0.0`. The constraints prevent
installation from silently replacing the local simulation's package versions.
If dependency resolution fails, select a compatible core/provider pair, update
both environments, and regenerate the local baseline.

On subsequent logins, repeat the module loading, shell initialization, and
environment activation commands. Create and install the environment only once.

## 4. Configure the Slurm job target

For this example, keep a separate configuration for the cluster so your local
baseline and scientific settings remain unchanged. On the cluster, copy the
local configuration:

```bash
cp configs/local.yaml configs/longleaf.yaml
```

For the Longleaf example, make site-specific changes only in
`configs/longleaf.yaml`; keep `configs/config.yaml` and the local baseline
configuration separate. Change the backend root to `model_output/longleaf`.
Replace the existing `jobs` block with the following named job; do not add a
second top-level `jobs` key:

When adapting the example to another cluster, you may rename the `longleaf`
job target and `model_output/longleaf` directory to suit your site. Use the
same target name in `--job-target` and update the output path in the retrieval
and comparison steps.

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

| Setting | Local run | Cluster run (Longleaf example) |
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
minutes. This is a small submission check, not a production sizing
recommendation. Follow your site's workload policy; for repeated tests use an
allocated interactive session when available, and combine very short tasks when
the cluster recommends it. Requesting extra CPUs does not automatically make
this solver parallel. The thread environment variables keep numerical libraries
within the single-CPU allocation.

Partition and account rules are site-specific. Add a required account or
partition using the provider's `sbatch-options`; keep resource fields such as
`memory` and `time` in the dedicated configuration keys.

!!! note "Longleaf resource example"
    UNC's [workload guidance](https://help.rc.unc.edu/workload-management/)
    discourages large numbers of short jobs. The tested Longleaf account ran
    with no partition requested and Slurm assigned `spill`; check the
    `Partition` field in `scontrol show job`. UNC's Slurm examples describe
    `general` as a default, but allocation policy can affect scheduling.

Always submit from the project root with the cluster environment active. The
provider uses the submission directory as its default working directory and
renders the command using the submitting environment's executable. Both must
remain accessible from compute nodes. `set -e` makes setup failures stop the
job. Create log directories before submission because Slurm opens logs before
running `pre-commands`. The `command -v flepimop2` line records the executable
path in stdout; it should point into `venv/bin`.

## 5. Inspect and submit

**On the cluster**, from the project root. In this example, `longleaf` is the
configured job target and `demo` is the simulation target:

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

Replace `123456` with your numeric job ID. These standard Slurm commands show
queue state, job details, accounting, and the job's output logs:

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
same directory on the cluster, you can use the provider's job commands:

```bash
flepimop2 job list
flepimop2 job status slurm-123456
seff 123456
```

The provider's status summary may use `seff`, which is not installed on every
cluster. Use the native scheduler commands above if `seff` is unavailable. These
provider commands read the cache in the current project and do not query the
cluster remotely when run on your laptop.

To cancel your job, run `scancel 123456`. Partial outputs remain; use a fresh
output directory when rerunning.

| Symptom | What to check |
| --- | --- |
| Unknown `slurm` module | Install the provider in the environment used by the submitting CLI. |
| `sbatch` missing, including on dry run | Submit from a cluster login environment where Slurm commands are available. |
| Module or executable missing in logs | Use the same available Python module or environment setup during installation and in `pre-commands`; check the environment path. |
| Configuration, plugin, or data not found | Transfer all required files; submit from the project root and replace laptop absolute paths. |
| Output or log permission error | Create directories first; check permissions and storage quota. |
| Invalid account or partition | Use your allocation settings and remove unneeded placeholders. |
| `OUT_OF_MEMORY` or `TIMEOUT` | Inspect accounting and adjust `memory` or `time` before a fresh run. |
| Submission succeeded but no output appeared | Inspect the job state and stderr; verify submission omitted `--dry-run`. |

## 7. Retrieve and compare results

**On your laptop**, from the original project directory. For this example, the
cluster output is under `model_output/longleaf`:

```bash
mkdir -p model_output/longleaf
rsync -av YOUR_USER@YOUR_TRANSFER_HOST:YOUR_PROJECT_PATH/model_output/longleaf/ \
  model_output/longleaf/
conda activate ./venv
```

Replace the placeholders with the same user, transfer host, and project path
used when uploading. If your cluster has no separate transfer host, use its
documented method. On Longleaf, the transfer host is `rc-dm.its.unc.edu`.

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
print("Local and cluster trajectories agree within tolerance.")
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
For many short simulations, follow your site's workload policy; an interactive
allocation or job packing may be more appropriate. The Slurm provider does not
automatically pack separate submissions together.
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

!!! note "Longleaf references"
    See UNC's [Slurm guide](https://help.rc.unc.edu/slurm-guide/),
    [Slurm examples](https://help.rc.unc.edu/longleaf-slurm-examples/), and
    [workload guidance](https://help.rc.unc.edu/workload-management/) for
    Longleaf-specific policies and commands.
