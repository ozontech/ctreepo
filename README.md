# CTreePO - Configuration Tree Patch Overview

- [CTreePO - Configuration Tree Patch Overview](#ctreepo---configuration-tree-patch-overview)
  - [Краткое описание](#краткое-описание)
  - [Быстрый пример (00.quick-start.py)](#быстрый-пример-00quick-startpy)
  - [Преобразование в дерево (01.parsing.py)](#преобразование-в-дерево-01parsingpy)
  - [Поиск/фильтрация (02.searching.py)](#поискфильтрация-02searchingpy)
  - [Сериализация/десериализация (03.serialization.py)](#сериализациядесериализация-03serializationpy)
  - [Изменение порядка (04.reorder.py)](#изменение-порядка-04reorderpy)
  - [Разница конфигураций](#разница-конфигураций)
    - [Наивная разница (05.naive.diff.py)](#наивная-разница-05naivediffpy)
    - [Пост-обработка разницы конфигураций (06.postproc.diff.py)](#пост-обработка-разницы-конфигураций-06postprocdiffpy)
    - [Секции без вычисления разницы (07.no.diff.section.py)](#секции-без-вычисления-разницы-07nodiffsectionpy)
    - [Секции, где порядок имеет значение (08.ordered.diff.py)](#секции-где-порядок-имеет-значение-08ordereddiffpy)

## Краткое описание

Библиотека для работы с конфигурацией сетевых устройств:

- преобразование конфигурации в дерево
- поиск/фильтрация конфигурации
- вычисление разницы (diff) между двумя конфигурациями

## Быстрый пример ([00.quick-start.py](./examples/00.quick-start.py))

- Читаем текущий и целевой конфигурации из файлов
- Преобразуем конфигурации в деревья, попутно размечая тегами секции bgp и static routes
- Получаем разницу конфигураций
- Фильтруем разницу (а можно сначала фильтровать текущее/целевое деревья, а потом вычислять разницу между ними)

<details>
    <summary>Листинг (click me)</summary>

```python
In [2]: from ctreepo import CTreeEnv, Vendor

In [3]: def get_configs() -> tuple[str, str]:
   ...:     with open(file="./examples/configs/cisco-router-1.txt", mode="r") as f:
   ...:         current_config = f.read()
   ...:     with open(file="./examples/configs/cisco-router-2.txt", mode="r") as f:
   ...:         target_config = f.read()
   ...:     return current_config, target_config
   ...: 

In [4]: def get_ct_environment() -> CTreeEnv:
   ...:     tagging_rules: list[dict[str, str | list[str]]] = [
   ...:         {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
   ...:         {"regex": r"^ip route \S+", "tags": ["static"]},
   ...:     ]
   ...:     return CTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         tagging_rules=tagging_rules,
   ...:     )
   ...: 

In [5]: current_config, target_config = get_configs()

In [6]: env = get_ct_environment()

In [7]: current = env.parse(current_config)

In [8]: target = env.parse(target_config)

In [9]: diff = env.diff(current, target)

In [10]: print("\n!-- разница конфигураций --")
    ...: print(diff.config)
    ...: 

!-- разница конфигураций --
interface Tunnel2
 no ip ospf priority 0
 ip ospf priority 1
!
router bgp 64512
 no neighbor RR peer-group
 address-family ipv4
  network 10.255.255.1 mask 255.255.255.255
!
line vty 0 4
 no exec-timeout 15 0
 exec-timeout 10 0
!
line vty 5 15
 no exec-timeout 15 0
 exec-timeout 10 0
!
ip name-server 192.168.0.9
!
no ip name-server 192.168.0.3
!
no ip route 192.168.255.1 255.255.255.255 Tunnel2
!
no ip route vrf FVRF 192.66.55.44 255.255.255.255 143.31.31.2
!

In [11]: print("\n!-- разница без секций с тегами bgp и static --")
    ...: diff_no_routing = env.search(diff, exclude_tags=["bgp", "static"])
    ...: print(diff_no_routing.config)
    ...: 

!-- разница без секций с тегами bgp и static --
interface Tunnel2
 no ip ospf priority 0
 ip ospf priority 1
!
line vty 0 4
 no exec-timeout 15 0
 exec-timeout 10 0
!
line vty 5 15
 no exec-timeout 15 0
 exec-timeout 10 0
!
ip name-server 192.168.0.9
!
no ip name-server 192.168.0.3
!

In [12]: print("\n!-- разница в секции с тегом bgp --")
    ...: diff_bgp = env.search(diff, include_tags=["bgp"])
    ...: print(diff_bgp.config)
    ...: 

!-- разница в секции с тегом bgp --
router bgp 64512
 no neighbor RR peer-group
 address-family ipv4
  network 10.255.255.1 mask 255.255.255.255
!
```

</details>
<br>

## Преобразование в дерево ([01.parsing.py](./examples/01.parsing.py))

- Преобразование текстовой конфигурации в дерево на основе отступов в тексте
- Возможность размечать секции/строки тегами для последующей фильтрации
- pre-run и post-run обработка конфига и получившегося дерева, например нормализация входного конфига, обработка баннеров (cisco) и пр.

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from ctreepo import CTreeEnv, Vendor

In [2]: def get_configs() -> str:
   ...:     with open(file="./examples/configs/cisco-example-1.txt", mode="r") as f:
   ...:         config = f.read()
   ...:     return config
   ...: 

In [3]: def get_ct_environment() -> CTreeEnv:
   ...:     return CTreeEnv(vendor=Vendor.CISCO)
   ...: 

In [4]: config_config = get_configs()

In [5]: env = get_ct_environment()

In [6]: current = env.parse(config_config)

In [7]: print("\n---дерево в виде привычной конфигурации---")
   ...: print(current.config)

---дерево в виде привычной конфигурации---
service tcp-keepalives-in
!
service timestamps debug datetime msec localtime show-timezone
!
enable secret 5 2Fe034RYzgb7xbt2pYxcpA==
!
aaa group server tacacs+ TacacsGroup
 server 192.168.0.100
 server 192.168.0.101
!
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
 no ip redirects
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
 no ip redirects
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
!
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
!

In [8]: print("\n---конфигурация с маскированными секретами---")
   ...: print(current.masked_config)

---конфигурация с маскированными секретами---
service tcp-keepalives-in
!
service timestamps debug datetime msec localtime show-timezone
!
enable secret 5 ******
!
aaa group server tacacs+ TacacsGroup
 server 192.168.0.100
 server 192.168.0.101
!
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
 no ip redirects
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
 no ip redirects
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
!
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
!

In [9]: print("\n---дерево в виде патча для устройства---")
   ...: print(current.patch)

---дерево в виде патча для устройства---
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
enable secret 5 2Fe034RYzgb7xbt2pYxcpA==
aaa group server tacacs+ TacacsGroup
server 192.168.0.100
server 192.168.0.101
exit
interface Tunnel1
ip address 10.0.0.2 255.255.255.0
no ip redirects
exit
interface Tunnel2
ip address 10.1.0.2 255.255.255.0
no ip redirects
exit
interface FastEthernet0
switchport access vlan 100
no ip address
exit
router bgp 64512
neighbor 192.168.255.1 remote-as 64512
neighbor 192.168.255.1 update-source Loopback0
address-family ipv4
network 192.168.100.0 mask 255.255.255.0
neighbor 192.168.255.1 activate
exit
exit

In [10]: print("\n---патч с маскированными секретами---")
    ...: print(current.masked_patch)

---патч с маскированными секретами---
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
enable secret 5 ******
aaa group server tacacs+ TacacsGroup
server 192.168.0.100
server 192.168.0.101
exit
interface Tunnel1
ip address 10.0.0.2 255.255.255.0
no ip redirects
exit
interface Tunnel2
ip address 10.1.0.2 255.255.255.0
no ip redirects
exit
interface FastEthernet0
switchport access vlan 100
no ip address
exit
router bgp 64512
neighbor 192.168.255.1 remote-as 64512
neighbor 192.168.255.1 update-source Loopback0
address-family ipv4
network 192.168.100.0 mask 255.255.255.0
neighbor 192.168.255.1 activate
exit
exit

In [11]: print("\n---дерево в виде формальной конфигурации (аналогично formal в ios-xr)---")
    ...: print(current.formal_config)

---дерево в виде формальной конфигурации (аналогично formal в ios-xr)---
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
enable secret 5 2Fe034RYzgb7xbt2pYxcpA==
aaa group server tacacs+ TacacsGroup / server 192.168.0.100
aaa group server tacacs+ TacacsGroup / server 192.168.0.101
interface Tunnel1 / ip address 10.0.0.2 255.255.255.0
interface Tunnel1 / no ip redirects
interface Tunnel2 / ip address 10.1.0.2 255.255.255.0
interface Tunnel2 / no ip redirects
interface FastEthernet0 / switchport access vlan 100
interface FastEthernet0 / no ip address
router bgp 64512 / neighbor 192.168.255.1 remote-as 64512
router bgp 64512 / neighbor 192.168.255.1 update-source Loopback0
router bgp 64512 / address-family ipv4 / network 192.168.100.0 mask 255.255.255.0
router bgp 64512 / address-family ipv4 / neighbor 192.168.255.1 activate
```

</details>
<br>

## Поиск/фильтрация ([02.searching.py](./examples/02.searching.py))

- может быть на основе тегов, проставленных во время преобразования в дерево
- может быть по строке (regex)
- в результате получается копия дерева с которой можно работать так же, как и с оригиналом

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from ctreepo import CTreeEnv, Vendor
   ...: 
   ...: 
   ...: def get_configs() -> str:
   ...:     with open(file="./examples/configs/cisco-example-1.txt", mode="r") as f:
   ...:         config = f.read()
   ...:     return config
   ...: 
   ...: 
   ...: def get_ct_environment() -> CTreeEnv:
   ...:     tagging_rules: list[dict[str, str | list[str]]] = [
   ...:         {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
   ...:         {"regex": r"^interface (Tunnel1) / ip address .*", "tags": ["interface", "tunnel-1-ip"]},
   ...:         {"regex": r"^interface (Tunnel2) / ip address .*", "tags": ["interface", "tunnel-1-ip"]},
   ...:         {"regex": r"^interface (\S+)$", "tags": ["interface"]},
   ...:     ]
   ...:     return CTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         tagging_rules=tagging_rules,
   ...:     )
   ...: 

In [2]: config_config = get_configs()
   ...: env = get_ct_environment()
   ...: router = env.parse(config_config)

In [3]: print("\n---все вхождения 'address'---")
   ...: address = env.search(router, string="address")
   ...: print(address.config)
   ...: 

---все вхождения 'address'---
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
!
interface FastEthernet0
 no ip address
!
router bgp 64512
 address-family ipv4
!

In [4]: print("\n---все вхождения 'address' с возможными потомками---")
   ...: address_children = env.search(router, string="address", include_children=True)
   ...: print(address_children.config)
   ...: 

---все вхождения 'address' с возможными потомками---
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
!
interface FastEthernet0
 no ip address
!
router bgp 64512
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
!

In [5]: print("\n---все вхождения 'address \d{1,3}'---")
   ...: address_ip = env.search(router, string=r"address \d{1,3}")
   ...: print(address_ip.config)
   ...: 

---все вхождения 'address \d{1,3}'---
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
!

In [6]: print("\n---конфигурация по тегу 'bgp'---")
   ...: bgp = env.search(router, include_tags=["bgp"])
   ...: print(bgp.masked_config)
   ...: 

---конфигурация по тегу 'bgp'---
router bgp 64512
 neighbor 192.168.255.1 remote-as 64512
 neighbor 192.168.255.1 update-source Loopback0
 address-family ipv4
  network 192.168.100.0 mask 255.255.255.0
  neighbor 192.168.255.1 activate
!

In [7]: print("\n---все, кроме тега 'bgp'---")
   ...: no_bgp = env.search(router, exclude_tags=["bgp"])
   ...: print(no_bgp.masked_config)
   ...: 

---все, кроме тега 'bgp'---
service tcp-keepalives-in
!
service timestamps debug datetime msec localtime show-timezone
!
enable secret 5 ******
!
aaa group server tacacs+ TacacsGroup
 server 192.168.0.100
 server 192.168.0.101
!
interface Tunnel1
 ip address 10.0.0.2 255.255.255.0
 no ip redirects
!
interface Tunnel2
 ip address 10.1.0.2 255.255.255.0
 no ip redirects
!
interface FastEthernet0
 switchport access vlan 100
 no ip address
!
```

</details>
<br>

Регулярные выражения пишутся для formal вида, т.е. строки с учетом иерархии над ней. Это дает возможность расставлять теги с учетом того, в какой секции находится конфигурационная строка:

```text
interface Tunnel1 / ip address 10.0.0.2 255.255.255.0
interface Tunnel2 / ip address 10.1.0.2 255.255.255.0
```

На ip интерфейса Tunnel1 вешаем тег "tunnel-1-ip", на ip интерфейса Tunnel2 вешаем тег "tunnel-2-ip"

```python
{
    "regex": r"^interface (Tunnel1) / ip address \S+ \S+(?: )?(secondary)?$",
    "tags": ["interface", "tunnel-1-ip"],
},
{
    "regex": r"^interface (Tunnel2) / ip address \S+ \S+(?: )?(secondary)?$",
    "tags": ["interface", "tunnel-1-ip"],
},
```

Если в регулярном выражении есть неименованные группы, то их содержимое автоматически попадает в теги:

```python
{
    "regex": r"^interface (\S+)$",
    "tags": ["interface"],
},
```

Помимо тега "interface", на строку конфигурации будет так же назначен тег, равный имени самого.

Если строка конфигурации не попала не в одно из правил, тогда теги для нее берутся из вышестоящего уровня. Например если на "interface Loopback0" были назначены теги ["interface", "Loopback0"], то все строки под этой секцией так же будут иметь эти теги, если явно не перезапишутся более узкими правилами.

## Сериализация/десериализация ([03.serialization.py](./examples/03.serialization.py))

Позволяет сохранить дерево в словарь и восстановить дерево из словаря, дальше в json, например сложить и сохранить в базу/отдать через API.

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from ctreepo import CTreeEnv, Vendor
   ...: 
   ...: 
   ...: def get_configs() -> str:
   ...:     with open(file="./examples/configs/cisco-example-2.txt", mode="r") as f:
   ...:         config = f.read()
   ...:     return config
   ...: 
   ...: 
   ...: def get_ct_environment() -> CTreeEnv:
   ...:     tagging_rules: list[dict[str, str | list[str]]] = [
   ...:         {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
   ...:         {"regex": r"^interface (\S+)$", "tags": ["interface"]},
   ...:     ]
   ...:     return CTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         tagging_rules=tagging_rules,
   ...:     )
   ...: 

In [2]: config = get_configs()
   ...: env = get_ct_environment()
   ...: router_original = env.parse(config)
   ...: 

In [3]: config_dict = env.to_dict(router_original)
   ...: print("\n---сериализация---")
   ...: print(config_dict)
   ...: 

---сериализация---
{'line': '', 'tags': [], 'children': {'service tcp-keepalives-in': {'line': 'service tcp-keepalives-in', 'tags': [], 'children': {}}, 'service timestamps debug datetime msec localtime show-timezone': {'line': 'service timestamps debug datetime msec localtime show-timezone', 'tags': [], 'children': {}}, 'interface FastEthernet0': {'line': 'interface FastEthernet0', 'tags': ['interface', 'FastEthernet0'], 'children': {'switchport access vlan 100': {'line': 'switchport access vlan 100', 'tags': ['interface', 'FastEthernet0'], 'children': {}}, 'no ip address': {'line': 'no ip address', 'tags': ['interface', 'FastEthernet0'], 'children': {}}}}, 'router bgp 64512': {'line': 'router bgp 64512', 'tags': ['bgp'], 'children': {'neighbor 192.168.255.1 remote-as 64512': {'line': 'neighbor 192.168.255.1 remote-as 64512', 'tags': ['bgp'], 'children': {}}, 'neighbor 192.168.255.1 update-source Loopback0': {'line': 'neighbor 192.168.255.1 update-source Loopback0', 'tags': ['bgp'], 'children': {}}, 'address-family ipv4': {'line': 'address-family ipv4', 'tags': ['bgp'], 'children': {'network 192.168.100.0 mask 255.255.255.0': {'line': 'network 192.168.100.0 mask 255.255.255.0', 'tags': ['bgp'], 'children': {}}, 'neighbor 192.168.255.1 activate': {'line': 'neighbor 192.168.255.1 activate', 'tags': ['bgp'], 'children': {}}}}}}}}

In [4]: router_restored = env.from_dict(config_dict)
   ...: print("\n---десериализация---")
   ...: print(router_restored.patch)

---десериализация---
service tcp-keepalives-in
service timestamps debug datetime msec localtime show-timezone
interface FastEthernet0
switchport access vlan 100
no ip address
exit
router bgp 64512
neighbor 192.168.255.1 remote-as 64512
neighbor 192.168.255.1 update-source Loopback0
address-family ipv4
network 192.168.100.0 mask 255.255.255.0
neighbor 192.168.255.1 activate
exit
exit

In [5]: print("\n---равенство двух объектов---")
   ...: print(router_original == router_restored)

---равенство двух объектов---
True
```

</details>
<br>

## Изменение порядка ([04.reorder.py](./examples/04.reorder.py))

У дерева есть метод `reorder()`, который позволяет отсортировать конфигурацию в определенном порядке. Например в случаях, когда сначала нужно соблюсти порядок настройки объектов конфигурации: сначала prefix-lists, затем route-maps (которые используют созданные prefix-lists), затем назначить созданные route-maps на bgp пиров.

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from ctreepo import CTreeEnv, Vendor
   ...: 
   ...: 
   ...: def get_configs() -> str:
   ...:     with open(file="./examples/configs/cisco-example-4.txt", mode="r") as f:
   ...:         config = f.read()
   ...:     return config
   ...: 
   ...: 
   ...: def get_ct_environment() -> CTreeEnv:
   ...:     tagging_rules: list[dict[str, str | list[str]]] = [
   ...:         {"regex": r"^router bgp .* neighbor (\S+) route-map (\S+) (?:in|out)", "tags": ["rm-attach"]},
   ...:         {"regex": r"^router bgp \d+$", "tags": ["bgp"]},
   ...:         {"regex": r"^route-map (\S+) (?:permit|deny) \d+$", "tags": ["rm"]},
   ...:         {"regex": r"^ip community-list (?:standard|expanded) (\S+)", "tags": ["cl"]},
   ...:         {"regex": r"^ip prefix-list (\S+)", "tags": ["pl"]},
   ...:     ]
   ...:     return CTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         tagging_rules=tagging_rules,
   ...:     )
   ...: 

In [2]: config = get_configs()
   ...: env = get_ct_environment()
   ...: router = env.parse(config)
   ...: 

In [3]: print("\n--community-list -> prefix-list -> route-map -> bgp -> untagged--")
   ...: router.reorder(["cl", "pl", "rm", "bgp"])
   ...: print(router.config)

--community-list -> prefix-list -> route-map -> bgp -> untagged--
ip community-list standard cl_PE1 permit 64512:10001
!
ip community-list standard cl_PE2 permit 64512:10002
!
ip community-list expanded cl_VPNv4_1 permit 64512:2[0-9][0-9][0-9]1
!
ip community-list expanded cl_VPNv4_2 permit 64512:2[0-9][0-9][0-9]2
!
ip prefix-list pl_CSC seq 5 permit 10.0.0.0/24 ge 32
!
route-map rm_CSC_PE_in deny 10
 match community cl_PE1 cl_PE2
!
route-map rm_CSC_PE_in permit 20
 match ip address prefix-list pl_CSC
 set local-preference 200
!
route-map rm_RR_in permit 10
 match community cl_VPNv4_1
 set local-preference 200
!
route-map rm_RR_in permit 20
 match community cl_VPNv4_2
 set local-preference 190
!
router bgp 64512
 neighbor CSC peer-group
 neighbor CSC remote-as 12345
 neighbor RR peer-group
 neighbor RR remote-as 64512
 address-family ipv4
  neighbor CSC send-community both
  neighbor CSC route-map rm_CSC_PE_in in
  neighbor CSC send-label
 address-family vpnv4
  neighbor RR route-map rm_RR_in in
!
no platform punt-keepalive disable-kernel-core
!
no service dhcp
!
ip dhcp bootp ignore
!
no service pad
!

In [4]: print("\n--bgp -> community-list -> prefix-list -> route-map -> untagged -> rm-attach--")
   ...: wo_rm_attach = env.search(router, exclude_tags=["rm-attach"])
   ...: rm_attach = env.search(router, include_tags=["rm-attach"])
   ...: wo_rm_attach.reorder(["bgp", "cl", "pl", "rm"])
   ...: print(wo_rm_attach.config)
   ...: print(rm_attach.config)

--bgp -> community-list -> prefix-list -> route-map -> untagged -> rm-attach--
router bgp 64512
 neighbor CSC peer-group
 neighbor CSC remote-as 12345
 neighbor RR peer-group
 neighbor RR remote-as 64512
 address-family ipv4
  neighbor CSC send-community both
  neighbor CSC send-label
 address-family vpnv4
!
ip community-list standard cl_PE1 permit 64512:10001
!
ip community-list standard cl_PE2 permit 64512:10002
!
ip community-list expanded cl_VPNv4_1 permit 64512:2[0-9][0-9][0-9]1
!
ip community-list expanded cl_VPNv4_2 permit 64512:2[0-9][0-9][0-9]2
!
ip prefix-list pl_CSC seq 5 permit 10.0.0.0/24 ge 32
!
route-map rm_CSC_PE_in deny 10
 match community cl_PE1 cl_PE2
!
route-map rm_CSC_PE_in permit 20
 match ip address prefix-list pl_CSC
 set local-preference 200
!
route-map rm_RR_in permit 10
 match community cl_VPNv4_1
 set local-preference 200
!
route-map rm_RR_in permit 20
 match community cl_VPNv4_2
 set local-preference 190
!
no platform punt-keepalive disable-kernel-core
!
no service dhcp
!
ip dhcp bootp ignore
!
no service pad
!
router bgp 64512
 address-family ipv4
  neighbor CSC route-map rm_CSC_PE_in in
 address-family vpnv4
  neighbor RR route-map rm_RR_in in
!
```

</details>
<br>

## Разница конфигураций

Разница конфигураций вычисляется путем сравнения деревьев текущей и целевой конфигурации. Наивная (сырая, raw) разница получается удалением отсутствующих в целевой конфигурации команд и добавление тех, которых нет в целевой. Удаление производится путем дописывания no/undo/... (в зависимости от производителя) перед командой. Во многих случаях такой подход дает рабочий результат, а в тех случаях, когда такой вариант не работает, сырая разница модифицируется PostPrecessing правилами. Набор правил наполняется постепенно по мере эксплуатации библиотеки и нахождения случаев, которые не работают через наивный вариант с добавлением no/undo/... Разница вычисляется без учета порядка команд, т.е.

```text
some command 1
some command 2
```

будет равна

```text
some command 2
some command 1
```

Для секций, где порядок важен (ACL например) есть параграф ниже.

### Наивная разница ([05.naive.diff.py](./examples/05.naive.diff.py))

Наивная разница получается путем простого добавления no/undo/... к командам, которых быть не должно, и добавлением тех команд которых нет в исходной конфигурации. Основные моменты:

- все глобальные "undo-команды" помещаются в конец. Сделано с той целью, что бы удаление (а не изменение) объектов было в самом конце, и что бы, по возможности, избежать проблем зависимостей использования (например когда prefix-list удаляется раньше, чем он перестает использоваться). Данное поведение можно отключить ключом `reorder_root` метода `diff()`.
- ко всем глобальным "undo-командам" добавляется тег `post`. Сделано для того, что бы можно было отфильтровать удаление объектов, например если не нужно проводить очистку конфигураций (или наоборот, провести только очистку) от неописанных в целевой конфигурации настроек.

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from ctreepo import CTreeEnv, Vendor
   ...: 
   ...: 
   ...: def get_configs() -> tuple[str, str]:
   ...:     with open(file="./examples/configs/cisco-naive-diff-target.txt", mode="r") as f:
   ...:         target = f.read()
   ...:     with open(file="./examples/configs/cisco-naive-diff-existed.txt", mode="r") as f:
   ...:         existed = f.read()
   ...: 
   ...:     return existed, target
   ...: 
   ...: 
   ...: def get_ct_environment() -> CTreeEnv:
   ...:     return CTreeEnv(vendor=Vendor.CISCO)
   ...: 

In [2]: existed_config, target_config = get_configs()
   ...: env = get_ct_environment()
   ...: existed = env.parse(existed_config)
   ...: target = env.parse(target_config)

In [3]: print("\n---Наивная разница конфигураций---")
   ...: diff = env.diff(a=existed, b=target)
   ...: print(diff.config)

---Наивная разница конфигураций---
interface FastEthernet0
 no switchport access vlan 100
 description User
 switchport access vlan 123
!
router bgp 64512
 address-family ipv4
  no network 192.168.100.0 mask 255.255.255.0
  network 192.168.200.1 mask 255.255.255.0
!
line vty 0 4
 transport input all
!
no router ospf 1
!

In [4]: print("\n---Наивная разница конфигураций: без очистки---")
   ...: diff_without_clear = env.search(diff, exclude_tags=["post"])
   ...: print(diff_without_clear.config)
   ...: 

---Наивная разница конфигураций: без очистки---
interface FastEthernet0
 no switchport access vlan 100
 description User
 switchport access vlan 123
!
router bgp 64512
 address-family ipv4
  no network 192.168.100.0 mask 255.255.255.0
  network 192.168.200.1 mask 255.255.255.0
!
line vty 0 4
 transport input all
!

In [5]: print("\n---Наивная разница конфигураций: только очистка---")
   ...: diff_clear = env.search(diff, include_tags=["post"])
   ...: print(diff_clear.config)
   ...: 

---Наивная разница конфигураций: только очистка---
no router ospf 1
!
```

</details>
<br>

### Пост-обработка разницы конфигураций ([06.postproc.diff.py](./examples/06.postproc.diff.py))

Когда наивный вариант не работает, разницу можно обработать с помощью правил и придать ей нужный вид. Правил пост-обработки может быть несколько, они независимы друг от друга и через декоратор `register_rule` помещаются в общий список правил.

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: import re
   ...: 
   ...: from ctreepo import CTreeEnv, Vendor
   ...: from ctreepo.generic import GenericCTree
   ...: from ctreepo.postproc import CTreePostProc, register_rule

In [2]: @register_rule(Vendor.CISCO)
   ...: class CiscoPostProcBGP(CTreePostProc):
   ...:     @classmethod
   ...:     def _delete_nodes(cls, ct: CTree, regex: str) -> None:
   ...:         nodes_to_delete: list[CTree] = []
   ...:         for node in ct.children.values():
   ...:             if len(node.children) != 0:
   ...:                 cls._delete_nodes(node, regex)
   ...:                 if len(node.children) == 0:
   ...:                     nodes_to_delete.append(node)
   ...:             else:
   ...:                 if re.match(regex, node.line):
   ...:                     nodes_to_delete.append(node)
   ...:         for node in nodes_to_delete:
   ...:             node.delete()
   ...:
   ...:     @classmethod
   ...:     def process(cls, ct: CTree) -> None:
   ...:         bgp_nodes = [node for node in ct.children.values() if node.line.startswith("router bgp ")]
   ...:         if len(bgp_nodes) != 1:
   ...:             return
   ...:         bgp = bgp_nodes[0]
   ...: 
   ...:         bgp_global = {node.line: node for node in bgp.children.values() if len(node.children) == 0}
   ...:         bgp_af = {node.line: node for node in bgp.children.values() if len(node.children) != 0}
   ...:         bgp.children = bgp_global | bgp_af
   ...: 
   ...:         regexes_to_delete = set()
   ...:         groups_to_delete = set()
   ...:         peers_to_delete = set()
   ...:         for node in bgp.children.values():
   ...:             if node.line.startswith("no neighbor ") and node.line.endswith(" peer-group"):
   ...:                 _, _, group, _ = node.line.split()
   ...:                 groups_to_delete.add(group)
   ...:         for node in bgp.children.values():
   ...:             if (
   ...:                 m := re.fullmatch(
   ...:                     pattern=rf"no neighbor (?P<peer>\S+) peer-group (?:{'|'.join(groups_to_delete)})",
   ...:                     string=node.line,
   ...:                 )
   ...:             ) is not None:
   ...:                 peers_to_delete.add(m.group("peer"))
   ...: 
   ...:         if len(groups_to_delete) != 0:
   ...:             regexes_to_delete.add(rf"no neighbor (?:{'|'.join(groups_to_delete)}) (?!peer-group)")
   ...:         if len(peers_to_delete) != 0:
   ...:             regexes_to_delete.add(rf"no neighbor (?:{'|'.join(peers_to_delete)})")
   ...: 
   ...:         if len(regexes_to_delete) != 0:
   ...:             cls._delete_nodes(bgp, "|".join(regexes_to_delete))

In [3]: def get_configs() -> tuple[str, str]:
   ...:     with open(file="./examples/configs/cisco-postproc-diff-target.txt", mode="r") as f:
   ...:         target = f.read()
   ...:     with open(file="./examples/configs/cisco-postproc-diff-existed.txt", mode="r") as f:
   ...:         existed = f.read()
   ...: 
   ...:     return existed, target
   ...: 

In [4]: def get_ct_environment_naive() -> CTreeEnv:
   ...:     return CTreeEnv(vendor=Vendor.CISCO, post_proc_rules=[])
   ...: 
   ...: 
   ...: def get_ct_environment_postproc() -> CTreeEnv:
   ...:     # декоратор register_rule добавляет правило в общий список и можно тут не
   ...:     # переопределять его через аргумент post_proc_rules, но если необходимо 
   ...:     # протестировать только какие-то определенные правила, тогда явно задаем их 
   ...:     # или указываем пустой список, что бы получить наивную разницу без обработки
   ...:     return CTreeEnv(vendor=Vendor.CISCO, post_proc_rules=[CiscoPostProcBGP])
   ...: 

In [5]: existed_config, target_config = get_configs()

In [6]: print("\n---Наивная разница конфигураций---")
   ...: env_naive = get_ct_environment_naive()
   ...: existed = env_naive.parse(existed_config)
   ...: target = env_naive.parse(target_config)
   ...: diff = env_naive.diff(a=existed, b=target)
   ...: print(diff.config)
   ...: 

---Наивная разница конфигураций---
router bgp 64512
 no neighbor RR peer-group
 no neighbor RR remote-as 64512
 no neighbor RR ebgp-multihop 255
 no neighbor RR update-source Loopback0
 no neighbor 192.168.255.2 peer-group RR
 no neighbor 192.168.255.3 peer-group RR
 address-family ipv4
  no neighbor RR send-community both
  no neighbor RR advertisement-interval 0
  no neighbor 192.168.255.2 activate
  no neighbor 192.168.255.3 activate
  neighbor 192.168.255.1 send-community both
!

In [7]: print("\n---Обработанная разница конфигураций---")
   ...: env_postproc = get_ct_environment_postproc()
   ...: existed = env_postproc.parse(existed_config)
   ...: target = env_postproc.parse(target_config)
   ...: diff = env_postproc.diff(a=existed, b=target)
   ...: print(diff.config)
   ...: 

---Обработанная разница конфигураций---
router bgp 64512
 no neighbor RR peer-group
 address-family ipv4
  neighbor 192.168.255.1 send-community both
!
```

</details>
<br>

### Секции без вычисления разницы ([07.no.diff.section.py](./examples/07.no.diff.section.py))

Некоторые секции конфигураций нужно настраивать полностью, даже если нужно поменять какой-то один параметр. Это могут быть RPL секции в IOS-XR или XPL в Huawei (смысл один и тот же: при входе в секцию, нужно применить полные её настройки). Регулярное выражение, описывающее такие секции может быть передано в качестве аргумента при создании окружения, в этом случае для этих секций в качестве разницы конфигураций будет применяться целевая конфигурация целиком, а не разница между текущей и целевой.

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from ctreepo import CTreeEnv, Vendor

In [2]: def get_configs() -> tuple[str, str]:
   ...:     with open(file="./examples/configs/cisco-no-diff-section-target.txt", mode="r") as f:
   ...:         target = f.read()
   ...:     with open(file="./examples/configs/cisco-no-diff-section-existed.txt", mode="r") as f:
   ...:         existed = f.read()
   ...: 
   ...:     return existed, target
   ...: 

In [3]: def get_ct_environment_naive() -> CTreeEnv:
   ...:     return CTreeEnv(vendor=Vendor.CISCO)
   ...: 

In [4]: def get_ct_environment_no_diff() -> CTreeEnv:
   ...:     return CTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         no_diff_sections=[
   ...:             r"prefix-set \S+",
   ...:             r"route-policy \S+",
   ...:         ],
   ...:     )
   ...: 

In [5]: existed_config, target_config = get_configs()

In [6]: print("\n---Наивная разница конфигураций---")
   ...: env_naive = get_ct_environment_naive()
   ...: existed = env_naive.parse(existed_config)
   ...: target = env_naive.parse(target_config)
   ...: diff = env_naive.diff(a=existed, b=target)
   ...: print(diff.config)

---Наивная разница конфигураций---
interface BVI123
 no description User-OLD
 description User-NEW
!
prefix-set ps-google
 no 8.8.8.8/32
 8.8.8.8/32,
 8.8.4.4/32
!
route-policy rp-google
 elseif destination in ps-some-networks then
  drop
!

In [7]: print("\n---Разница конфигураций с учетом no-diff секций---")
   ...: env_no_diff = get_ct_environment_no_diff()
   ...: existed = env_no_diff.parse(existed_config)
   ...: target = env_no_diff.parse(target_config)
   ...: diff = env_no_diff.diff(a=existed, b=target)
   ...: print(diff.config)

---Разница конфигураций с учетом no-diff секций---
interface BVI123
 no description User-OLD
 description User-NEW
!
prefix-set ps-google
 8.8.8.8/32,
 8.8.4.4/32
!
route-policy rp-google
 if destination in ps-google then
  drop
 elseif destination in ps-some-networks then
  drop
 else
  pass
 endif
!
```

</details>
<br>

### Секции, где порядок имеет значение ([08.ordered.diff.py](./examples/08.ordered.diff.py))

В некоторых секциях (например acl) порядок записей имеет значение. Регулярное выражение, описывающее такие секции может быть передано при создании окружения. В этом случае библиотека будет стараться привести текущую конфигурацию к целевой с учетом порядка команд. Но несмотря на это, к таким секциям нужно относиться с особой внимательностью и, по возможности, избегать их. Упомянутые выше ACL могут иметь entry-number перед правилом, что избавляет от необходимости проверки порядка, так как не важно в каком порядке будут применены команды, за счет наличия entry-number в ACE, правила будут установлены в нужное место (отдельно не забываем про возможности делать re-sequence, эту команду можно, например добавить через post-processing при модификации acl, тогда будет всегда консистентный шаг между ACE).

<details>
    <summary>Листинг (click me)</summary>

```python
In [1]: from ctreepo import CTreeEnv, Vendor

In [2]: def get_configs() -> tuple[str, str]:
   ...:     with open(file="./examples/configs/cisco-ordered-diff-target.txt", mode="r") as f:
   ...:         target = f.read()
   ...:     with open(file="./examples/configs/cisco-ordered-diff-existed.txt", mode="r") as f:
   ...:         existed = f.read()
   ...: 
   ...:     return existed, target
   ...: 

In [3]: def get_ct_environment_naive() -> CTreeEnv:
   ...:     return CTreeEnv(vendor=Vendor.CISCO)
   ...: 
   ...: 
   ...: def get_ct_environment_ordered() -> CTreeEnv:
   ...:     return CTreeEnv(
   ...:         vendor=Vendor.CISCO,
   ...:         ordered_sections=[
   ...:             r"ip access-list standard \S+",
   ...:         ],
   ...:     )
   ...: 

In [4]: existed_config, target_config = get_configs()

In [5]: print("\n---Наивная разница конфигураций---")
   ...: env_naive = get_ct_environment_naive()
   ...: existed = env_naive.parse(existed_config)
   ...: target = env_naive.parse(target_config)
   ...: diff = env_naive.diff(a=existed, b=target)
   ...: print(diff.config)

---Наивная разница конфигураций---
ip access-list standard acl_TEST_STD
 permit 8.8.4.4
!
ip access-list extended act_TEST_EXT
 15 permit ip host 8.8.4.4 any
!

In [6]: print("\n---Разница конфигураций с учетом секций со значимым порядком---")
   ...: env_ordered = get_ct_environment_ordered()
   ...: existed = env_ordered.parse(existed_config)
   ...: target = env_ordered.parse(target_config)
   ...: diff = env_ordered.diff(a=existed, b=target)
   ...: print(diff.config)

---Разница конфигураций с учетом секций со значимым порядком---
ip access-list standard acl_TEST_STD
 no deny   any
 permit 8.8.4.4
 deny   any
!
ip access-list extended act_TEST_EXT
 15 permit ip host 8.8.4.4 any
!
```

</details>
<br>
