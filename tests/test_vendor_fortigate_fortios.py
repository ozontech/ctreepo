from textwrap import dedent

import pytest

from ctreepo import CTree, CTreeParser, Vendor
from ctreepo.parser import TaggingRulesDict


@pytest.fixture()
def root() -> CTree:
    config_str = dedent(
        """
        #global_vdom=1
        config system global
            set admin-concurrent enable
            set admin-console-timeout 0
            set admin-restrict-local disable
            set admin-scp disable
            set admin-sport 443
            set admin-ssh-port 22
            set admin-telnet-port 23
        end
        config system interface
            edit "port1"
                set vdom "root"
                set mode static
                set bfd global
                set icmp-send-redirect enable
                set icmp-accept-redirect enable
                set external disable
                set description ''
                config ipv6
                    set ip6-mode static
                    set nd-mode basic
                    unset ip6-allowaccess
                end
                set priority 0
                set speed auto
            next
            edit "port2"
                set vdom "root"
                set mode static
                set bfd global
                set icmp-send-redirect enable
                set icmp-accept-redirect enable
                set external disable
                set description ''
                config ipv6
                    set ip6-mode static
                    set nd-mode basic
                    unset ip6-allowaccess
                end
                set priority 0
                set speed auto
            next
        end
        config system replacemsg mail "partial"
            set buffer "Fragmented emails are blocked."
            set header 8bit
            set format text
        end
        """,
    )
    tagging_rules_dict = {
        Vendor.FORTINET: [
            {"regex": r"^config system global$", "tags": ["system"]},
            {"regex": r'^config system interface / edit "(\S+)"$', "tags": ["interface"]},
            {"regex": r'^config system replacemsg (mail) "(\S+)"$', "tags": ["replacemsg"]},
        ],
    }
    loader = TaggingRulesDict(tagging_rules_dict)  # type: ignore[arg-type]
    parser = CTreeParser(
        vendor=Vendor.FORTINET,
        tagging_rules=loader,
    )
    root: CTree = parser.parse(config_str)
    return root


def test_config(root: CTree) -> None:
    config = dedent(
        """
        config system global
            set admin-concurrent enable
            set admin-console-timeout 0
            set admin-restrict-local disable
            set admin-scp disable
            set admin-sport 443
            set admin-ssh-port 22
            set admin-telnet-port 23

        config system interface
            edit "port1"
                set vdom "root"
                set mode static
                set bfd global
                set icmp-send-redirect enable
                set icmp-accept-redirect enable
                set external disable
                set description ''
                config ipv6
                    set ip6-mode static
                    set nd-mode basic
                    unset ip6-allowaccess
                set priority 0
                set speed auto
            edit "port2"
                set vdom "root"
                set mode static
                set bfd global
                set icmp-send-redirect enable
                set icmp-accept-redirect enable
                set external disable
                set description ''
                config ipv6
                    set ip6-mode static
                    set nd-mode basic
                    unset ip6-allowaccess
                set priority 0
                set speed auto

        config system replacemsg mail "partial"
            set buffer ""
            set header 8bit
            set format text
        """,
    ).lstrip()
    assert root.config == config


def test_patch(root: CTree) -> None:
    patch = dedent(
        """
        config system global
        set admin-concurrent enable
        set admin-console-timeout 0
        set admin-restrict-local disable
        set admin-scp disable
        set admin-sport 443
        set admin-ssh-port 22
        set admin-telnet-port 23
        end
        config system interface
        edit "port1"
        set vdom "root"
        set mode static
        set bfd global
        set icmp-send-redirect enable
        set icmp-accept-redirect enable
        set external disable
        set description ''
        config ipv6
        set ip6-mode static
        set nd-mode basic
        unset ip6-allowaccess
        end
        set priority 0
        set speed auto
        next
        edit "port2"
        set vdom "root"
        set mode static
        set bfd global
        set icmp-send-redirect enable
        set icmp-accept-redirect enable
        set external disable
        set description ''
        config ipv6
        set ip6-mode static
        set nd-mode basic
        unset ip6-allowaccess
        end
        set priority 0
        set speed auto
        next
        end
        config system replacemsg mail "partial"
        set buffer ""
        set header 8bit
        set format text
        end
        """,
    ).strip()
    assert root.patch == patch


def test_patch_to_root(root: CTree) -> None:
    patch = dedent(
        """
        config system interface
        edit "port2"
        config ipv6
        set ip6-mode static
        set nd-mode basic
        unset ip6-allowaccess
        end
        next
        end
        """,
    ).strip()
    partial = root.children["config system interface"].children['edit "port2"'].children["config ipv6"]
    assert partial.patch == patch
