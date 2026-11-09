import pytest

from vash.adapters.cloud.oci.inventory import Inventory, review
from vash.core.exceptions import VashError

TEN = "ocid1.tenancy..t"


class FakeOci:
    def __init__(self, in_use=()):
        self.calls = []
        self.in_use = set(in_use)
        self.vcns = {
            "ocid1.vcn..a": {"name": "PoC_VCN", "comp": "ocid1.comp..x",
                              "subnets": [("ocid1.subnet..pub", "public subnet", False),
                                          ("ocid1.subnet..priv", "private subnet", True)]},
            "ocid1.vcn..b": {"name": "Old_VCN", "comp": "ocid1.comp..x",
                              "subnets": [("ocid1.subnet..old", "old subnet", False)]},
        }

    def __call__(self, *args):
        self.calls.append(args)
        a = list(args)
        if a[:3] == ["search", "resource", "structured-search"] and a[a.index("--query-text") + 1] == "query all resources":
            return {"data": {"items": [
                {"resource-type": "Bucket", "display-name": "odoo-files", "identifier": "ocid1.bucket..b",
                 "lifecycle-state": "ACTIVE", "compartment-id": "ocid1.comp..x"},
                {"resource-type": "Vault", "display-name": "root-vault", "identifier": "ocid1.vault..v",
                 "lifecycle-state": "ACTIVE", "compartment-id": TEN},
                {"resource-type": "Vcn", "display-name": "dup", "identifier": "ocid1.vcn..a",
                 "lifecycle-state": "AVAILABLE", "compartment-id": "ocid1.comp..x"},
                {"resource-type": "Vnic", "display-name": "nic", "identifier": "ocid1.vnic..n",
                 "lifecycle-state": "AVAILABLE", "compartment-id": "ocid1.comp..x"}]}}
        if a[:3] == ["iam", "compartment", "list"] and a[a.index("--compartment-id") + 1] != TEN:
            return {"data": []}
        if a[:3] == ["network", "vcn", "list"]:
            comp = a[a.index("--compartment-id") + 1]
            return {"data": [{"id": k, "display-name": v["name"], "lifecycle-state": "AVAILABLE"}
                             for k, v in self.vcns.items() if v["comp"] == comp]}
        if a[:3] == ["compute", "instance", "list"]:
            comp = a[a.index("--compartment-id") + 1]
            if comp != "ocid1.comp..x" or getattr(self, "terminated", None):
                return {"data": []}
            return {"data": [{"id": "ocid1.instance..vm", "display-name": "kyc-vm", "lifecycle-state": "RUNNING"}]}
        if a[:3] == ["iam", "compartment", "list"]:
            return {"data": [{"id": "ocid1.comp..x", "name": "PoC", "lifecycle-state": "ACTIVE",
                              "compartment-id": TEN}]}
        if a[:3] == ["search", "resource", "structured-search"] and "instance" in a[-1]:
            return {"data": {"items": [{"identifier": "ocid1.instance..vm", "display-name": "kyc-vm",
                                        "lifecycle-state": "RUNNING", "compartment-id": "ocid1.comp..x"}]}}
        if a[:3] == ["compute", "instance", "list-vnics"]:
            return {"data": [{"id": "vnic-vm", "public-ip": "203.0.113.9"}]}
        if a[:3] == ["compute", "instance", "get"]:
            return {"data": {"compartment-id": "ocid1.comp..x", "availability-domain": "AD-1",
                             "display-name": "kyc-vm",
                             "lifecycle-state": "TERMINATED" if getattr(self, "terminated", None) else "RUNNING"}}
        if a[:3] == ["network", "vnic", "get"]:
            vid = a[a.index("--vnic-id") + 1]
            return {"data": {"compartment-id": "ocid1.comp..x", "time-created": "2026-11-04T01:39:02.547000+00:00",
                             "display-name": f"name-of-{vid}"}}
        if a[:3] == ["compute", "vnic-attachment", "list"]:
            vid = a[a.index("--vnic-id") + 1]
            if vid == "vnic-vm":
                return {"data": [{"instance-id": "ocid1.instance..vm", "lifecycle-state": "ATTACHED"}]}
            return {"data": []}
        if a[:3] == ["search", "resource", "structured-search"] and "timeCreated" in a[-1]:
            return {"data": {"items": [
                {"resource-type": "Vnic", "display-name": "x", "time-created": "2026-11-04T01:39:02Z"},
                {"resource-type": "Compartment", "display-name": "Common", "time-created": "2026-11-04T01:39:00Z",
                 "lifecycle-state": "ACTIVE"},
                {"resource-type": "PrivateEndpoint", "display-name": "odoo-pe", "time-created": "2026-11-04T01:38:40Z",
                 "lifecycle-state": "ACTIVE"},
                {"resource-type": "Bucket", "display-name": "old", "time-created": "2026-10-01T00:00:00Z",
                 "lifecycle-state": "ACTIVE"}]}}
        if a[:3] == ["compute", "boot-volume-attachment", "list"]:
            return {"data": [{"boot-volume-id": "ocid1.bootvolume..b"}]}
        if a[:3] == ["compute", "volume-attachment", "list"]:
            return {"data": [{"volume-id": "ocid1.volume..data", "lifecycle-state": "ATTACHED"}]}
        if a[:3] == ["compute", "instance", "terminate"]:
            self.terminated = a[a.index("--instance-id") + 1]
            self.in_use = set()
            return {}
        if a[:3] == ["search", "resource", "structured-search"] and "compartmentId" not in a[-1]:
            return {"data": {"items": [{"identifier": k, "display-name": v["name"], "lifecycle-state": "AVAILABLE",
                                        "compartment-id": v["comp"]} for k, v in self.vcns.items()]}}
        if a[:3] == ["network", "subnet", "list"]:
            vcn = a[a.index("--vcn-id") + 1]
            return {"data": [{"id": s, "display-name": n, "lifecycle-state": "AVAILABLE",
                              "prohibit-public-ip-on-vnic": priv, "compartment-id": "ocid1.comp..x"}
                             for s, n, priv in self.vcns.get(vcn, {}).get("subnets", [])]}
        if a[:3] == ["network", "private-ip", "list"]:
            sid = a[a.index("--subnet-id") + 1]
            return {"data": [{"ip-address": "10.0.0.5", "display-name": "kyc-vm", "vnic-id": "vnic-vm"}]
                    if sid in self.in_use else []}
        if a[:3] == ["search", "resource", "structured-search"] and "compartmentId" in a[-1]:
            return {"data": {"items": [{"resource-type": "Instance", "display-name": "kyc-vm",
                                        "lifecycle-state": "RUNNING"}]}}
        if a[:3] == ["network", "subnet", "delete"]:
            sid = a[a.index("--subnet-id") + 1]
            if sid in self.in_use:
                raise VashError("oci network subnet delete failed: Conflict, subnet in use", "fix")
            for v in self.vcns.values():
                v["subnets"] = [s for s in v["subnets"] if s[0] != sid]
            return {}
        if a[:3] == ["network", "vcn", "get"]:
            return {"data": {"compartment-id": "ocid1.comp..x", "default-route-table-id": "rt-default",
                             "default-security-list-id": "sl-default", "default-dhcp-options-id": "dhcp-default"}}
        if a[:2] == ["network", "route-table"] and a[2] == "list":
            return {"data": [{"id": "rt-default"}, {"id": "rt-extra"}]}
        if a[:2] == ["network", "security-list"] and a[2] == "list":
            return {"data": [{"id": "sl-default"}, {"id": "sl-extra"}]}
        if a[:2] == ["network", "dhcp-options"] and a[2] == "list":
            return {"data": [{"id": "dhcp-default"}]}
        if a[:2] == ["network", "internet-gateway"] and a[2] == "list":
            return {"data": [{"id": "igw-1"}]}
        if a[2] == "list":
            return {"data": []}
        if a[:3] == ["network", "vcn", "delete"]:
            self.vcns.pop(a[a.index("--vcn-id") + 1])
            return {}
        return {}


