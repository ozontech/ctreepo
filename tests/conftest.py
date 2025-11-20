from dataclasses import dataclass

import pytest
import yaml


@dataclass(slots=True, frozen=True, repr=False)
class YamlTestCase:
    current: str
    target: str
    template: str
    diff: str
    patch: str


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "yaml_data" not in metafunc.fixturenames:
        return

    yaml_path = metafunc.definition.path.with_suffix(".yaml")

    if not yaml_path.is_file():
        pytest.exit(f"файл {str(yaml_path)!r} не найден")

    with open(yaml_path) as f:
        cases = yaml.safe_load(f)

    params = [
        pytest.param(
            YamlTestCase(
                current=case["current"],
                target=case["target"],
                template=case.get("template", ""),
                diff=case["diff"].strip(),
                patch=case.get("patch", "").strip(),
            ),
            id=case.get("name", f"case-{i}"),
        )
        for i, case in enumerate(cases)
    ]
    metafunc.parametrize("yaml_data", params)
