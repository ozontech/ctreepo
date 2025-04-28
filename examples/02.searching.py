from ctreepo import CTreeEnv, Vendor


def get_configs() -> str:
    with open(file="./examples/configs/cisco-example-1.txt", mode="r") as f:
        config = f.read()
    return config


def get_ct_environment() -> CTreeEnv:
    tagging_rules: list[dict[str, str | list[str]]] = [
        {
            "regex": r"^router bgp \d+$",
            "tags": ["bgp"],
        },
        {
            "regex": r"^interface (Tunnel1) / ip address \S+ \S+(?: )?(secondary)?$",
            "tags": ["interface", "tunnel-1-ip"],
        },
        {
            "regex": r"^interface (Tunnel2) / ip address \S+ \S+(?: )?(secondary)?$",
            "tags": ["interface", "tunnel-1-ip"],
        },
        {
            "regex": r"^interface (\S+)$",
            "tags": ["interface"],
        },
    ]
    return CTreeEnv(
        vendor=Vendor.CISCO,
        tagging_rules=tagging_rules,
    )


if __name__ == "__main__":
    config = get_configs()
    env = get_ct_environment()

    router = env.parse(config)

    print("\n---все вхождения 'address'---")
    address = env.search(router, string="address")
    print(address.config)

    print("\n---все вхождения 'address' с возможными потомками---")
    address_children = env.search(router, string="address", include_children=True)
    print(address_children.config)

    print("\n---все вхождения 'address \\d{1,3}'---")
    address_ip = env.search(router, string=r"address \d{1,3}")
    print(address_ip.config)

    print("\n---конфигурация по тегу 'bgp'---")
    bgp = env.search(router, include_tags=["bgp"])
    print(bgp.config)

    print("\n---все, кроме тега 'bgp'---")
    no_bgp = env.search(router, exclude_tags=["bgp"])
    print(no_bgp.config)

    print("\n---конфигурация по тегу 'secondary'---")
    secondary = env.search(router, include_tags=["secondary"])
    print(secondary.config)

    print("\n---конфигурация по тегу 'tunnel-1-ip'---")
    tunnel_1_ip = env.search(router, include_tags=["tunnel-1-ip"])
    print(tunnel_1_ip.config)
