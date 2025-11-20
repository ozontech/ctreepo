from pytest_mock import MockerFixture

from ctreepo.ctree import CTree
from ctreepo.hasher import CTreeHasher


def test_ctree_hasher_reset_hash(
    config_tree: CTree,
    config_hash: dict[str, str],
    mocker: MockerFixture,
) -> None:
    root_old_hash = config_hash["root"]

    bgp = config_tree.node("router bgp 64512")
    assert isinstance(bgp, CTree)
    bgp_old_hash = config_hash["router bgp 64512"]

    af = config_tree.node("router bgp 64512", "address-family ipv4")
    assert isinstance(af, CTree)
    af_old_hash = config_hash["address-family ipv4"]

    net = config_tree.node("router bgp 64512", "address-family ipv4", "network 192.168.100.0 mask 255.255.255.0")
    assert isinstance(net, CTree)
    net_old_hash = config_hash["network 192.168.100.0 mask 255.255.255.0"]

    nb = config_tree.node("router bgp 64512", "neighbor 192.168.255.1 password 7 some-secret")
    assert isinstance(nb, CTree)
    nb_old_hash = config_hash["neighbor 192.168.255.1 password 7 some-secret"]

    intf = config_tree.node("interface Loopback0")
    assert isinstance(intf, CTree)
    intf_old_hash = config_hash["interface Loopback0"]

    calc_hash = mocker.spy(CTreeHasher, "calc_hash")
    reset_hash = mocker.spy(CTreeHasher, "reset_hash")
    # сначала проверим, что все хеши есть и соответствуют ожидаемым
    # да, тут дублирования calc_hash, но лишним не будет
    assert calc_hash.call_count == 0
    assert config_tree.hash == root_old_hash
    assert calc_hash.call_count == len(config_hash)

    # дальше через _hash, так как hash корня должен был просчитать все узлы
    assert intf._hash == intf_old_hash
    assert bgp._hash == bgp_old_hash
    assert af._hash == af_old_hash
    assert net._hash == net_old_hash
    assert nb._hash == nb_old_hash

    # делаем модификацию в строке
    assert reset_hash.call_count == 0
    net.line = "some new line"
    # это должно проводить к сбросу хеша как у самой ноды, так и всех нод вверх по дереву
    # обращаемся через _hash что бы не запустить расчет раньше времени
    assert config_tree._hash is None
    assert bgp._hash is None
    assert af._hash is None
    assert net._hash is None
    assert reset_hash.call_count == 4
    # но сиблинги остаются без изменений
    assert intf._hash == intf_old_hash
    assert nb._hash == nb_old_hash

    # теперь проверяем хеш корня, это запускает вычисление там, где был сброс
    assert config_tree.hash is not None
    assert calc_hash.call_count == len(config_hash) + 4
    # проверяем, что данные посчитаны
    assert bgp._hash is not None
    assert af._hash is not None
    assert net._hash is not None
    # при этом сиблинги не должны меняться
    assert intf._hash == intf_old_hash
    assert nb._hash == nb_old_hash
