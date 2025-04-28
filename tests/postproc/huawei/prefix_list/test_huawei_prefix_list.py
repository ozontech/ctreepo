from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_prefix_list_delete() -> None:
    current_config = dedent(
        """
        ip ip-prefix TEST_PL_1 index 10 permit 10.1.50.0 23 greater-equal 32 less-equal 32
        ip ip-prefix TEST_PL_2 index 10 permit 10.2.50.0 23 greater-equal 32 less-equal 32
        ip ip-prefix TEST_PL_3 index 10 permit 10.3.50.0 24 greater-equal 32 less-equal 32
        """
    ).strip()
    target_config = dedent(
        """
        ip ip-prefix TEST_PL_1 index 10 permit 10.0.0.0 243 greater-equal 32 less-equal 32
        ip ip-prefix TEST_PL_3 index 10 permit 10.3.50.0 24 greater-equal 32 less-equal 32
        """
    ).strip()
    diff_config = dedent(
        """
        ip ip-prefix TEST_PL_1 index 10 permit 10.0.0.0 243 greater-equal 32 less-equal 32
        #
        undo ip ip-prefix TEST_PL_2 index 10
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        ip ip-prefix TEST_PL_1 index 10 permit 10.0.0.0 243 greater-equal 32 less-equal 32
        undo ip ip-prefix TEST_PL_2 index 10
        """
    ).strip()

    parser = CTreeParser(vendor=Vendor.HUAWEI)

    current = parser.parse(current_config)
    target = parser.parse(target_config)

    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch
