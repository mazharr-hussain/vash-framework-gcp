# VASH onboarding

One command in OCI Cloud Shell creates an Always Free Arm VM and installs VASH on it.

```bash
curl -fsSL https://raw.githubusercontent.com/mazharr-hussain/vash-framework/main/bootstrap/oci-cloudshell.sh | bash
```

What it does (`vash onboard oci`):

0. Asks whether to check everything: every subscribed region of this tenancy, and every parent or child tenancy (OCI Organizations) this login can reach (others are named as "no access"): compartments, VCNs, subnets and VMs from direct listings, and every other resource (databases, buckets, vaults, load balancers, volumes ...) from Resource Search, automatic sub-parts left out, and shows them in one table (S.No, type, name, state, the compartment or VCN each belongs to, public or not, OCID). It then asks whether to delete any: you give S.No or OCIDs, comma separated. For each choice it lists what would also be deleted (a VCN's subnets, gateways, route tables, lists) and what still uses it (IPs of VMs, databases or load balancers in a subnet, peering or DRG attachments, resources in a compartment); anything in use is blocked. Only the free ones are offered, with one last yes/no. A compartment that still holds resources is emptied with Oracle's compartment cleaner (oracle-devrel/oci-automation-hub, pinned): its dry-run plan first, then after a yes a Resource Manager backup stack in the root compartment, the tool's own "type DELETE", deletion and a final check; sub-compartments must be removed first. A VM can be deleted too: the check shows its boot volume (deleted with it) and attached block volumes (detached and kept), its own IPs do not block its subnet or VCN in the same batch (VMs go first), and its name must be typed after the last yes. Then it offers a running VM from the table to install VASH on (Ubuntu or Debian, over SSH: no new VM, no terraform), else a public subnet for a new VM (Enter = create a new network).
   Names: "Use the default name prefix 'vash'?" and "Use the default compartment 'vash'?"; on n you type your own (for example north, south or your name), and new objects are called <prefix>-runner, <prefix>-vcn, <prefix>-subnet. SSH key: each existing key is offered with a yes/no; on n a new key <prefix>-key is created (no file is ever overwritten), and a VM built earlier keeps its key.
1. Reads the tenancy and region from Cloud Shell, asks for the compartment name (default `vash`), and reuses it or, after a yes, creates it.
2. Checks the free A1 quota in each availability domain and keeps those with 2 cores and 12 GB free.
3. Picks the latest Ubuntu 24.04 Arm image, creates an SSH key if there is none, and opens SSH to this shell's IP only.
4. Asks once, then runs terraform on `iac/oci/environments/always-free`; on "Out of host capacity" it tries the next domain.
5. The VM installs on first boot: Python, git, terraform, VASH, Ollama with `qwen2.5-coder:7b`, and the GitHub Actions runner files.
6. Waits until the VM reports ready, then prints the SSH command.

Options (after `bash -s --`):

- `--runner-repo owner/name`: register the VM as a self-hosted runner. The token is asked at a prompt and sent over SSH stdin; it is never written to a file.
- `--ocpus 4 --memory 24`: a bigger VM (the whole free A1 allowance).
- `--admin-cidr x.x.x.x/32`: who may SSH in (only for the network VASH creates).
- `--subnet-id <ocid>`: use an existing public subnet instead of creating a network (for example when the free VCN limit is reached). It must allow SSH (TCP 22); VASH checks it and never changes it.
- `--compartment <name>`: the compartment to use. Without it, VASH asks for the name (Enter keeps `vash`); a compartment that does not exist is created only after a yes.
- `--yes`: do not ask before creating (the inventory and every delete are skipped).
- `--no-inventory`: skip step 0.
- `--cleanup-only`: only the inventory and deletes; no VM setup. Without it, onboarding asks "Continue with the VASH VM setup now?" after the cleanup.
- `--name-prefix north`: names of new objects (skips the question).
- `--vm-ip x.x.x.x --ssh-user ubuntu --ssh-key ~/.ssh/key`: install on an existing VM.
- `--down`: remove the VM and its network.

Running it again is safe: the terraform state lives in `~/.vash/oci`, the earlier domain and image are kept, and terraform only repairs what drifted.
