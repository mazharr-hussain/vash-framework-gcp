"""VASH command line interface (C-15)."""
import sys
import argparse
from pathlib import Path
from typing import Sequence
from vash import __version__
from vash.core.exceptions import VashError, NotAvailableYet

def main(argv: Sequence[str] | None = None) -> int:
    """Run the VASH CLI."""
    parser = argparse.ArgumentParser(prog="vash", description="VASH Engine")
    parser.add_argument("--version", action="store_true", help="Show version")
    subparsers = parser.add_subparsers(dest="command")

    p_init = subparsers.add_parser("init", help="Create a project from the scaffold")
    p_init.add_argument("target", nargs="?", default=".")
    p_init.add_argument("--repo", type=Path, default=Path.cwd())
    p_check = subparsers.add_parser("check", help="Run Stage 0 checks")
    p_check.add_argument("--repo", type=Path, default=Path.cwd())
    p_load = subparsers.add_parser("load", help="Rebuild .claude/ and CLAUDE.md")
    p_load.add_argument("--repo", type=Path, default=Path.cwd())
    p_ava = subparsers.add_parser("ava", help="Run an AvA activity")
    p_ava.add_argument("task_id")
    p_ava.add_argument("--repo", type=Path, default=Path.cwd())
    p_cost = subparsers.add_parser("cost", help="Show cost meter status")
    p_cost.add_argument("--repo", type=Path, default=Path.cwd())
    p_status = subparsers.add_parser("status", help="Show freeze and audit status")
    p_status.add_argument("--repo", type=Path, default=Path.cwd())
    for kind in ("skill", "agent"):
        p_kind = subparsers.add_parser(kind, help=f"Create or check {kind}s (portable, Agent Skills standard)")
        kind_sub = p_kind.add_subparsers(dest="action", required=True)
        p_new = kind_sub.add_parser("new", help=f"Create a {kind} from the template")
        p_new.add_argument("name")
        p_new.add_argument("--description", required=True, help="What it does and when to use it")
        p_new.add_argument("--searched", default="to-record", help="LAW 3: what was searched first")
        p_new.add_argument("--catalog", action="store_true", help="Create it in the VASH catalog, not the project")
        p_new.add_argument("--repo", type=Path, default=Path.cwd())
        p_val = kind_sub.add_parser("validate", help="Validate every skill and agent")
        p_val.add_argument("--repo", type=Path, default=Path.cwd())
        if kind == "skill":
            p_sug = kind_sub.add_parser("suggest", help="Rule R15: propose skills for repeated work")
            p_sug.add_argument("--repo", type=Path, default=Path.cwd())
            p_sug.add_argument("--min", type=int, default=3, help="Repetitions that make a skill")
            p_sug.add_argument("--similarity", type=float, default=0.8)
            p_sug.add_argument("--open-issues", action="store_true", help="Open one issue per proposal")
            p_sug.add_argument("--label", action="append", help="Label for the opened issues")
    p_onboard = subparsers.add_parser("onboard", help="Create a cloud runner VM with VASH installed")
    p_onboard.add_argument("cloud", help="Cloud adapter id from the catalog")
    p_onboard.add_argument("--down", action="store_true", help="Remove what onboarding created")
    p_onboard.add_argument("--yes", action="store_true", help="Do not ask before creating or removing")
    p_onboard.add_argument("--runner-repo", help="owner/name: register a self-hosted CI runner for it")
    p_onboard.add_argument("--admin-cidr", help="CIDR allowed to SSH (default: this shell's IP/32)")
    p_onboard.add_argument("--compartment", help="Compartment name; when missing: default vash after a yes, else typed; created only after a yes")
    p_onboard.add_argument("--cleanup-only", action="store_true", help="Only list and delete existing objects; no VM setup")
    p_onboard.add_argument("--no-inventory", action="store_true", help="Skip the list of existing compartments, VCNs and subnets")
    p_onboard.add_argument("--name-prefix", help="Prefix of new object names, e.g. north; when missing: default vash after a yes, else typed")
    p_onboard.add_argument("--vm-ip", help="Install on this existing VM instead of creating one")
    p_onboard.add_argument("--ssh-user", help="SSH user of the existing VM (default ubuntu)")
    p_onboard.add_argument("--ssh-key", help="Private key for the existing VM (default ~/.ssh/id_rsa)")
    p_onboard.add_argument("--subnet-id", help="Existing public subnet to use; no network is created")
    p_onboard.add_argument("--ocpus", type=int, default=2)
    p_onboard.add_argument("--memory", type=int, default=12, help="GB of memory")
    p_onboard.add_argument("--os-version", default="24.04")
    p_onboard.add_argument("--model", default="qwen2.5-coder:7b", help="Model to pull on the VM")
    p_onboard.add_argument("--workdir", help="Where the terraform state is kept")

    args = parser.parse_args(argv)

    if args.version:
        print(f"vash {__version__}")
        return 0

    if not args.command:
        parser.print_help()
        return 2

    try:
        if args.command == "init":
            from vash.cli.init import run
            return run(args.target, args.repo)
        elif args.command == "check":
            from vash.cli.check import run
            return run(args.repo)
        elif args.command == "load":
            from vash.cli.load import run
            return run(args.repo)
        elif args.command == "ava":
            from vash.cli.ava import run
            return run(args.repo, args.task_id)
        elif args.command == "cost":
            from vash.cli.cost import run
            return run(args.repo)
        elif args.command == "status":
            from vash.cli.status import run
            return run(args.repo)
        elif args.command in ("skill", "agent"):
            from vash.cli import skill as skill_cli
            if args.action == "new":
                return skill_cli.new_skill(args) if args.command == "skill" else skill_cli.new_agent(args)
            if args.action == "validate":
                return skill_cli.validate(args)
            return skill_cli.suggest(args)
        elif args.command == "onboard":
            from vash.cli.onboard import run
            return run(args)
    except NotAvailableYet as e:
        print(f"Error: {e}")
        return 0
    except VashError as e:
        print(f"Error: {e}")
        return e.exit_code

    return 2

def cli() -> None:
    """Entry point for the vash command."""
    sys.exit(main())
