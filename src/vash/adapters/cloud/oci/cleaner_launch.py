"""Start Oracle's compartment cleaner with Cloud Shell sign-in added.

Usage: python -m vash.adapters.cloud.oci.cleaner_launch <sample dir> <cleaner arguments...>

The cleaner signs in with a config file, instance principal or resource principal.
OCI Cloud Shell signs in with a delegation token (OCI_CLI_CLOUD_SHELL=True and a
`delegation_token_file` in its config); for that case this launcher supplies the
matching SDK signer. Everywhere else the cleaner's own sign-in is used unchanged.
"""
from __future__ import annotations

import configparser
import os
import sys
from pathlib import Path


def _cloud_shell_token() -> str | None:
    if os.environ.get("OCI_CLI_CLOUD_SHELL", "").lower() != "true":
        return None
    cfg = Path(os.environ.get("OCI_CONFIG_FILE", str(Path.home() / ".oci" / "config")))
    if not cfg.exists():
        return None
    parser = configparser.ConfigParser()
    parser.read(cfg)
    profile = os.environ.get("OCI_CONFIG_PROFILE", "DEFAULT")
    section = parser[profile] if parser.has_section(profile) else parser["DEFAULT"]
    token_file = section.get("delegation_token_file")
    if not token_file or not Path(token_file).exists():
        return None
    return Path(token_file).read_text().strip()


def main(argv: list[str]) -> int:
    sample_dir, cleaner_args = argv[0], argv[1:]
    sys.path.insert(0, sample_dir)
    from oci_compartment_cleaner import runtime  # noqa: E402  (from the pinned sample)
    from oci_compartment_cleaner.cli import main as cleaner_main  # noqa: E402

    token = _cloud_shell_token()
    if token is not None:
        import oci

        def cloud_shell_auth(args):
            signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=token)
            return {"region": args.region}, signer

        runtime.auth_config_and_signer = cloud_shell_auth
    sys.argv = ["oci_compartment_cleaner", *cleaner_args]
    return int(cleaner_main() or 0)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
