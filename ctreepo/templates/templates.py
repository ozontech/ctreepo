from pathlib import Path

from ctreepo.models import Platform

__all__ = ("TEMPLATES",)


TEMPLATES = dict.fromkeys(Platform, "")

for platform in TEMPLATES:
    template_file = Path(Path(__file__).parent, platform).with_suffix(".txt")
    with open(template_file, "r") as f:
        data = f.read()
    TEMPLATES[platform] = data