def yes(question):
    """Yes to everything, except another delete round."""
    return "something else" not in question


def lines():
    out = []
    return out, out.append


def test_table_lists_compartments_vcns_and_subnets_with_owner():
    out, echo = lines()
    inv = Inventory(FakeOci(), echo)
    rows = inv.rows(TEN)
    assert [(r.no, r.kind) for r in rows][:3] == [(1, "Compartment"), (2, "VCN"), (3, "Subnet")]
    sub = next(r for r in rows if r.ocid == "ocid1.subnet..pub")
    assert sub.parent == "PoC_VCN" and sub.public == "yes"
    assert any(line.startswith("Reading ") for line in out)
    out.clear()
    inv.show(rows)
    assert "S.No" in out[1] and "Belongs to" in out[1]


def test_select_by_number_and_ocid():
    inv = Inventory(FakeOci(), lambda m: None)
    rows = inv.rows(TEN)
    chosen, unknown = inv.select(rows, "2, ocid1.subnet..old, 99, 2")
    assert [r.ocid for r in chosen] == ["ocid1.vcn..a", "ocid1.subnet..old"]
    assert unknown == ["99"]


def test_vcn_delete_removes_children_in_order_and_keeps_defaults():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    rows = inv.rows(TEN)
    inv.delete([r for r in rows if r.ocid == "ocid1.vcn..b"])
    ops = [c[:3] for c in fake.calls if c[2] in ("delete", "update")]
    assert ops[0] == ("network", "subnet", "delete")
    assert ("network", "route-table", "update") in ops  # default table emptied, not deleted
    deleted_ids = [c[c.index(f) + 1] for c in fake.calls if c[2] == "delete"
                   for f in c if f.endswith("-id") and f.startswith("--")]
    assert "sl-default" not in deleted_ids and "sl-extra" in deleted_ids
    assert ops[-1] == ("network", "vcn", "delete")
    assert "ocid1.vcn..b" not in fake.vcns


