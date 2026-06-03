"""
JSON file cache utility.
JSON 文件缓存工具 - 统一的 JSON 文件读写入口

提供带错误处理的 JSON 文件读写操作，避免在多个文件中
重复实现 json.load/json.dump + open + 错误处理 的模式。
"""

import json
import logging
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


def read_json_cache(file_path: Path) -> dict[str, Any] | None:
    """从 JSON 文件读取缓存数据

    Args:
        file_path: 缓存文件路径

    Returns:
        解析后的字典数据，文件不存在或解析失败返回 None
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, encoding="utf-8") as f:
            return cast(dict[str, Any], json.load(f))
    except json.JSONDecodeError as e:
        logger.debug(f"缓存文件 JSON 解析失败 {file_path}: {e}")
        return None
    except OSError as e:
        logger.debug(f"读取缓存文件 IO 错误 {file_path}: {e}")
        return None
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.debug(f"读取缓存文件失败 {file_path}: {e}")
        return None


def write_json_cache(file_path: Path, data: dict[str, Any], ensure_dir: bool = True) -> bool:
    """将数据写入 JSON 缓存文件

    Args:
        file_path: 缓存文件路径
        data: 要写入的数据
        ensure_dir: 是否自动创建父目录

    Returns:
        写入是否成功
    """
    try:
        if ensure_dir:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return True
    except OSError as e:
        logger.warning(f"写入缓存文件 IO 错误 {file_path}: {e}")
        return False
    except (TypeError, ValueError) as e:
        logger.warning(f"缓存数据序列化失败 {file_path}: {e}")
        return False
    except (OSError, TypeError) as e:
        logger.warning(f"写入缓存文件失败 {file_path}: {e}")
        return False
