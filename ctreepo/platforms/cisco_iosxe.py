import re

from ctreepo.ctree import CTree
from ctreepo.models import Platform

__all__ = ("CiscoIOSXE",)


class CiscoIOSXE(CTree):
    platform = Platform.CISCO_IOSXE
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
