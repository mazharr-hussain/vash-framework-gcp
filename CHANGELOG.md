# Changelog

All notable changes to this project will be documented in this file.
This is a hand-written seed for bootstrap stage A; it will be engine-generated in the future.

## [Unreleased]
### Added
- Initial repository scaffolding, governance, security policies, and the build system.
- Added the VASH method and AvA protocol (Step 2).
- Added the core engine, interfaces, registry and freeze loading (Step 3).
- Added GitHub, CI, OCI, Ollama and OpenAI-compatible adapters (Step 4).
- Added Stage 0 and Gate 1 deterministic tools (Step 5).
- Added the CLI, loader and AvA runner (Step 6).
- Added the catalog, stack packs, scaffold and OCI IaC (Step 7).
- Added VASH's own CI, templates and freeze (Step 8).
- Packaged method, catalog and scaffold in the wheel; `pip install` works without `VASH_HOME`.
- Added `vash onboard oci`: one Cloud Shell command creates the Always Free runner VM and installs VASH, terraform and Ollama.
- Added iteration mode (agile delivery): optional `delivery` block in the freeze, FEATURE activities with their checklist, and `feature:`/`iteration:` traced in every AvA log.
- Added portable skills and agents: `vash skill new|validate|suggest`, `vash agent new`, project skills/ and agents/, AGENTS.md and .agents/skills/ for every coding tool, skills in prompts for plain model APIs, Gate 1 rule G1-13 (official skills-ref validator) and rule R15.
- Renamed the skill prompt-engineer to prompt-engineering (agents are roles, skills are know-how); the agent keeps prompt-engineer.
- Fixed `vash onboard oci` in OCI Cloud Shell (FIPS mode): reuses id_ed25519 or id_rsa, and falls back to RSA 4096 when ed25519 is refused.
- `vash onboard oci`: `--subnet-id` reuses an existing public subnet (no network created, SSH rule checked); the compartment name is asked (default `vash`) or given with `--compartment`, and a new one is created only after a yes.
- `vash onboard oci`: optional inventory of compartments, VCNs and subnets (numbered table with owner), delete by S.No or OCID after a dependency check (in-use objects blocked) and a final yes, and pick an existing public subnet from the table.
- Bootstrap: always reinstalls VASH (the version number does not change between fixes, so a plain upgrade kept old code).
- `vash onboard oci`: no hardcoded object names (prefix: default `vash` after a yes, else typed; `<prefix>-runner`, `<prefix>-vcn` ...), existing VMs listed and reusable (install over SSH, never deleted), SSH key chosen by the owner (new `<prefix>-key` on no, never overwritten).
- `vash onboard oci`: VMs can be deleted from the inventory (boot volume deleted, block volumes detached and kept, VM first so its IPs do not block its subnet or VCN, name typed to confirm).
- `vash onboard oci`: compartments that hold resources are emptied with Oracle's compartment cleaner (oci-automation-hub, pinned; dry-run plan, Resource Manager backup, typed DELETE, Cloud Shell sign-in added); the table uses direct listings (no search lag); "Continue with the VASH VM setup now?" after cleanup, and `--cleanup-only`.
- Catalog: UPL-1.0 allowed; vendor-first rule; LAW 3 search record for the OCI tools.
- IaC: network and VM now use Oracle's CD3 Automation Toolkit modules (v2026.2.2); VASH's own network and compute modules are removed. The free-tier database keeps VASH's module (CD3's adb module has no free-tier option).
- `vash onboard oci`: the dependency check names who holds each IP (the VM, or the service created with the VNIC), a VM name gets 3 tries, and the table shows progress while it reads.
- Fixed: the owner lookup sends the time in the form OCI Search accepts, and a failed lookup shows "owner unknown" instead of stopping the run.
- `vash onboard oci`: deletes continue after a failure (each failure reported with OCI's own message, stdout included), a VM is terminated and then polled (the CLI's --wait-for-state failed in Cloud Shell), and the IP owner guess only considers services that create VNICs.
- `vash onboard oci`: the inventory covers the whole tenancy (this region): every other resource from Resource Search; such a resource is removed through its compartment with Oracle's cleaner, or in the Console when it is in the root.
- `vash onboard oci`: the inventory covers every subscribed region and every parent or child tenancy the login can reach (Tenancy and Region columns); deletes, dependency checks and the cleaner go to the object's own region; Resource Search and the cleaner stay in the signed-in tenancy.
