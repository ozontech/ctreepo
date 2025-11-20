from ctreepo import CTreeEnv, Vendor


def get_configs() -> str:
    with open(file="./examples/configs/cisco-example-1.txt", mode="r") as f:
        config = f.read()
    return config


def get_ct_environment() -> CTreeEnv:
    return CTreeEnv(vendor=Vendor.CISCO)


if __name__ == "__main__":
    config_config = get_configs()
    env = get_ct_environment()
    current = env.parse(config_config)

    print("\n---дерево в виде привычной конфигурации---")
    print(current.config)

    print("\n---конфигурация с маскированными секретами---")
    print(current.masked_config)

    print("\n---дерево в виде патча для устройства---")
    print(current.patch)

    print("\n---патч с маскированными секретами---")
    print(current.masked_patch)

    print("\n---дерево в виде формальной конфигурации (аналогично formal в ios-xr)---")
    print(current.formal_config)
