import re

from ctreepo.spec.config_handler_registry import PreConfigHandlerRegistry

__all__ = ("expand_vty",)


@PreConfigHandlerRegistry.register("huawei_vrp")
def expand_vty(config: str) -> str:
    to_replace: list[tuple[str, str]] = []
    for block in re.finditer(
        pattern=r"(\n|^)user-interface vty (?P<start>\d+) (?P<end>\d+)\n(?P<params>.*?)\n(?!\s)",
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
