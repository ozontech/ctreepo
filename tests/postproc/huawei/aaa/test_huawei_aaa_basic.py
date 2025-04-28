from textwrap import dedent

from ctreepo import CTreeDiffer, CTreeParser, Vendor


def test_huawei_aaa_basic() -> None:
    """Базовая настройка aaa.

    Тест на двойной quit для пустых секций.
    """
    current_config = dedent(
        """
        aaa
         authorization-scheme scheme-name
          authorization-mode local if-authenticated
        """
    )
    target_config = dedent(
        """
        aaa
         undo local-user policy security-enhance
         default-domain admin domain-name
         authentication-scheme default
         authentication-scheme scheme-name
          authentication-mode hwtacacs local
         authentication-scheme local
         authorization-scheme default
         authorization-scheme scheme-name
          authorization-mode local if-authenticated
         accounting-scheme default
         domain default
         domain default_admin
         domain domain-name
          authentication-scheme group-name
          authorization-scheme group-name
          hwtacacs server group-name
         domain local
          authentication-scheme local
        """
    ).strip()
    diff_config = dedent(
        """
        aaa
         undo local-user policy security-enhance
         default-domain admin domain-name
         authentication-scheme default
         authentication-scheme scheme-name
          authentication-mode hwtacacs local
         authentication-scheme local
         authorization-scheme default
         accounting-scheme default
         domain default
         domain default_admin
         domain domain-name
          authentication-scheme group-name
          authorization-scheme group-name
          hwtacacs server group-name
         domain local
          authentication-scheme local
        #
        """
    ).strip()
    diff_patch = dedent(
        """
        aaa
        undo local-user policy security-enhance
        default-domain admin domain-name
        authentication-scheme default
        quit
        authentication-scheme scheme-name
        authentication-mode hwtacacs local
        quit
        authentication-scheme local
        quit
        authorization-scheme default
        quit
        accounting-scheme default
        quit
        domain default
        quit
        domain default_admin
        quit
        domain domain-name
        authentication-scheme group-name
        authorization-scheme group-name
        hwtacacs server group-name
        quit
        domain local
        authentication-scheme local
        quit
        quit
        """
    ).strip()

    parser = CTreeParser(Vendor.HUAWEI)
    current = parser.parse(current_config)
    target = parser.parse(target_config)
    diff = CTreeDiffer.diff(current, target)
    assert diff.config == diff_config
    assert diff.patch == diff_patch
