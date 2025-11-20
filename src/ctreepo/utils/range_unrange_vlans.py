from collections.abc import Iterator

__all__ = (
    "unrange_huawei_vlans",
    "range_huawei_vlans",
)


def unrange_huawei_vlans(line: str) -> Iterator[int]:
    vlans = line.split()
    pointer = 0
    while pointer < len(vlans):
        start = vlans[pointer]
        end = vlans[pointer]
        pointer += 1
        if pointer < len(vlans) and vlans[pointer] == "to":
            end = vlans[pointer + 1]
            pointer += 2
        yield from range(int(start), int(end) + 1)


def range_huawei_vlans(vlans: list[int]) -> str:
    result: list[str] = []
    pointer = 0
    while pointer < len(vlans):
        if pointer < len(vlans) - 1 and vlans[pointer] + 1 == vlans[pointer + 1]:
            if len(result) == 0 or result[-1] != "to":
                result.append(str(vlans[pointer]))
                result.append("to")
        else:
            result.append(str(vlans[pointer]))
        pointer += 1

    return " ".join(result)