def test_subnet_in_use_failure_is_reported_and_the_rest_goes_on():
    fake = FakeOci(in_use={"ocid1.subnet..pub"})
    inv = Inventory(fake, lambda m: None)
    rows = inv.rows(TEN)
    pub = next(r for r in rows if r.ocid == "ocid1.subnet..pub")
    old = next(r for r in rows if r.ocid == "ocid1.subnet..old")
    failures = inv.delete([pub, old])
    assert len(failures) == 1 and "in use" in failures[0]
    assert ("network", "subnet", "delete", "--subnet-id", "ocid1.subnet..old") == fake.calls[-1][:5]


def test_review_asks_twice_before_deleting():
    fake = FakeOci()
    answers = {"check": True, "something else": False, "delete any": True, "Delete these now": False}
    def confirm(q):
        return next(v for k, v in answers.items() if k in q)
    inv = Inventory(fake, lambda m: None)
    review(inv, TEN, confirm, lambda q, d: "3" if "delete" in q else "", want_subnet=True)
    assert not any(c[2] == "delete" for c in fake.calls)


def test_review_deletes_after_final_yes_and_picks_subnet():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    rows = inv.rows(TEN)
    old_vcn = next(r.no for r in rows if r.ocid == "ocid1.vcn..b")
    pub = next(r.no for r in rows if r.ocid == "ocid1.subnet..pub")
    picked = review(inv, TEN, yes,
                    lambda q, d: str(old_vcn) if "delete" in q else str(pub), want_subnet=True)
    assert "ocid1.vcn..b" not in fake.vcns
    assert picked.subnet_id == "ocid1.subnet..pub" and picked.vm is None


def test_review_no_check_does_nothing():
    fake = FakeOci()
    assert review(Inventory(fake, lambda m: None), TEN, lambda q: False, lambda q, d: "", True).subnet_id == ""
    assert fake.calls == []


def test_private_subnet_cannot_be_picked():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    priv = next(r.no for r in inv.rows(TEN) if r.ocid == "ocid1.subnet..priv")
    answers = {"check": True, "delete any": False}
    picked = review(inv, TEN, lambda q: next(v for k, v in answers.items() if k in q),
                    lambda q, d: str(priv), want_subnet=True)
    assert picked.subnet_id == "" and picked.vm is None


