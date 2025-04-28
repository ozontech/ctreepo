from textwrap import dedent

import pytest

from ctreepo import CTreeDiffer, CTreeParser, Vendor
from ctreepo.vendors import AristaCT, HuaweiCT


def test_differ_vendor_mismatch() -> None:
    config = dedent(
        """
        ip community-list CL_NAME_1
         community 123:12345
        """
    )
    parser1 = CTreeParser(vendor=Vendor.HUAWEI)
    parser2 = CTreeParser(vendor=Vendor.ARISTA)
    root1 = parser1.parse(config)
    root2 = parser2.parse(config)
    assert root1.__class__ == HuaweiCT
    assert root2.__class__ == AristaCT

    with pytest.raises(RuntimeError) as exc:
        CTreeDiffer.diff(root1, root2)
    assert str(exc.value) == "a and b should be instances of the same class"
