import pytest

from ctreepo.parser import CTreeParser


@pytest.fixture(scope="package")
def parser() -> CTreeParser:
    parser = CTreeParser("huawei_vrp")
    return parser
