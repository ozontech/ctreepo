from ctreepo import CTreeEnv, Vendor


def get_configs() -> tuple[str, str]:
    with open(file="./examples/configs/cisco-no-diff-section-target.txt", mode="r") as f:
        target = f.read()
    with open(file="./examples/configs/cisco-no-diff-section-existed.txt", mode="r") as f:
        existed = f.read()

    return existed, target


def get_ct_environment_naive() -> CTreeEnv:
    return CTreeEnv(vendor=Vendor.CISCO)


def get_ct_environment_no_diff() -> CTreeEnv:
    return CTreeEnv(
        vendor=Vendor.CISCO,
        no_diff_sections=[
            r"prefix-set \S+",
            r"route-policy \S+",
        ],
    )


if __name__ == "__main__":
    existed_config, target_config = get_configs()

    print("\n---Наивная разница конфигураций---")
    env_naive = get_ct_environment_naive()
    existed = env_naive.parse(existed_config)
    target = env_naive.parse(target_config)
    diff = env_naive.diff(a=existed, b=target)
    print(diff.config)

    print("\n---Разница конфигураций с учетом no-diff секций---")
    env_no_diff = get_ct_environment_no_diff()
    existed = env_no_diff.parse(existed_config)
    target = env_no_diff.parse(target_config)
    diff = env_no_diff.diff(a=existed, b=target)
    print(diff.config)
