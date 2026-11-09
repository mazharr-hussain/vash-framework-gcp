"""Existing compartments, VCNs and subnets: list them, delete chosen ones, pick a subnet.

Used by `vash onboard oci` before it builds anything. Every delete is asked twice
(the choice, then the exact list after a dependency check), a VM also needs its name
typed, and OCI itself refuses to delete a subnet or VCN that is still in use.
"""
from __future__ import annotations

from dataclasses import dataclass
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from vash.core.exceptions import VashError


@dataclass(frozen=True)
class Row:
    no: int
    kind: str  # Compartment | VCN | Subnet | VM
    name: str
    state: str
    parent: str  # compartment of a VCN, VCN of a subnet
    public: str  # subnets: yes/no; VMs: public IP
    ocid: str
    compartment_id: str
    vcn_id: str = ""
    region: str = ""
    tenancy: str = ""


# Listed by VASH itself (direct listings), so skipped in the Resource Search part of the table.
CORE_TYPES = {"Compartment", "Vcn", "Subnet", "Instance"}
# Automatic sub-parts of other resources: shown in dependency checks, not as rows.
SUB_PART_TYPES = {"Vnic", "PrivateIp", "VnicAttachment", "BootVolumeAttachment", "VolumeAttachment",
                  "DHCPOptions", "RouteTable", "SecurityList", "InternetGateway", "NatGateway",
                  "ServiceGateway", "LocalPeeringGateway", "DrgAttachment", "NetworkSecurityGroup",
                  "BootVolume", "DnsResolver", "DnsView", "CustomerDnsZone", "Tenancy", "Key",
                  "VaultSecret"}
VASH_KINDS = {"Compartment", "VCN", "Subnet", "VM"}

TERMINATE_POLLS = 40  # 10 minutes at 15 s

# Services that create their own VNICs in a customer subnet (OCI Search resource types).
VNIC_OWNER_TYPES = {
    "PrivateEndpoint", "ResourceManagerPrivateEndpoint", "LoadBalancer", "NetworkLoadBalancer",
    "AutonomousDatabase", "DbSystem", "CloudVmCluster", "VmCluster", "MysqlDbSystem",
    "PostgresqlDbSystem", "NoSqlTable", "ContainerInstance", "FunctionsApplication", "MountTarget",
    "Bastion", "ApiGateway", "ClustersCluster", "NodePool", "IntegrationInstance",
    "AnalyticsInstance", "DataScienceNotebookSession", "GoldenGateDeployment", "OpenSearchCluster",
    "RedisCluster", "NetworkFirewall", "DrgAttachment", "Instance",
}


