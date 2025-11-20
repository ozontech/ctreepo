from ctreepo.tagging import TaggingRulesFromDict


def test_basic_dict_parsing(config_tags_dict: dict[str, list[str]]) -> None:
    rules = TaggingRulesFromDict("cisco_iosxe", config_tags_dict)
    assert set(rules.rules.keys()) == {"cisco_iosxe"}

    cisco_rules = rules.rules["cisco_iosxe"]
    assert len(cisco_rules) == len(config_tags_dict)
    for rule in cisco_rules:
        assert rule.regex in config_tags_dict
        assert rule.tags == set(config_tags_dict.get(rule.regex, []))