def test_in_use_subnet_is_blocked_and_not_deleted():
    fake = FakeOci(in_use={"ocid1.subnet..pub"})
    out, echo = lines()
    inv = Inventory(fake, echo)
    no = next(r.no for r in inv.rows(TEN) if r.ocid == "ocid1.subnet..pub")
    review(inv, TEN, yes, lambda q, d: str(no) if "delete" in q else "", want_subnet=False)
    assert not any(c[2] == "delete" for c in fake.calls)
    assert any("still in use: IP 10.0.0.5: VM kyc-vm" in line for line in out)
    assert any("every choice is still in use" in line for line in out)


def test_vcn_dependencies_listed_and_in_use_child_blocks():
    fake = FakeOci(in_use={"ocid1.subnet..priv"})
    inv = Inventory(fake, lambda m: None)
    vcn = next(r for r in inv.rows(TEN) if r.ocid == "ocid1.vcn..a")
    also, blockers = inv.dependencies(vcn)
    assert "subnet public subnet" in also and "internet-gateway igw-1" in also
    assert "route-table rt-extra" in also and not any("rt-default" in a for a in also)
    assert blockers == ["subnet private subnet: IP 10.0.0.5: VM kyc-vm"]


def test_non_empty_compartment_is_blocked():
    inv = Inventory(FakeOci(), lambda m: None)
    comp = next(r for r in inv.rows(TEN) if r.kind == "Compartment")
    _, blockers = inv.dependencies(comp)
    assert blockers == ["Instance kyc-vm"]


def test_only_free_objects_are_deleted_from_a_mixed_choice():
    fake = FakeOci(in_use={"ocid1.subnet..pub"})
    inv = Inventory(fake, lambda m: None)
    rows = inv.rows(TEN)
    pub = next(r.no for r in rows if r.ocid == "ocid1.subnet..pub")
    old = next(r.no for r in rows if r.ocid == "ocid1.subnet..old")
    asked = []
    def confirm(q):
        asked.append(q)
        return "something else" not in q
    review(inv, TEN, confirm, lambda q, d: f"{pub},{old}" if "delete" in q else "", want_subnet=False)
    deleted = [c[c.index("--subnet-id") + 1] for c in fake.calls if c[:3] == ("network", "subnet", "delete")]
    assert deleted == ["ocid1.subnet..old"]
    assert any("Delete these now" in q and "old subnet" in q and "public subnet" not in q for q in asked)


def test_vm_dependencies_show_boot_volume_and_kept_volumes():
    inv = Inventory(FakeOci(), lambda m: None)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM")
    assert vm.public == "203.0.113.9" and vm.parent == "PoC"
    also, blockers = inv.dependencies(vm)
    assert any("boot volume ocid1.bootvolume..b" in a for a in also)
    assert any(a.startswith("block volume ocid1.volume..data") and a.endswith("detached and kept") for a in also)
    assert blockers == []


def test_vm_needs_its_name_typed():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM")
    answers = {"delete, comma": str(vm.no), "Type the VM name": "wrong-name"}
    review(inv, TEN, yes, lambda q, d: next((v for k, v in answers.items() if k in q), ""),
           want_subnet=False)
    assert not any(c[:3] == ("compute", "instance", "terminate") for c in fake.calls)


def test_vm_and_its_subnet_go_together_vm_first():
    fake = FakeOci(in_use={"ocid1.subnet..pub"})  # the VM's IP is in this subnet
    out, echo = lines()
    inv = Inventory(fake, echo)
    rows = inv.rows(TEN)
    vm = next(r for r in rows if r.kind == "VM")
    sub = next(r for r in rows if r.ocid == "ocid1.subnet..pub")
    answers = {"delete, comma": f"{sub.no},{vm.no}", "Type the VM name": "kyc-vm"}
    review(inv, TEN, yes, lambda q, d: next((v for k, v in answers.items() if k in q), ""),
           want_subnet=False)
    ops = [c[:3] for c in fake.calls if c[2] in ("terminate", "delete")]
    assert ops == [("compute", "instance", "terminate"), ("network", "subnet", "delete")]
    assert not any("still in use" in line for line in out)


def test_existing_vm_can_be_picked():
    inv = Inventory(FakeOci(), lambda m: None)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM")
    answers = {"check": True, "delete any": False}
    choice = review(inv, TEN, lambda q: next(v for k, v in answers.items() if k in q),
                    lambda q, d: str(vm.no) if "existing VM" in q else "", want_subnet=True)
    assert choice.vm == vm and choice.subnet_id == ""