def _search_time(value: str) -> str:
    """OCI Search takes 2026-11-04T01:39:02Z, not 2026-11-04T01:39:02.547000+00:00."""
    if not value:
        return ""
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Inventory:
    def __init__(self, oci: Callable[..., Any], echo: Callable[[str], None], cleaner: Any = None,
                 sleep: Callable[[float], None] = time.sleep):
        self._raw_oci = oci
        self.region: str | None = None  # every call goes to this region when set
        self.regions: list[str] = []
        self.related: list[dict[str, str]] = []
        self.echo = echo
        self.sleep = sleep
        self.cleaner = cleaner  # Oracle's compartment cleaner, for compartments that still hold resources

    def oci(self, *args: str) -> Any:
        if self.region:
            args = (*args, "--region", self.region)
        return self._raw_oci(*args)

    def in_region(self, region: str) -> "Inventory":
        self.region = region or None
        return self

    def subscribed_regions(self, tenancy: str) -> list[str]:
        self.region = None
        try:
            data = self.oci("iam", "region-subscription", "list", "--tenancy-id", tenancy).get("data", [])
        except VashError as exc:
            self.echo(f"Could not list the subscribed regions ({exc}); using the current region only")
            return [""]
        regions = [r.get("region-name", "") for r in data if r.get("status", "READY") == "READY"]
        home = [r.get("region-name", "") for r in data if r.get("is-home-region")]
        return sorted(set(regions), key=lambda r: (r not in home, r)) or [""]

    def related_tenancies(self, tenancy: str) -> list[dict[str, str]]:
        """Parent or child tenancies (OCI Organizations): {role, name, id, state}."""
        self.region = None
        found: list[dict[str, str]] = []
        try:
            orgs = self.oci("organizations", "organization", "list", "--compartment-id", tenancy).get("data", {})
            items = orgs.get("items", orgs) if isinstance(orgs, dict) else orgs
            for org in items or []:
                parent = org.get("parent-tenancy-id", "")
                kids = self.oci("organizations", "organization-tenancy", "list",
                                "--organization-id", org["id"]).get("data", {})
                for k in (kids.get("items", []) if isinstance(kids, dict) else kids) or []:
                    tid = k.get("tenancy-id", "")
                    if tid and tid != tenancy and all(f["id"] != tid for f in found):
                        found.append({"role": "parent" if tid == parent else "child", "name": k.get("name", ""),
                                      "id": tid, "state": k.get("lifecycle-state", "")})
        except (VashError, KeyError, AttributeError):
            return []
        return found

    # ---- reading -------------------------------------------------------
    def rows(self, tenancy: str) -> list[Row]:
        """Every tenancy this login reaches (this one, then related ones), every subscribed region."""
        rows: list[Row] = []
        tenancies = [{"role": "this", "name": "this tenancy", "id": tenancy}] + self.related
        for ten in tenancies:
            self.region = None
            try:
                comps = self.oci("iam", "compartment", "list", "--compartment-id", ten["id"],
                                 "--compartment-id-in-subtree", "true", "--lifecycle-state", "ACTIVE",
                                 "--access-level", "ACCESSIBLE", "--all").get("data", [])
            except VashError:
                self.echo(f"No access to {ten['role']} tenancy {ten['name']} ({ten['id']}) with this login; skipped")
                continue
            label = "" if ten["id"] == tenancy else ten["name"] or ten["id"]
            names = {ten["id"]: "(root)" if not label else f"(root of {label})"}
            names.update({c["id"]: c["name"] for c in comps})
            for c in comps:
                rows.append(Row(len(rows) + 1, "Compartment", c["name"], c.get("lifecycle-state", ""),
                                names.get(c.get("compartment-id", ""), ""), "", c["id"], c.get("compartment-id", ""),
                                tenancy=label))
            regions = self.subscribed_regions(ten["id"])
            if ten["id"] == tenancy:
                self.regions = regions
            for region in regions:
                self.in_region(region)
                rows.extend(self._region_rows(ten["id"], comps, names, region, len(rows), label,
                                              search=ten["id"] == tenancy))
        self.region = None
        return rows

    def _region_rows(self, tenancy: str, comps: list[dict], names: dict[str, str], region: str,
                     start: int, label: str = "", search: bool = True) -> list[Row]:
        """VCNs, subnets and VMs (direct listings) and every other resource (Resource Search) of one region."""
        rows: list[Row] = []
        where = (f" in {region}" if region else "") + (f" ({label})" if label else "")

        def add(*fields: Any, **extra: Any) -> None:
            rows.append(Row(start + len(rows) + 1, *fields, region=region, tenancy=label, **extra))

        # Direct listings, not Resource Search: search lags behind deletes by a minute or two.
        scopes = [tenancy] + [c["id"] for c in comps]
        for comp in scopes:
            self.echo(f"Reading {names.get(comp, comp)}{where} ...")
            for v in self.oci("network", "vcn", "list", "--compartment-id", comp, "--all").get("data", []):
                if v.get("lifecycle-state") in ("TERMINATED", "TERMINATING"):
                    continue
                add("VCN", v.get("display-name", ""), v.get("lifecycle-state", ""),
                                names.get(comp, comp), "", v["id"], comp)
                subnets = self.oci("network", "subnet", "list", "--compartment-id", comp,
                                   "--vcn-id", v["id"], "--all").get("data", [])
                for s in subnets:
                    if s.get("lifecycle-state") in ("TERMINATED", "TERMINATING"):
                        continue
                    add("Subnet", s.get("display-name", ""), s.get("lifecycle-state", ""),
                                    v.get("display-name", ""), "no" if s.get("prohibit-public-ip-on-vnic", True) else "yes",
                                    s["id"], s.get("compartment-id", comp), v["id"])
        for comp in scopes:
            for vm in self.oci("compute", "instance", "list", "--compartment-id", comp, "--all").get("data", []):
                state = vm.get("lifecycle-state", "")
                if state in ("TERMINATED", "TERMINATING"):
                    continue
                ip = ""
                if state == "RUNNING":
                    vnics = self.oci("compute", "instance", "list-vnics", "--instance-id", vm["id"]).get("data", [])
                    ip = next((v.get("public-ip") for v in vnics if v.get("public-ip")), "") or ""
                add("VM", vm.get("display-name", ""), state,
                                names.get(comp, comp), ip, vm["id"], comp)
        if not search:  # Resource Search covers only the signed-in tenancy
            return rows
        self.echo(f"Reading every other resource{where} (Resource Search) ...")
        try:
            others = self.oci("search", "resource", "structured-search", "--query-text",
                              "query all resources", "--limit", "1000").get("data", {}).get("items", [])
        except VashError as exc:
            self.echo(f"Resource Search failed, only the core objects are listed: {exc}")
            others = []
        for item in sorted(others, key=lambda i: (names.get(i.get("compartment-id", ""), ""),
                                                  i.get("resource-type", ""), i.get("display-name", ""))):
            kind = item.get("resource-type", "")
            if kind in CORE_TYPES or kind in SUB_PART_TYPES:
                continue
            if item.get("lifecycle-state") in ("TERMINATED", "TERMINATING", "DELETED", "DELETING"):
                continue
            comp = item.get("compartment-id", "")
            add(kind, item.get("display-name", "") or item.get("identifier", ""),
                            item.get("lifecycle-state", ""), names.get(comp, comp), "",
                            item.get("identifier", ""), comp)
        return rows

    def show(self, rows: list[Row]) -> None:
        headers = ("S.No", "Tenancy", "Type", "Name", "State", "Region", "Belongs to", "Public", "OCID")
        table = [headers] + [(str(r.no), r.tenancy or "this", r.kind, r.name, r.state, r.region or "-", r.parent,
                              r.public, r.ocid) for r in rows]
        widths = [max(len(row[i]) for row in table) for i in range(len(headers))]
        line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        self.echo(line)
        for i, row in enumerate(table):
            self.echo("| " + " | ".join(cell.ljust(widths[j]) for j, cell in enumerate(row)) + " |")
            if i == 0:
                self.echo(line)
        self.echo(line)

    @staticmethod
    def select(rows: list[Row], answer: str) -> tuple[list[Row], list[str]]:
        """Rows chosen by S.No or OCID (comma separated), and the entries that matched nothing."""
        by_no = {str(r.no): r for r in rows}
        by_id = {r.ocid: r for r in rows}
        chosen, unknown = [], []
        for part in (p.strip() for p in answer.split(",")):
            if not part:
                continue
            row = by_no.get(part) or by_id.get(part)
            if row is None:
                unknown.append(part)
            elif row not in chosen:
                chosen.append(row)
        return chosen, unknown

    # ---- dependencies --------------------------------------------------
    def compartment_resources(self, compartment_id: str) -> dict[str, list[dict]]:
        """Live resources directly in a compartment, per subscribed region."""
        found: dict[str, list[dict]] = {}
        for region in self.regions or [""]:
            self.in_region(region)
            items = self.oci("search", "resource", "structured-search", "--query-text",
                             f"query all resources where compartmentId = '{compartment_id}'"
                             ).get("data", {}).get("items", [])
            live = [i for i in items if i.get("lifecycle-state") not in ("TERMINATED", "DELETED")]
            if live:
                found[region] = live
        self.region = None
        return found

    def vm_vnics(self, vm_ocid: str) -> set[str]:
        data = self.oci("compute", "instance", "list-vnics", "--instance-id", vm_ocid).get("data", [])
        return {v["id"] for v in data if v.get("id")}

    def vnic_owner(self, vnic_id: str) -> str:
        """Who holds a VNIC: the VM it is attached to, or the service created with it."""
        vnic = self.oci("network", "vnic", "get", "--vnic-id", vnic_id).get("data", {})
        comp = vnic.get("compartment-id", "")
        attached = self.oci("compute", "vnic-attachment", "list", "--compartment-id", comp,
                            "--vnic-id", vnic_id, "--all").get("data", []) if comp else []
        for att in attached:
            if att.get("lifecycle-state") in ("ATTACHED", "ATTACHING") and att.get("instance-id"):
                vm = self.oci("compute", "instance", "get", "--instance-id", att["instance-id"]).get("data", {})
                return f"VM {vm.get('display-name', att['instance-id'])}"
        created = _search_time(vnic.get("time-created", ""))
        if not (comp and created):
            return f"VNIC {vnic.get('display-name', vnic_id)}"
        # A service VNIC is created a moment after its service: look for what was created just before it.
        try:
            found = self.oci("search", "resource", "structured-search", "--query-text",
                             f"query all resources where compartmentId = '{comp}' && timeCreated <= '{created}'"
                             ).get("data", {}).get("items", [])
        except VashError:
            return f"VNIC {vnic.get('display-name', vnic_id)} (owner unknown: search failed)"
        candidates = self._owner_candidates(found)
        if not candidates:
            # The service may sit in another compartment than its VNIC: search the whole tenancy,
            # in the 10 minutes before the VNIC was created.
            since = _search_time((datetime.fromisoformat(created.replace("Z", "+00:00"))
                                  - timedelta(minutes=10)).isoformat())
            try:
                found = self.oci("search", "resource", "structured-search", "--query-text",
                                 f"query all resources where timeCreated >= '{since}' && timeCreated <= '{created}'"
                                 ).get("data", {}).get("items", [])
            except VashError:
                found = []
            candidates = self._owner_candidates(found)
        if candidates:
            c = candidates[0]
            return (f"probably {c.get('resource-type', '')} {c.get('display-name', '')} "
                    f"(created {c.get('time-created', '')[:16]}, VNIC {vnic.get('display-name', '')})")
        return (f"VNIC {vnic.get('display-name', vnic_id)} (owner not found; in the Console open the subnet, "
                "IP administration, to see what holds it)")

    @staticmethod
    def _owner_candidates(items: list[dict]) -> list[dict]:
        return sorted((i for i in items if i.get("resource-type") in VNIC_OWNER_TYPES
                       and i.get("lifecycle-state") not in ("TERMINATED", "DELETED")),
                      key=lambda i: i.get("time-created", ""), reverse=True)

    def _users_of_subnet(self, subnet_id: str, ignore: frozenset[str] = frozenset()) -> list[str]:
        """Everything holding an IP in the subnet, named by its owner, except the VNICs of VMs
        deleted in the same batch."""
        ips = self.oci("network", "private-ip", "list", "--subnet-id", subnet_id, "--all").get("data", [])
        owners: dict[str, str] = {}
        users = []
        for ip in ips:
            vnic_id = ip.get("vnic-id")
            if vnic_id in ignore:
                continue
            if vnic_id and vnic_id not in owners:
                owners[vnic_id] = self.vnic_owner(vnic_id)
            owner = owners.get(vnic_id, ip.get("display-name") or "")
            users.append(f"IP {ip.get('ip-address', '')}: {owner}")
        return users

    def dependencies(self, r: Row, ignore: frozenset[str] = frozenset()) -> tuple[list[str], list[str]]:
        """(also deleted with it, still using it). Anything in the second list blocks the delete.

        `ignore` holds the VNIC ids of VMs chosen in the same batch: they go first, so their IPs
        do not block their subnet or VCN.
        """
        also: list[str] = []
        blockers: list[str] = []
        self.in_region(r.region)
        if r.kind == "VM":
            vm = self.oci("compute", "instance", "get", "--instance-id", r.ocid).get("data", {})
            comp = vm.get("compartment-id", r.compartment_id)
            boots = self.oci("compute", "boot-volume-attachment", "list", "--availability-domain",
                             vm.get("availability-domain", ""), "--compartment-id", comp,
                             "--instance-id", r.ocid).get("data", [])
            also += [f"boot volume {b.get('boot-volume-id', '')} (its disk: all data on it is lost)" for b in boots]
            vols = self.oci("compute", "volume-attachment", "list", "--compartment-id", comp,
                            "--instance-id", r.ocid, "--all").get("data", [])
            also += [f"block volume {v.get('volume-id', '')}: detached and kept" for v in vols
                     if v.get("lifecycle-state") == "ATTACHED"]
        elif r.kind == "Subnet":
            blockers += self._users_of_subnet(r.ocid, ignore)
        elif r.kind == "VCN":
            vcn = self.oci("network", "vcn", "get", "--vcn-id", r.ocid).get("data", {})
            comp = vcn.get("compartment-id", r.compartment_id)
            defaults = {vcn.get("default-route-table-id"), vcn.get("default-security-list-id"),
                        vcn.get("default-dhcp-options-id")}
            for s in self._children("subnet", comp, r.ocid):
                name = s.get("display-name", s["id"])
                also.append(f"subnet {name}")
                blockers += [f"subnet {name}: {u}" for u in self._users_of_subnet(s["id"], ignore)]
            for kind in ("internet-gateway", "nat-gateway", "service-gateway", "nsg",
                         "route-table", "security-list", "dhcp-options"):
                for item in self._children(kind, comp, r.ocid):
                    if item["id"] not in defaults:
                        also.append(f"{kind} {item.get('display-name', item['id'])}")
            for item in self._children("local-peering-gateway", comp, r.ocid):
                name = item.get("display-name", item["id"])
                if item.get("peering-status") == "PEERED":
                    blockers.append(f"local-peering-gateway {name}: peered with another VCN (remove the peering first)")
                else:
                    also.append(f"local-peering-gateway {name} (not peered)")
            for item in self._children("drg-attachment", comp, r.ocid):
                blockers.append(f"drg-attachment {item.get('display-name', item['id'])} (remove it first)")
        elif r.kind == "Compartment":
            self.region = None
            subs = self.oci("iam", "compartment", "list", "--compartment-id", r.ocid,
                            "--lifecycle-state", "ACTIVE", "--all").get("data", [])
            blockers += [f"sub-compartment {c['name']} (remove it first)" for c in subs]
            for region, items in self.compartment_resources(r.ocid).items():
                where = f" [{region}]" if region else ""
                blockers += [f"{i.get('resource-type', '')} {i.get('display-name', i.get('identifier', ''))}{where}"
                             for i in items]
        return also, blockers

    # ---- deleting ------------------------------------------------------
    def delete(self, chosen: list[Row]) -> list[str]:
        """VMs first, then subnets, then VCNs (with their gateways, tables and lists), then compartments.

        A failure is reported and the next item still runs; the failures are returned.
        """
        failures: list[str] = []

        def attempt(row: Row, action: Callable[[], None]) -> None:
            self.in_region(row.region)
            try:
                action()
            except VashError as exc:
                failures.append(f"{row.kind} {row.name}: {exc}")
                self.echo(f"Could not delete {row.kind} {row.name}: {exc}")

        def terminate(r: Row) -> None:
            # The CLI's --wait-for-state failed on terminate in Cloud Shell, so VASH polls the state itself.
            self.oci("compute", "instance", "terminate", "--instance-id", r.ocid,
                     "--preserve-boot-volume", "false", "--force")
            self.echo(f"VM {r.name}: terminating ...")
            for _ in range(TERMINATE_POLLS):
                try:
                    state = self.oci("compute", "instance", "get", "--instance-id", r.ocid
                                     ).get("data", {}).get("lifecycle-state", "")
                except VashError:
                    state = "TERMINATED"  # no longer found
                if state == "TERMINATED":
                    self.echo(f"VM {r.name} terminated")
                    return
                self.sleep(15)
            raise VashError(f"VM {r.name} is still {state} after {TERMINATE_POLLS * 15 // 60} minutes",
                            "Check it in the Console; run the cleanup again when it is gone")

        def drop_compartment(r: Row) -> None:
            self.oci("iam", "compartment", "delete", "--compartment-id", r.ocid, "--force")
            self.echo(f"Compartment {r.name}: deletion started (OCI finishes it in the background)")

        for r in chosen:
            if r.kind == "VM":
                attempt(r, lambda r=r: terminate(r))
        vcn_ids = {r.ocid for r in chosen if r.kind == "VCN"}
        for r in chosen:
            if r.kind == "Subnet" and r.vcn_id not in vcn_ids:
                attempt(r, lambda r=r: self._delete_subnet(r.ocid, r.name))
        for r in chosen:
            if r.kind == "VCN":
                attempt(r, lambda r=r: self._delete_vcn(r))
        for r in chosen:
            if r.kind == "Compartment":
                attempt(r, lambda r=r: drop_compartment(r))
        return failures

    def _delete_subnet(self, ocid: str, name: str) -> None:
        self.oci("network", "subnet", "delete", "--subnet-id", ocid, "--force", "--wait-for-state", "TERMINATED")
        self.echo(f"Subnet {name} deleted")

    def _children(self, kind: str, comp: str, vcn: str) -> list[dict]:
        return self.oci("network", kind, "list", "--compartment-id", comp, "--vcn-id", vcn, "--all").get("data", [])

    def _delete_vcn(self, r: Row) -> None:
        vcn = self.oci("network", "vcn", "get", "--vcn-id", r.ocid).get("data", {})
        comp = vcn.get("compartment-id", r.compartment_id)
        defaults = {vcn.get("default-route-table-id"), vcn.get("default-security-list-id"),
                    vcn.get("default-dhcp-options-id")}
        for s in self._children("subnet", comp, r.ocid):
            self._delete_subnet(s["id"], s.get("display-name", s["id"]))
        for rt in self._children("route-table", comp, r.ocid):
            if rt["id"] in defaults:
                self.oci("network", "route-table", "update", "--rt-id", rt["id"], "--route-rules", "[]", "--force")
            else:
                self.oci("network", "route-table", "delete", "--rt-id", rt["id"], "--force",
                         "--wait-for-state", "TERMINATED")
        for kind, flag in (("internet-gateway", "--ig-id"), ("nat-gateway", "--nat-gateway-id"),
                           ("service-gateway", "--service-gateway-id"), ("nsg", "--nsg-id"),
                           ("local-peering-gateway", "--local-peering-gateway-id")):
            for item in self._children(kind, comp, r.ocid):
                self.oci("network", kind, "delete", flag, item["id"], "--force", "--wait-for-state", "TERMINATED")
        for kind, flag in (("security-list", "--security-list-id"), ("dhcp-options", "--dhcp-id")):
            for item in self._children(kind, comp, r.ocid):
                if item["id"] not in defaults:
                    self.oci("network", kind, "delete", flag, item["id"], "--force", "--wait-for-state", "TERMINATED")
        self.oci("network", "vcn", "delete", "--vcn-id", r.ocid, "--force", "--wait-for-state", "TERMINATED")
        self.echo(f"VCN {r.name} deleted")


