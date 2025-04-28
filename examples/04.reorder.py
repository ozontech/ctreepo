from ctreepo import CTreeEnv, Vendor


def get_configs() -> str:
    with open(file="./examples/configs/cisco-example-4.txt", mode="r") as f:
        config = f.read()
    return config


def get_ct_environment() -> CTreeEnv:
    tagging_rules: list[dict[str, str | list[str]]] = [
        {"regex": r"^router bgp .* neighbor (\S+) route-map (\S+) (?:in|out)", "tags": ["rm-attach"]},
        {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
        {"regex": r"^route-map (\S+) (?:permit|deny) \d+$", "tags": ["rm"]},
        {"regex": r"^ip community-list (?:standard|expanded) (\S+)", "tags": ["cl"]},
        {"regex": r"^ip prefix-list (\S+)", "tags": ["pl"]},
    ]
    return CTreeEnv(
        vendor=Vendor.CISCO,
        tagging_rules=tagging_rules,
    )


if __name__ == "__main__":
    config = get_configs()
    env = get_ct_environment()
    router = env.parse(config)

    print("\n--community-list -> prefix-list -> route-map -> bgp -> untagged--")
    router.reorder(["cl", "pl", "rm", "bgp"])
    print(router.config)

    print("\n--bgp -> community-list -> prefix-list -> route-map -> untagged -> rm-attach--")
    wo_rm_attach = env.search(router, exclude_tags=["rm-attach"])
    rm_attach = env.search(router, include_tags=["rm-attach"])
    wo_rm_attach.reorder(["bgp", "cl", "pl", "rm"])
    print(wo_rm_attach.config)
    print(rm_attach.config)
