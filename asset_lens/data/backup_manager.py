"""
Auto backup system for asset-lens.
自动备份系统 - 定时备份重要数据

功能:
1. 数据自动备份
2. 备份文件管理
3. 备份恢复
4. 备份清理
"""

import json
import logging
import shutil
import tarfile
from datetime import datetime, timedelta
from typing import Any

from ..config import config

logger = logging.getLogger(__name__)


class BackupManager:
    """备份管理器"""

    def __init__(self):
        self.backup_path = config.cache_path / "backups"
        self.backup_path.mkdir(parents=True, exist_ok=True)
        self.config_file = self.backup_path / "backup_config.json"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """加载备份配置"""
        default_config = {
            "auto_backup_enabled": True,
            "backup_interval_days": 1,
            "max_backup_count": 10,
            "backup_directories": [
                "data",
                "cache",
                "config",
            ],
            "exclude_patterns": [
                "*.pyc",
                "__pycache__",
                "*.log",
                "*.tmp",
            ],
            "last_backup_time": None,
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except (ValueError, KeyError, TypeError):
                pass

        return default_config

    def _save_config(self) -> None:
        """保存备份配置"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def create_backup(
        self,
        backup_name: str | None = None,
        include_data: bool = True,
        include_cache: bool = True,
        include_config: bool = True,
    ) -> dict[str, Any]:
        """
        创建备份

        Args:
            backup_name: 备份名称
            include_data: 是否包含数据目录
            include_cache: 是否包含缓存目录
            include_config: 是否包含配置目录

        Returns:
            备份结果
        """
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_file = self.backup_path / f"{backup_name}.tar.gz"

        result: dict[str, Any] = {
            "success": False,
            "backup_name": backup_name,
            "backup_file": str(backup_file),
            "backup_size": 0,
            "file_count": 0,
            "directories": [],
            "errors": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            file_count = 0
            directories = []

            with tarfile.open(backup_file, "w:gz") as tar:
                if include_data:
                    data_dir = config.project_root / "data"
                    if data_dir.exists():
                        tar.add(data_dir, arcname="data")
                        file_count += sum(1 for _ in data_dir.rglob("*") if _.is_file())
                        directories.append("data")

                if include_cache:
                    cache_dir = config.cache_path
                    if cache_dir.exists():
                        tar.add(cache_dir, arcname="cache")
                        file_count += sum(1 for _ in cache_dir.rglob("*") if _.is_file())
                        directories.append("cache")

                if include_config:
                    config_dir = config.config_path
                    if config_dir.exists():
                        tar.add(config_dir, arcname="config")
                        file_count += sum(1 for _ in config_dir.rglob("*") if _.is_file())
                        directories.append("config")

            result["success"] = True
            result["backup_size"] = backup_file.stat().st_size
            result["file_count"] = file_count
            result["directories"] = directories

            self.config["last_backup_time"] = result["created_at"]
            self._save_config()

            self._cleanup_old_backups()

        except Exception as e:
            result["errors"].append(str(e))

        return result

    def restore_backup(
        self,
        backup_name: str,
        restore_data: bool = True,
        restore_cache: bool = True,
        restore_config: bool = True,
    ) -> dict[str, Any]:
        """
        恢复备份

        Args:
            backup_name: 备份名称
            restore_data: 是否恢复数据目录
            restore_cache: 是否恢复缓存目录
            restore_config: 是否恢复配置目录

        Returns:
            恢复结果
        """
        backup_file = self.backup_path / f"{backup_name}.tar.gz"

        result: dict[str, Any] = {
            "success": False,
            "backup_name": backup_name,
            "restored_directories": [],
            "errors": [],
            "restored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if not backup_file.exists():
            result["errors"].append(f"备份文件不存在: {backup_file}")
            return result

        try:
            restore_dir = self.backup_path / f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            restore_dir.mkdir(parents=True, exist_ok=True)

            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(restore_dir)

            if restore_data:
                src_data = restore_dir / "data"
                dst_data = config.project_root / "data"
                if src_data.exists():
                    if dst_data.exists():
                        shutil.rmtree(dst_data)
                    shutil.move(str(src_data), str(dst_data))
                    result["restored_directories"].append("data")

            if restore_cache:
                src_cache = restore_dir / "cache"
                dst_cache = config.cache_path
                if src_cache.exists():
                    if dst_cache.exists():
                        shutil.rmtree(dst_cache)
                    shutil.move(str(src_cache), str(dst_cache))
                    result["restored_directories"].append("cache")

            if restore_config:
                src_config = restore_dir / "config"
                dst_config = config.config_path
                if src_config.exists():
                    if dst_config.exists():
                        shutil.rmtree(dst_config)
                    shutil.move(str(src_config), str(dst_config))
                    result["restored_directories"].append("config")

            shutil.rmtree(restore_dir)

            result["success"] = True

        except Exception as e:
            result["errors"].append(str(e))

        return result

    def list_backups(self) -> list[dict[str, Any]]:
        """
        列出所有备份

        Returns:
            备份列表
        """
        backups = []

        for backup_file in sorted(self.backup_path.glob("backup_*.tar.gz"), reverse=True):
            try:
                stat = backup_file.stat()
                backups.append(
                    {
                        "name": backup_file.stem,
                        "file": str(backup_file),
                        "size": stat.st_size,
                        "size_mb": stat.st_size / (1024 * 1024),
                        "created_at": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
            except Exception as e:
                logger.debug(f"忽略异常: {e}")
                continue

        return backups

    def delete_backup(self, backup_name: str) -> dict[str, Any]:
        """
        删除备份

        Args:
            backup_name: 备份名称

        Returns:
            删除结果
        """
        backup_file = self.backup_path / f"{backup_name}.tar.gz"

        result = {
            "success": False,
            "backup_name": backup_name,
            "deleted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if backup_file.exists():
            try:
                backup_file.unlink()
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
        else:
            result["error"] = "备份文件不存在"

        return result

    def _cleanup_old_backups(self) -> int:
        """
        清理旧备份

        Returns:
            删除的备份数量
        """
        max_count = self.config.get("max_backup_count", 10)
        backups = sorted(self.backup_path.glob("backup_*.tar.gz"))

        deleted_count = 0
        while len(backups) > max_count:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
                deleted_count += 1
            except Exception as e:
                logger.debug(f"忽略异常: {e}")
                continue

        return deleted_count

    def get_backup_status(self) -> dict[str, Any]:
        """
        获取备份状态

        Returns:
            备份状态
        """
        backups = self.list_backups()

        total_size = sum(b["size"] for b in backups)

        return {
            "auto_backup_enabled": self.config.get("auto_backup_enabled", True),
            "backup_interval_days": self.config.get("backup_interval_days", 1),
            "max_backup_count": self.config.get("max_backup_count", 10),
            "current_backup_count": len(backups),
            "total_backup_size": total_size,
            "total_backup_size_mb": total_size / (1024 * 1024),
            "last_backup_time": self.config.get("last_backup_time"),
            "next_backup_time": self._calculate_next_backup_time(),
        }

    def _calculate_next_backup_time(self) -> str | None:
        """计算下次备份时间"""
        last_backup = self.config.get("last_backup_time")
        if not last_backup:
            return None

        try:
            last_time = datetime.strptime(last_backup, "%Y-%m-%d %H:%M:%S")
            interval = self.config.get("backup_interval_days", 1)
            next_time = last_time + timedelta(days=interval)
            return next_time.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    def should_backup(self) -> bool:
        """
        检查是否需要备份

        Returns:
            是否需要备份
        """
        if not self.config.get("auto_backup_enabled", True):
            return False

        last_backup = self.config.get("last_backup_time")
        if not last_backup:
            return True

        try:
            last_time = datetime.strptime(last_backup, "%Y-%m-%d %H:%M:%S")
            interval = self.config.get("backup_interval_days", 1)
            next_time = last_time + timedelta(days=interval)
            return datetime.now() >= next_time
        except ValueError:
            return True

    def auto_backup(self) -> dict[str, Any] | None:
        """
        自动备份（如果需要）

        Returns:
            备份结果（如果执行了备份）
        """
        if self.should_backup():
            return self.create_backup()
        return None


backup_manager = BackupManager()
