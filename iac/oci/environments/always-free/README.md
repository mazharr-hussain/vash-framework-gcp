# OCI Always Free

The VASH runner: network and one A1 Flex VM (2 cores, 12 GB by default), built with Oracle's
CD3 Automation Toolkit modules (oracle-devrel/cd3-automation-toolkit, UPL-1.0, release v2026.2.2):
vcn, igw, route-table, sec-list, subnet and compute/instance. With `subnet_id` set, no network is
created. When `create_database = true`, the free Autonomous Database comes from VASH's own
`modules/database` (the CD3 adb module has no free-tier option).

`vash onboard oci` writes `terraform.tfvars.json` and `scripts/vash-runner.sh` (the first-boot
install the CD3 instance module reads) and runs terraform (see `bootstrap/README.md`).