class FakeCleaner:
    def __init__(self, dry=0, real=0):
        self.calls = []
        self.codes = {False: dry, True: real}

    def run(self, compartment_id, backup_id, execute, region=None):
        self.calls.append((compartment_id, backup_id, execute))
        return self.codes[execute]


def _pick_compartment(inv):
    return next(r for r in inv.rows(TEN) if r.kind == "Compartment")


def test_compartment_with_resources_goes_to_the_cleaner_dry_run_first():
    fake, cleaner = FakeOci(), FakeCleaner()
    inv = Inventory(fake, lambda m: None, cleaner)
    comp = _pick_compartment(inv)
    review(inv, TEN, yes, lambda q, d: str(comp.no) if "delete, comma" in q else "", want_subnet=False)
    assert cleaner.calls == [(comp.ocid, TEN, False), (comp.ocid, TEN, True)]
    assert any(c[:3] == ("iam", "compartment", "delete") for c in fake.calls)


def test_cleaner_stops_after_a_no_to_the_plan():
    fake, cleaner = FakeOci(), FakeCleaner()
    inv = Inventory(fake, lambda m: None, cleaner)
    comp = _pick_compartment(inv)
    review(inv, TEN, lambda q: "Run that plan" not in q and "something else" not in q,
           lambda q, d: str(comp.no) if "delete, comma" in q else "", want_subnet=False)
    assert cleaner.calls == [(comp.ocid, TEN, False)]
    assert not any(c[:3] == ("iam", "compartment", "delete") for c in fake.calls)


def test_failed_dry_run_deletes_nothing():
    fake, cleaner = FakeOci(), FakeCleaner(dry=1)
    inv = Inventory(fake, lambda m: None, cleaner)
    comp = _pick_compartment(inv)
    review(inv, TEN, yes, lambda q, d: str(comp.no) if "delete, comma" in q else "", want_subnet=False)
    assert [c[2] for c in cleaner.calls] == [False]
    assert not any(c[:3] == ("iam", "compartment", "delete") for c in fake.calls)


def test_sub_compartment_blocks_the_cleaner():
    fake, cleaner = FakeOci(), FakeCleaner()
    real = fake.__call__

    def with_child(*args):
        a = list(args)
        if a[:3] == ["iam", "compartment", "list"] and a[a.index("--compartment-id") + 1] == "ocid1.comp..x":
            return {"data": [{"id": "ocid1.comp..child", "name": "Child"}]}
        return real(*args)
    inv = Inventory(with_child, lambda m: None, cleaner)
    comp = _pick_compartment(inv)
    _, blockers = inv.dependencies(comp)
    assert "sub-compartment Child (remove it first)" in blockers
    review(inv, TEN, yes, lambda q, d: str(comp.no) if "delete, comma" in q else "", want_subnet=False)
    assert cleaner.calls == []


def test_service_vnic_owner_is_named():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    owner = inv.vnic_owner("vnic-service")
    query = [c[-1] for c in fake.calls if c[:3] == ("search", "resource", "structured-search")][0]
    assert "timeCreated <= '2026-11-04T01:39:02Z'" in query
    assert owner.startswith("probably PrivateEndpoint odoo-pe")
    assert "name-of-vnic-service" in owner


def test_vm_name_gets_three_tries():
    fake = FakeOci()
    out, echo = lines()
    inv = Inventory(fake, echo)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM")
    typed = iter(["intance1", "kyc-vm"])
    review(inv, TEN, yes,
           lambda q, d: str(vm.no) if "delete, comma" in q else (next(typed) if "Type the VM" in q else ""),
           want_subnet=False)
    assert any(c[:3] == ("compute", "instance", "terminate") for c in fake.calls)
    assert any("try again" in line for line in out)


def test_search_time_format_and_failure_does_not_stop():
    from vash.adapters.cloud.oci.inventory import _search_time
    assert _search_time("2026-11-04T01:39:02.547000+00:00") == "2026-11-04T01:39:02Z"
    assert _search_time("") == ""
    fake = FakeOci()
    real = fake.__call__
    def failing_search(*args):
        if args[:3] == ("search", "resource", "structured-search") and "timeCreated" in args[-1]:
            raise VashError("oci search failed: CannotParseRequest", "fix")
        return real(*args)
    owner = Inventory(failing_search, lambda m: None).vnic_owner("vnic-service")
    assert "owner unknown" in owner


