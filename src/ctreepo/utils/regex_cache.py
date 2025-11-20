import re

__all__ = (
    "REGEX_CHARS",
    "CTreeRegexCache",
)


REGEX_CHARS = r"\(\?P<(\S+?)>(\S+?)\)"


# тут для ускорения сделал отдельный кеш паттернов
class CTreeRegexCache:
    PATTERN_CACHE: dict[str, re.Pattern[str]] = {
        REGEX_CHARS: re.compile(REGEX_CHARS),
    }

    @classmethod
    def get_pattern(cls, line: str) -> re.Pattern[str]:
        if line not in cls.PATTERN_CACHE:
            cls.PATTERN_CACHE[line] = re.compile(line)
        return cls.PATTERN_CACHE[line]
