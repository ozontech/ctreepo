from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Platform
from ctreepo.platforms import AristaEOS, HuaweiVRP


def test_differ_platform_mismatch() -> None:
    config = dedent(
        """
        ip community-list CL_NAME_1
         community 123:12345
        """,
    )
    parser1 = CTreeParser(platform=Platform.HUAWEI_VRP)
    parser2 = CTreeParser(platform=Platform.ARISTA_EOS)
    root1 = parser1.parse(config)
    root2 = parser2.parse(config)
    assert root1.__class__ == HuaweiVRP
    assert root2.__class__ == AristaEOS

    with pytest.raises(RuntimeError) as exc:
        CTreeDiffer.diff(root1, root2)
    assert str(exc.value) == "a and b should be instances of the same class"