def _typed(inv: "Inventory", ask: Callable[[str, str], str], name: str) -> bool:
    for attempt in range(3):
        if ask(f"Type the VM name to terminate it ({name})", "").strip() == name:
            return True
        if attempt < 2:
            inv.echo(f"That is not '{name}'; try again")
    return False


def clean_compartment(inv: Inventory, r: Row, tenancy: str, confirm: Callable[[str], bool]) -> None:
    """Dry-run plan first; the real run backs up to the root compartment and asks for DELETE itself."""
    if not confirm(f"Empty compartment {r.name} with Oracle's compartment cleaner? It first writes a dry-run plan"):
        inv.echo(f"Compartment {r.name} left as it is")
        return
    regions = list(inv.compartment_resources(r.ocid)) or [""]
    for region in regions:
        where = f" in {region}" if region else ""
        if inv.cleaner.run(r.ocid, tenancy, execute=False, region=region or None) != 0:
            inv.echo(f"The cleaner's dry run failed for {r.name}{where}; nothing deleted (see its log above)")
            return
        if not confirm(f"Run that plan on {r.name}{where} now? A Resource Manager backup stack is made in the root "
                       "compartment first, and the cleaner asks you to type DELETE"):
            inv.echo(f"Compartment {r.name} left as it is")
            return
        if inv.cleaner.run(r.ocid, tenancy, execute=True, region=region or None) != 0:
            inv.echo(f"The cleaner stopped for {r.name}{where}; see its log above")
            return
    inv.region = None
    inv.oci("iam", "compartment", "delete", "--compartment-id", r.ocid, "--force")
    inv.echo(f"Compartment {r.name}: emptied; deletion started (OCI finishes it in the background)")