def test_terminate_polls_instead_of_cli_wait():
    fake = FakeOci()
    slept = []
    inv = Inventory(fake, lambda m: None, sleep=slept.append)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM")
    assert inv.delete([vm]) == []
    term = [c for c in fake.calls if c[:3] == ("compute", "instance", "terminate")][0]
    assert "--wait-for-state" not in term
    assert any(c[:3] == ("compute", "instance", "get") for c in fake.calls)


def test_table_covers_every_other_resource_once():
    inv = Inventory(FakeOci(), lambda m: None)
    rows = inv.rows(TEN)
    kinds = [r.kind for r in rows]
    assert "Bucket" in kinds and "Vault" in kinds
    assert "Vnic" not in kinds
    assert sum(1 for r in rows if r.ocid == "ocid1.vcn..a") == 1


def test_other_resources_point_to_their_compartment_or_the_console():
    fake = FakeOci()
    out, echo = lines()
    inv = Inventory(fake, echo)
    rows = inv.rows(TEN)
    bucket = next(r for r in rows if r.kind == "Bucket")
    vault = next(r for r in rows if r.kind == "Vault")
    comp = next(r for r in rows if r.kind == "Compartment")
    answers = {"check": True, "delete any": True}
    review(inv, TEN, lambda q: next((v for k, v in answers.items() if k in q), False),
           lambda q, d: f"{bucket.no},{vault.no}" if "delete, comma" in q else "", want_subnet=False)
    assert any(f"choose its compartment PoC (S.No {comp.no})" in line for line in out)
    assert any("root-vault: in the root compartment" in line for line in out)
    assert not any(c[2] == "delete" for c in fake.calls)


class TwoRegionOci:
    """Minimal OCI: one VM in each of two regions, a related child tenancy, and one it cannot reach."""

    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        a = list(args)
        region = a[a.index("--region") + 1] if "--region" in a else None
        if a[:3] == ["iam", "region-subscription", "list"]:
            return {"data": [{"region-name": "me-jeddah-1", "is-home-region": True, "status": "READY"},
                             {"region-name": "eu-frankfurt-1", "status": "READY"}]}
        if a[:3] == ["organizations", "organization", "list"]:
            return {"data": {"items": [{"id": "org1", "parent-tenancy-id": TEN}]}}
        if a[:3] == ["organizations", "organization-tenancy", "list"]:
            return {"data": {"items": [{"tenancy-id": "ocid1.tenancy..child", "name": "child-a", "lifecycle-state": "ACTIVE"},
                                       {"tenancy-id": "ocid1.tenancy..locked", "name": "child-b", "lifecycle-state": "ACTIVE"}]}}
        if a[:3] == ["iam", "compartment", "list"]:
            if a[a.index("--compartment-id") + 1] == "ocid1.tenancy..locked":
                raise VashError("NotAuthorizedOrNotFound", "fix")
            return {"data": []}
        if a[:3] == ["compute", "instance", "list"]:
            comp = a[a.index("--compartment-id") + 1]
            return {"data": [{"id": f"vm-{comp[-5:]}-{region}", "display-name": f"vm-{region}", "lifecycle-state": "STOPPED"}]}
        if a[:3] == ["compute", "instance", "get"]:
            return {"data": {"lifecycle-state": "TERMINATED"}}
        if a[2] == "list" or a[:2] == ["search", "resource"]:
            return {"data": {"items": []}} if a[0] == "search" else {"data": []}
        return {"data": {}}


def test_all_regions_and_reachable_related_tenancies_are_listed():
    fake = TwoRegionOci()
    out, echo = lines()
    inv = Inventory(fake, echo, sleep=lambda s: None)
    review(inv, TEN, lambda q: "check" in q, lambda q, d: "", want_subnet=False)
    rows_regions = {(r.tenancy, r.region) for r in inv.rows(TEN) if r.kind == "VM"}
    assert ("", "me-jeddah-1") in rows_regions and ("", "eu-frankfurt-1") in rows_regions
    assert ("child-a", "me-jeddah-1") in rows_regions
    assert any("No access to child tenancy child-b" in line for line in out)
    assert not any(c[0] == "search" and "--region" in c and "child" in str(c) for c in fake.calls)


