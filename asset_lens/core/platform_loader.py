"""
Platform configuration loader.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Optional, Self


@dataclass
class PlatformConfig:
    """Platform configuration"""

    id: str
    name: str
    field: str
    type: str
    description: str = ""


@dataclass
class PlatformTypeConfig:
    """Platform type configuration"""

    id: str
    name: str


class PlatformLoader:
    """Load and manage platform configurations"""

    _instance: Optional["PlatformLoader"] = None
    _platforms: ClassVar[dict[str, PlatformConfig]] = {}
    _platform_types: ClassVar[dict[str, str]] = {}
    _loaded: bool = False

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance  # type: ignore[return-value]

    @classmethod
    def load(cls, config_path: Path | None = None, data_mode: str | None = None) -> None:
        """Load platform configuration from JSON file"""
        if cls._loaded and config_path is None:
            return

        if config_path is None:
            if data_mode is None:
                data_mode = "sample"

            config_dir = Path(__file__).parent.parent.parent / "config"

            if data_mode == "real":
                config_path = config_dir / "platforms.json"
            else:
                config_path = config_dir / "platforms.json.example"

        if not config_path.exists():
            cls._load_defaults()
            cls._loaded = True
            return

        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        cls._platforms = {}
        for platform_data in data.get("platforms", []):
            platform = PlatformConfig(
                id=platform_data["id"],
                name=platform_data["name"],
                field=platform_data["field"],
                type=platform_data["type"],
                description=platform_data.get("description", ""),
            )
            cls._platforms[platform.id] = platform

        cls._platform_types = data.get("platform_types", {})
        cls._loaded = True

    @classmethod
    def _load_defaults(cls) -> None:
        """Load default platform configuration"""
        default_platforms = [
            PlatformConfig("platform_a", "平台A", "platform_a_amount", "third_party", "第三方平台A"),
            PlatformConfig("platform_b", "平台B", "platform_b_amount", "third_party", "第三方平台B"),
            PlatformConfig("securities_a", "券商A", "securities_a_amount", "securities", "证券账户A"),
            PlatformConfig("securities_b", "券商B", "securities_b_amount", "securities", "证券账户B"),
            PlatformConfig("bank_a", "银行A", "bank_a_amount", "bank", "银行账户A"),
            PlatformConfig("bank_b", "银行B", "bank_b_amount", "bank", "银行账户B"),
            PlatformConfig("bank_c", "银行C", "bank_c_amount", "bank", "银行账户C"),
        ]

        cls._platforms = {p.id: p for p in default_platforms}
        cls._platform_types = {
            "third_party": "第三方平台",
            "bank": "银行",
            "securities": "证券",
        }

    @classmethod
    def get_platform(cls, platform_id: str, data_mode: str | None = None) -> PlatformConfig | None:
        """Get platform by ID"""
        if not cls._loaded:
            cls.load(data_mode=data_mode)
        return cls._platforms.get(platform_id)

    @classmethod
    def get_all_platforms(cls, data_mode: str | None = None) -> list[PlatformConfig]:
        """Get all platforms"""
        if not cls._loaded:
            cls.load(data_mode=data_mode)
        return list(cls._platforms.values())

    @classmethod
    def get_platforms_by_type(cls, platform_type: str) -> list[PlatformConfig]:
        """Get platforms by type"""
        if not cls._loaded:
            cls.load()
        return [p for p in cls._platforms.values() if p.type == platform_type]

    @classmethod
    def get_platform_name(cls, platform_id: str) -> str:
        """Get platform display name"""
        platform = cls.get_platform(platform_id)
        return platform.name if platform else platform_id

    @classmethod
    def get_field_name(cls, platform_id: str) -> str:
        """Get platform field name"""
        platform = cls.get_platform(platform_id)
        return platform.field if platform else f"{platform_id}_amount"

    @classmethod
    def get_platform_type_name(cls, platform_type: str) -> str:
        """Get platform type display name"""
        if not cls._loaded:
            cls.load()
        return cls._platform_types.get(platform_type, platform_type)

    @classmethod
    def get_all_field_names(cls) -> list[str]:
        """Get all field names"""
        if not cls._loaded:
            cls.load()
        return [p.field for p in cls._platforms.values()]

    @classmethod
    def get_field_to_name_mapping(cls) -> dict[str, str]:
        """Get mapping from field name to display name"""
        if not cls._loaded:
            cls.load()
        return {p.field: p.name for p in cls._platforms.values()}

    @classmethod
    def get_id_to_field_mapping(cls) -> dict[str, str]:
        """Get mapping from platform ID to field name"""
        if not cls._loaded:
            cls.load()
        return {p.id: p.field for p in cls._platforms.values()}

    @classmethod
    def reset(cls) -> None:
        """Reset the loader (useful for testing)"""
        cls._loaded = False
        cls._platforms = {}
        cls._platform_types = {}