@dataclass(frozen=True)
class Choice:
    """What the owner picked from the table: an existing VM, or a subnet for a new one."""
    vm: Row | None = None
    subnet_id: str = ""


def _choices(rows: list[Row]) -> str:
    return ", ".join(f"{r.no} = {r.kind} {r.name}" for r in rows)


def _pick(inv: Inventory, ask: Callable[[str, str], str], question: str, allowed: list[Row],
          many: bool) -> list[Row]:
    """Ask for S.No(s) from `allowed`; a wrong answer is explained and asked again (3 tries).
    Enter means none."""
    for attempt in range(3):
        answer = ask(question, "").strip()
        if not answer:
            return []
        chosen, unknown = inv.select(allowed, answer)
        if not many and len(chosen) > 1:
            unknown, chosen = [answer], []
        if chosen and not unknown:
            return chosen
        wrong = ", ".join(unknown) or answer
        what = "one S.No" if not many else "S.No numbers from the table"
        if attempt < 2:
            inv.echo(f"'{wrong}' is not a valid choice here. Type {what} from: {_choices(allowed)}; "
                     "or press Enter to skip")
    inv.echo("No valid choice after 3 tries: skipped")
    return []


def _delete_round(inv: Inventory, rows: list[Row], tenancy: str, confirm: Callable[[str], bool],
                  ask: Callable[[str, str], str]) -> bool:
    """One pass: choose, dependency check, reconfirm, delete. True if anything was changed."""
    chosen = _pick(inv, ask, "Which rows do you want to delete? Type the S.No to delete, comma separated "
                   "(example: 4,5), or their OCIDs; press Enter for none", rows, many=True)
    comp_no = {r.ocid: r.no for r in rows if r.kind == "Compartment"}
    for r in [r for r in chosen if r.kind not in VASH_KINDS]:
        if r.compartment_id in comp_no:
            inv.echo(f"{r.no}. {r.kind} {r.name}: removed with its compartment by Oracle's cleaner; "
                     f"choose its compartment {r.parent} (S.No {comp_no[r.compartment_id]})")
        else:
            inv.echo(f"{r.no}. {r.kind} {r.name}: in the root compartment, which the cleaner never touches; "
                     "remove it in the Console")
    chosen = [r for r in chosen if r.kind in VASH_KINDS]
    ignore: frozenset[str] = frozenset()
    for r in chosen:
        if r.kind == "VM":
            ignore |= inv.in_region(r.region).vm_vnics(r.ocid)
    deletable = []
    to_clean: list[Row] = []
    for r in chosen:
        also, blockers = inv.dependencies(r, ignore)
        inv.echo(f"{r.no}. {r.kind} {r.name} ({r.ocid})")
        for a in also:
            label = "kept" if a.endswith("detached and kept") else "also deleted"
            inv.echo(f"     {label}: {a}")
        for b in blockers:
            inv.echo(f"     still in use: {b}")
        cleanable = (r.kind == "Compartment" and blockers and inv.cleaner is not None and not r.tenancy
                     and not any(b.startswith("sub-compartment") for b in blockers))
        if cleanable:
            inv.echo("     -> holds resources: Oracle's compartment cleaner can empty it (plan and backup first)")
            to_clean.append(r)
        elif blockers:
            inv.echo("     -> blocked: it stays until what uses it (listed above) is removed")
        else:
            inv.echo("     -> nothing uses it")
            deletable.append(r)
    changed = False
    if deletable:
        names = ", ".join(f"{r.no}. {r.kind} {r.name}" for r in deletable)
        vms = [r for r in deletable if r.kind == "VM"]
        if not confirm(f"Delete these now: {names}? This cannot be undone"):
            inv.echo("Nothing deleted")
        elif not all(_typed(inv, ask, r.name) for r in vms):
            inv.echo("A VM name did not match after 3 tries: nothing deleted")
        else:
            failures = inv.delete(deletable)
            if failures:
                inv.echo(f"{len(failures)} item(s) were not deleted; the rest went ahead")
            changed = True
    elif chosen and not to_clean:
        inv.echo("Nothing can be deleted: every choice is still in use")
    for r in to_clean:
        clean_compartment(inv, r, tenancy, confirm)
        changed = True
    return changed


