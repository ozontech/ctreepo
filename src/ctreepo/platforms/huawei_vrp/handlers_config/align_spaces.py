from ctreepo.spec.config_handler_registry import PreConfigHandlerRegistry

__all__ = ("align_spaces",)


@PreConfigHandlerRegistry.register("huawei_vrp")
def align_spaces(config: str) -> str:
    # у huawei в некоторых устройствах/версиях некоторые глобальные команды
    # выглядят так, как будто они находятся внутри секции, это ломает парсинг.
    # например пробел(ы) перед ntp-service, хотя это глобальный конфиг
    # #
    #  ntp-service server disable
    #  ntp-service source-interface LoopBack0
    #  ntp-service unicast-server 1.2.3.4
    # #
    # или пробел перед http
    # #
    #  http timeout 60
    #  http secure-server ssl-policy default_policy
    #  http server enable
    # #
    # поэтому удаляем пробел из конфигурации перед анализом

    result = []
    section = False
    for line in config.splitlines():
        if len(line) == 0:
            continue
        if line == "#":
            section = False
            space_count = 0
        elif not line.startswith(" "):
            section = True
        if line.startswith(" ") and not section:
            if space_count == 0:
                space_count = len(line) - len(line.lstrip())
            result.append(line.removeprefix(" " * space_count))
        else:
            result.append(line)
    return "\n".join(result)
