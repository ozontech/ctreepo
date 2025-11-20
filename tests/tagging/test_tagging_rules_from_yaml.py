import yaml

from ctreepo.tagging import TaggingRulesFromYAML


def test_basic_yaml_parsing(config_tags_yaml_file: str) -> None:
    rules = TaggingRulesFromYAML(config_tags_yaml_file)

    print(rules.rules)
    with open(config_tags_yaml_file) as f:
        yaml_rules = yaml.safe_load(f.read()).get(rules.yaml_key)

    assert len(rules.rules) == len(yaml_rules)
    assert set(rules.rules.keys()) == set(yaml_rules)