def review(inv: Inventory, tenancy: str, confirm: Callable[[str], bool],
           ask: Callable[[str, str], str], want_subnet: bool, want_vm: bool = True) -> Choice:
    """The interactive part of onboarding."""
    if not confirm("Do you want to check everything in the tenancy (all subscribed regions), to delete what you no "
                   "longer need?"):
        return Choice()
    inv.related = inv.related_tenancies(tenancy)
    for ten in inv.related:
        inv.echo(f"Related {ten['role']} tenancy {ten['name']} ({ten['id']}): listed when this login can reach it")
    rows = inv.rows(tenancy)
    inv.show(rows)
    question = "Do you want to delete any of them?"
    while rows and confirm(question):
        if _delete_round(inv, rows, tenancy, confirm, ask):
            rows = inv.rows(tenancy)
            inv.show(rows)
        question = "Do you want to delete something else from the table?"
    vms = [r for r in rows if r.kind == "VM" and r.state == "RUNNING" and r.public]
    if want_vm and vms:
        chosen = _pick(inv, ask, f"Install VASH on an existing VM? Type its S.No ({_choices(vms)}), "
                       "or press Enter to create a new VM", vms, many=False)
        if chosen:
            return Choice(vm=chosen[0])
    if not want_subnet:
        return Choice()
    public = [r for r in rows if r.kind == "Subnet" and r.public == "yes" and r.state == "AVAILABLE"]
    if not public:
        return Choice()
    chosen = _pick(inv, ask, f"The new VASH VM needs a public subnet. Use one that exists? Type its S.No "
                   f"({_choices(public)}), or press Enter to create a new network", public, many=False)
    return Choice(subnet_id=chosen[0].ocid) if chosen else Choice()
