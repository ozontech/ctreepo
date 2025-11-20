import importlib.util
import sys
from dataclasses import fields
from pathlib import Path
from threading import Lock

import yaml

from .platform_spec import PlatformSpec

__all__ = ("PlatformRegistry",)


class PlatformRegistry:
    _PLATFORMS: dict[str, PlatformSpec] = {}
    _LOCK: Lock = Lock()

    @classmethod
    def register(cls, platform_spec: PlatformSpec, *, rewrite: bool = False) -> None:
        if platform_spec.name in cls._PLATFORMS and not rewrite:
            raise ValueError(f"Платформа {platform_spec.name!r} уже зарегистрирована")
        cls._PLATFORMS[platform_spec.name] = platform_spec

    @classmethod
    def from_yaml(cls, path: Path) -> PlatformSpec:
        with open(path) as f:
            platform_data = yaml.safe_load(f)

        valid_fields = {f.name for f in fields(PlatformSpec)}
        extra = set(platform_data) - valid_fields
        if extra:
            raise ValueError(f"Неизвестные ключи в {path.name!r}: {extra}")

        return PlatformSpec(**platform_data)

    @classmethod
    def load_platform(
        cls,
        platform: str,
        *,
        rewrite: bool = False,
        custom_platform_yaml: Path | None = None,
    ) -> None:
        # если custom_platform_yaml None, то используем стандартные определения
        if custom_platform_yaml is None:
            path_yaml = Path(Path(__file__).parent.parent, "platforms", platform, f"{platform}_spec.yaml")
        # иначе если абсолютный путь передан, то так и оставляем
        elif custom_platform_yaml.is_absolute():
            path_yaml = custom_platform_yaml
        # в остальных случаях считаем от cwd
        else:
            path_yaml = Path(Path.cwd(), custom_platform_yaml)

        if not path_yaml.is_file():
            raise ValueError(f"нет файла {str(path_yaml)!r} для платформы {platform!r}")

        with cls._LOCK:
            if platform in cls._PLATFORMS and not rewrite:
                return
            platform_spec = cls.from_yaml(path_yaml)
            cls.register(platform_spec, rewrite=rewrite)
            cls.load_handlers(platform)

    @classmethod
    def load_handlers(cls, platform: str) -> None:
        path = Path(Path(__file__).parent.parent, "platforms", platform, "__init__.py")
        if not path.is_file():
            return
        spec = importlib.util.spec_from_file_location(f"ctreepo.platforms.{platform}", path)
        if not spec or not spec.loader:
            raise ImportError(f"Не удалось импортировать обработчики для {platform!r}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

    @classmethod
    def platforms(cls) -> list[PlatformSpec]:
        return list(cls._PLATFORMS.values())

    @classmethod
    def get_spec(
        cls,
        platform: str,
        *,
        rewrite: bool = False,
        custom_platform_yaml: Path | None = None,
    ) -> PlatformSpec:
        if platform not in cls._PLATFORMS or rewrite:
            cls.load_platform(platform, rewrite=rewrite, custom_platform_yaml=custom_platform_yaml)
        return cls._PLATFORMS[platform]
