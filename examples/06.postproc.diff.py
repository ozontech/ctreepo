import re

from ctreepo import CTree, CTreeEnv, Vendor
from ctreepo.postproc import CTreePostProc, register_rule


@register_rule(Vendor.CISCO)
class CiscoPostProcBGP(CTreePostProc):
    @classmethod
    def _delete_nodes(cls, ct: CTree, regex: str) -> None:
        """Рекурсивное удаление узлов по переданному паттерну."""
        nodes_to_delete: list[CTree] = []
        for node in ct.children.values():
            if len(node.children) != 0:
                cls._delete_nodes(node, regex)
                # если у нас была секция, и в этой секции ничего не осталось, то и саму секцию удаляем,
                # иначе будут мусорные строки (типа входим к секцию, но ничего не делаем там)
                if len(node.children) == 0:
                    nodes_to_delete.append(node)
            else:
                if re.match(regex, node.line):
                    nodes_to_delete.append(node)
        for node in nodes_to_delete:
            node.delete()

    @classmethod
    def process(cls, ct: CTree) -> None:
        """Пост-обработка секции bgp для Cisco.

        - если есть команда "no neighbor <GROUP-NAME> peer-group", значит группы в целевой
            конфигурации вообще нет, и нужно все команды "no neighbor <GROUP-NAME> <some-options>"
            удалить, так же как и назначение пиров в эту группу "neighbor x.x.x.x peer-group <GROUP-NAME>",
            а оставить только одну "no neighbor <GROUP-NAME> peer-group", устройство остальное само вычистит

        !группы, определенные в af не обрабатываем, так как это пример использования

        Args:
            ct (CTree): дерево, для модификации
        """
        # найдем секцию bgp, если она есть
        bgp_nodes = [node for node in ct.children.values() if node.line.startswith("router bgp ")]
        if len(bgp_nodes) != 1:
            return
        bgp = bgp_nodes[0]

        # пересортируем секцию bgp, что бы все глобальные bgp команды шли перед настройками af
        # это не относится к задаче, но неизвестно как формировалась целевая конфигурация, поэтому лучше сделать
        bgp_global = {node.line: node for node in bgp.children.values() if len(node.children) == 0}
        bgp_af = {node.line: node for node in bgp.children.values() if len(node.children) != 0}
        bgp.children = bgp_global | bgp_af

        # теперь нужно сформировать признаки, как найти команды, которые будем удалять из diff'а
        # в задаче это имя удаляем peer-group, поэтому пройдемся по всем линиям и если есть
        # `no neighbor <GROUP-NAME> peer-group`, значит мы удаляем эту группу целиком, а не просто
        # меняем какой-либо параметр у нее
        regexes_to_delete = set()
        groups_to_delete = set()
        peers_to_delete = set()
        for node in bgp.children.values():
            # можно через re поймать строку, но выбрал такой вариант
            if node.line.startswith("no neighbor ") and node.line.endswith(" peer-group"):
                # no neighbor <GROUP-NAME> peer-group
                _, _, group, _ = node.line.split()
                groups_to_delete.add(group)
        for node in bgp.children.values():
            if (
                m := re.fullmatch(
                    pattern=rf"no neighbor (?P<peer>\S+) peer-group (?:{'|'.join(groups_to_delete)})",
                    string=node.line,
                )
            ) is not None:
                peers_to_delete.add(m.group("peer"))

        if len(groups_to_delete) != 0:
            regexes_to_delete.add(rf"no neighbor (?:{'|'.join(groups_to_delete)}) (?!peer-group)")
        if len(peers_to_delete) != 0:
            regexes_to_delete.add(rf"no neighbor (?:{'|'.join(peers_to_delete)})")

        # после получения признаков, удаляем ноды, которые им соответствуют
        if len(regexes_to_delete) != 0:
            cls._delete_nodes(bgp, "|".join(regexes_to_delete))


def get_configs() -> tuple[str, str]:
    with open(file="./examples/configs/cisco-postproc-diff-target.txt", mode="r") as f:
        target = f.read()
    with open(file="./examples/configs/cisco-postproc-diff-existed.txt", mode="r") as f:
        existed = f.read()

    return existed, target


def get_ct_environment_naive() -> CTreeEnv:
    return CTreeEnv(vendor=Vendor.CISCO, post_proc_rules=[])


def get_ct_environment_postproc() -> CTreeEnv:
    # декоратор register_rule добавляет правило в общий список и можно тут не
    # переопределять его через аргумент post_proc_rules, но если необходимо
    # протестировать только какие-то определенные правила, тогда явно задаем их
    # или указываем пустой список, что бы получить наивную разницу без обработки
    return CTreeEnv(vendor=Vendor.CISCO, post_proc_rules=[CiscoPostProcBGP])


if __name__ == "__main__":
    existed_config, target_config = get_configs()

    print("\n---Наивная разница конфигураций---")
    env_naive = get_ct_environment_naive()
    existed = env_naive.parse(existed_config)
    target = env_naive.parse(target_config)
    diff = env_naive.diff(a=existed, b=target)
    print(diff.config)

    print("\n---Обработанная разница конфигураций---")
    env_postproc = get_ct_environment_postproc()
    existed = env_postproc.parse(existed_config)
    target = env_postproc.parse(target_config)
    diff = env_postproc.diff(a=existed, b=target)
    print(diff.config)