def test_delete_goes_to_the_row_region():
    fake = TwoRegionOci()
    inv = Inventory(fake, lambda m: None, sleep=lambda s: None)
    vm = next(r for r in inv.rows(TEN) if r.kind == "VM" and r.region == "eu-frankfurt-1" and not r.tenancy)
    inv.delete([vm])
    term = [c for c in fake.calls if c[:3] == ("compute", "instance", "terminate")][0]
    assert term[-2:] == ("--region", "eu-frankfurt-1")


def test_wrong_choice_is_explained_and_asked_again():
    out, echo = lines()
    inv = Inventory(FakeOci(), echo)
    rows = inv.rows(TEN)
    vcn = next(r.no for r in rows if r.ocid == "ocid1.vcn..a")
    pub = next(r.no for r in rows if r.ocid == "ocid1.subnet..pub")
    answers = iter([f"{vcn},{pub}", str(pub)])
    picked = review(inv, TEN, lambda q: "check" in q, lambda q, d: next(answers) if "public subnet" in q else "",
                    want_subnet=True, want_vm=False)
    assert picked.subnet_id == "ocid1.subnet..pub"
    assert any(f"'{vcn}' is not a valid choice" in line and f"{pub} = Subnet public subnet" in line
               for line in out)


def test_second_delete_round_in_the_same_run():
    fake = FakeOci()
    inv = Inventory(fake, lambda m: None)
    rows = inv.rows(TEN)
    rounds = iter(["ocid1.subnet..old", "ocid1.vcn..b"])
    more = iter([True, True, False])
    def confirm(q):
        return next(more) if ("delete any" in q or "something else" in q) else True
    review(inv, TEN, confirm, lambda q, d: next(rounds) if "delete, comma" in q else "", want_subnet=False)
    assert "ocid1.vcn..b" not in fake.vcns
    assert any(c[:3] == ("network", "subnet", "delete") for c in fake.calls)


def test_unpeered_lpg_goes_with_its_vcn_and_a_peered_one_blocks():
    fake = FakeOci()
    real = fake.__call__
    status = {"value": "NEW"}
    def with_lpg(*args):
        if args[:3] == ("network", "local-peering-gateway", "list"):
            fake.calls.append(args)
            return {"data": [{"id": "lpg-1", "display-name": "lpg", "peering-status": status["value"]}]}
        return real(*args)
    inv = Inventory(with_lpg, lambda m: None)
    vcn = next(r for r in inv.rows(TEN) if r.ocid == "ocid1.vcn..b")
    also, blockers = inv.dependencies(vcn)
    assert "local-peering-gateway lpg (not peered)" in also and blockers == []
    assert inv.delete([vcn]) == []
    assert any(c[:3] == ("network", "local-peering-gateway", "delete") for c in fake.calls)
    status["value"] = "PEERED"
    _, blockers = inv.dependencies(vcn)
    assert blockers == ["local-peering-gateway lpg: peered with another VCN (remove the peering first)"]


def test_vnic_owner_searched_tenancy_wide_when_not_in_its_compartment():
    fake = FakeOci()
    real = fake.__call__
    def by_scope(*args):
        if args[:3] == ("search", "resource", "structured-search") and "timeCreated" in args[-1]:
            fake.calls.append(args)
            if "compartmentId" in args[-1]:
                return {"data": {"items": []}}
            return {"data": {"items": [{"resource-type": "MountTarget", "display-name": "fs-mt",
                                        "time-created": "2026-11-04T01:38:00Z", "lifecycle-state": "ACTIVE"}]}}
        return real(*args)
    owner = Inventory(by_scope, lambda m: None).vnic_owner("vnic-service")
    assert owner.startswith("probably MountTarget fs-mt")
    wide = [c[-1] for c in fake.calls if c[:3] == ("search", "resource", "structured-search")][-1]
    assert "timeCreated >= '2026-11-04T01:29:02Z'" in wide
