import re

from .ctree import CTree
from .models import Vendor

__all__ = (
    "AristaCT",
    "CiscoCT",
    "HuaweiCT",
)


class AristaCT(CTree):
    vendor = Vendor.ARISTA
    spaces = "   "
    undo = "no"
    section_exit = "exit"
    section_separator = "!"
    sections_require_exit = [
        r"route-map \S+ (?:deny|permit) \d+",
        r"vlan \d+.*",
    ]
    sections_without_exit = []
    junk_lines = [
        r"\s*!.*",
        r"end",
    ]
    mask_patterns = [
        r".*(?:password|secret)(?: sha512)? (\S+)",
        r".*(?:key|md5)(?: 7)? (\S+)",
    ]


class CiscoCT(CTree):
    vendor = Vendor.CISCO
    spaces = " "
    undo = "no"
    section_exit = "exit"
    section_separator = "!"
    sections_require_exit = [
        r"route-map \S+ (?:deny|permit) \d+",
    ]
    sections_without_exit = [
        r"crypto pki certificate chain \S+ / certificate(?: ca| self-signed)? \S+",
    ]
    junk_lines = [
        r"\s*!.*",
        r"Building configuration...",
        r"Current configuration : \d+ bytes",
        r"version \S+",
        r"\s*exit-address-family",
        r"end",
    ]
    mask_patterns = [
        r".*secret (?:5|9|7) (\S+)",
    ]
    new_line_mask = "<<br>>"

    @classmethod
    def _mask_banners(cls, config: str) -> str:
        banners = []
        for section in re.finditer(
            r"banner (?P<type>(?:motd|login|exec)) (?P<sep>\S+)(?P<body>.*?)(?P=sep)\n",
            config,
            re.DOTALL,
        ):
            banners.append(section.group("body"))
        for banner in banners:
            config = config.replace(banner, banner.replace("\n", cls.new_line_mask))
        return config

    @classmethod
    def _mask_certificates(cls, config: str) -> str:
        certificates = []
        for cert in re.finditer(
            r"(?<=\s)certificate(?: ca| self-signed)? \S+\n(?P<body>.*?\s+quit)(?=\n)",
            config,
            re.DOTALL,
        ):
            certificates.append(cert.group("body"))
        for certificate in certificates:
            config = config.replace(certificate, certificate.replace("\n", cls.new_line_mask))
        return config

    @classmethod
    def pre_run(cls, config: str) -> str:
        config = cls._mask_banners(config)
        config = cls._mask_certificates(config)
        return config

    def post_run(self) -> None:
        for node in self.children.values():
            if node.line.startswith(("banner motd", "banner exec", "banner login")):
                node.line = node.line.replace(self.new_line_mask, "\n")
            elif node.line.startswith("crypto pki certificate chain"):
                for certificates in node.children.values():
                    for cert_body in certificates.children.values():
                        cert_body.line = cert_body.line.replace(self.new_line_mask, "\n")
                    certificates.rebuild()
        self.rebuild()


class HuaweiCT(CTree):
    vendor = Vendor.HUAWEI
    spaces = " "
    undo = "undo"
    section_exit = "quit"
    section_separator = "#"
    sections_require_exit = [
        r"route-policy \S+ (?:deny|permit) node \d+",
        r"aaa / authentication-scheme \S+",
        r"aaa / authorization-scheme \S+",
        r"aaa / accounting-scheme \S+",
        r"aaa / service-scheme \S+",
        r"aaa / domain \S+",
        r"(?:radius|hwtacacs)-server template \S+",
        r"(?:dot1x|mac)-access-profile \S+",
        r"authentication-profile \S+",
        r"interface \S+",
    ]
    sections_without_exit = [
        r"xpl \S+ .*",
    ]
    junk_lines = [
        r"\s*#.*",
        r"!.*",
        r"return",
    ]
    mask_patterns = [
        r".*(?:auth-code|(?:pre-)?shared-key|password|md5|key|authentication|read) cipher (\S+)(?: \S+)*",
        r".*password irreversible-cipher (\S+)",
        r".*pass-phrase (\S+) aes",
        r".*snmp-agent community (?:read|write) (\S+)",
    ]

    @classmethod
    def _remove_spaces(cls, config: str) -> str:
        # у huawei в некоторых устройствах/версиях некоторые глобальные команды
        # выглядят так, как будто они находятся внутри секции, это ломает парсинг.
        # например пробел(ы) перед ntp-service, хотя это глобальный конфиг
        # #
        #  ntp-service server disable
        #  ntp-service source-interface LoopBack0
        #  ntp-service unicast-server 1.2.3.4
        # #
        # или пробел перед http
        # #
        #  http timeout 60
        #  http secure-server ssl-policy default_policy
        #  http server enable
        # #
        # поэтому удаляем пробел из конфигурации перед анализом

        result = []
        section = False
        for line in config.splitlines():
            if len(line) == 0:
                continue
            if line == "#":
                section = False
                space_count = 0
            elif not line.startswith(" "):
                section = True
            if line.startswith(" ") and not section:
                if space_count == 0:
                    space_count = len(line) - len(line.lstrip())
                result.append(line.removeprefix(" " * space_count))
            else:
                result.append(line)
        return "\n".join(result)

    @classmethod
    def _expand_vty(cls, config: str) -> str:
        to_replace: list[tuple[str, str]] = []
        for block in re.finditer(
            pattern=r"(?<=\n)user-interface vty (?P<start>\d+) (?P<end>\d+)\n(?P<params>.*?)\n(?!\s)",
            string=config,
            flags=re.DOTALL,
        ):
            new_lines = []
            start = int(block.group("start"))
            end = int(block.group("end"))
            params = block.group("params")
            for vty in range(start, end + 1):
                new_lines.append(f"user-interface vty {vty}")
                new_lines.extend(params.splitlines())

            to_replace.append((block.group(0).strip(), "\n".join(new_lines)))

        for old, new in to_replace:
            config = config.replace(old, new)

        return config

    @classmethod
    def pre_run(cls, config: str) -> str:
        config = cls._remove_spaces(config)
        config = cls._expand_vty(config)
        return config
