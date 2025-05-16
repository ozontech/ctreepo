from ctreepo import CTreeEnv, Vendor


def get_configs() -> tuple[str, str]:
    with open(file="./examples/configs/cisco-ordered-diff-target.txt", mode="r") as f:
        target = f.read()
    with open(file="./examples/configs/cisco-ordered-diff-existed.txt", mode="r") as f:
        existed = f.read()

    return existed, target


def get_ct_environment_naive() -> CTreeEnv:
    return CTreeEnv(vendor=Vendor.CISCO)


def get_ct_environment_ordered() -> CTreeEnv:
    return CTreeEnv(
        vendor=Vendor.CISCO,
        ordered_sections=[
            r"ip access-list standard \S+",
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

    print("\n---Разница конфигураций с учетом секций со значимым порядком---")
    env_ordered = get_ct_environment_ordered()
    existed = env_ordered.parse(existed_config)
    target = env_ordered.parse(target_config)
    diff = env_ordered.diff(a=existed, b=target)
    print(diff.config)
