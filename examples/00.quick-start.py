from ctreepo import CTreeEnv, Vendor


def get_configs() -> tuple[str, str]:
    with open(file="./examples/configs/cisco-router-1.txt", mode="r") as f:
        current_config = f.read()
    with open(file="./examples/configs/cisco-router-2.txt", mode="r") as f:
        target_config = f.read()
    return current_config, target_config


def get_ct_environment() -> CTreeEnv:
    tagging_rules: list[dict[str, str | list[str]]] = [
        {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
        {"regex": r"^ip route \S+", "tags": ["static"]},
    ]
    return CTreeEnv(
        vendor=Vendor.CISCO,
        tagging_rules=tagging_rules,
    )


if __name__ == "__main__":
    current_config, target_config = get_configs()
    env = get_ct_environment()

    current = env.parse(current_config)
    target = env.parse(target_config)
    diff = env.diff(current, target)

    print("\n!-- разница конфигураций --")
    print(diff.config)

    print("\n!-- разница без секций с тегами bgp и static --")
    diff_no_routing = env.search(diff, exclude_tags=["bgp", "static"])
    print(diff_no_routing.config)

    print("\n!-- разница в секции с тегом bgp --")
    diff_bgp = env.search(diff, include_tags=["bgp"])
    print(diff_bgp.config)
