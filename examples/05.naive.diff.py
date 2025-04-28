from ctreepo import CTreeEnv, Vendor


def get_configs() -> tuple[str, str]:
    with open(file="./examples/configs/cisco-naive-diff-target.txt", mode="r") as f:
        target = f.read()
    with open(file="./examples/configs/cisco-naive-diff-existed.txt", mode="r") as f:
        existed = f.read()

    return existed, target


def get_ct_environment() -> CTreeEnv:
    return CTreeEnv(vendor=Vendor.CISCO)


if __name__ == "__main__":
    existed_config, target_config = get_configs()
    env = get_ct_environment()
    existed = env.parse(existed_config)
    target = env.parse(target_config)

    print("\n---Наивная разница конфигураций---")
    diff = env.diff(a=existed, b=target)
    print(diff.config)

    print("\n---Наивная разница конфигураций: без очистки---")
    diff_without_clear = env.search(diff, exclude_tags=["post"])
    print(diff_without_clear.config)

    print("\n---Наивная разница конфигураций: только очистка---")
    diff_clear = env.search(diff, include_tags=["post"])
    print(diff_clear.config)
