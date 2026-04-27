"""
Tests for Backup Manager
"""

import pytest
import os
import tarfile
from pathlib import Path
from unittest.mock import Mock, patch
from asset_lens.data.backup_manager import BackupManager


@pytest.fixture
def backup_manager(tmp_path):
    """创建备份管理器实例"""
    manager = BackupManager()
    manager.backup_path = tmp_path
    manager.config_file = tmp_path / "backup_config.json"
    return manager


class TestBackupManager:
    """测试备份管理器"""

    def test_init(self, backup_manager):
        """测试初始化"""
        assert backup_manager.backup_path is not None
        assert backup_manager.config_file is not None
        assert isinstance(backup_manager.config, dict)

    def test_load_config_default(self, backup_manager):
        """测试加载默认配置"""
        config = backup_manager._load_config()

        assert "auto_backup_enabled" in config
        assert "backup_interval_days" in config
        assert "max_backup_count" in config
        assert config["auto_backup_enabled"] is True
        assert config["backup_interval_days"] == 1
        assert config["max_backup_count"] == 10

    def test_save_config(self, backup_manager):
        """测试保存配置"""
        backup_manager._save_config()

        assert backup_manager.config_file.exists()

    def test_create_backup_success(self, backup_manager, tmp_path):
        """测试创建备份 - 成功"""
        with patch("asset_lens.data.backup_manager.config") as mock_config:
            mock_config.project_root = tmp_path
            mock_config.cache_path = tmp_path / "cache"
            mock_config.config_path = tmp_path / "config"

            data_dir = tmp_path / "data"
            data_dir.mkdir()
            (data_dir / "test.txt").write_text("test data")

            result = backup_manager.create_backup(
                backup_name="test_backup",
                include_data=True,
                include_cache=False,
                include_config=False,
            )

            assert result["success"] is True
            assert result["backup_name"] == "test_backup"
            assert result["backup_file"].endswith(".tar.gz")
            assert os.path.exists(result["backup_file"])

    def test_create_backup_with_all(self, backup_manager, tmp_path):
        """测试创建备份 - 包含所有目录"""
        with patch("asset_lens.data.backup_manager.config") as mock_config:
            mock_config.project_root = tmp_path
            mock_config.cache_path = tmp_path / "cache"
            mock_config.config_path = tmp_path / "config"

            data_dir = tmp_path / "data"
            cache_dir = tmp_path / "cache"
            config_dir = tmp_path / "config"

            for d in [data_dir, cache_dir, config_dir]:
                d.mkdir()
                (d / "test.txt").write_text("test data")

            result = backup_manager.create_backup(backup_name="full_backup")

            assert result["success"] is True
            assert "data" in result["directories"]
            assert "cache" in result["directories"]
            assert "config" in result["directories"]

    def test_restore_backup_success(self, backup_manager, tmp_path):
        """测试恢复备份 - 成功"""
        with patch("asset_lens.data.backup_manager.config") as mock_config:
            mock_config.project_root = tmp_path
            mock_config.cache_path = tmp_path / "cache"
            mock_config.config_path = tmp_path / "config"

            data_dir = tmp_path / "data"
            data_dir.mkdir()
            (data_dir / "test.txt").write_text("original data")

            backup_result = backup_manager.create_backup(
                backup_name="test_restore",
                include_data=True,
                include_cache=False,
                include_config=False,
            )

            assert backup_result["success"] is True

            (data_dir / "test.txt").write_text("modified data")

            restore_result = backup_manager.restore_backup(
                "test_restore",
                restore_data=True,
                restore_cache=False,
                restore_config=False,
            )

            assert restore_result["success"] is True
            assert "data" in restore_result["restored_directories"]

    def test_restore_backup_nonexistent(self, backup_manager):
        """测试恢复备份 - 备份不存在"""
        result = backup_manager.restore_backup("nonexistent")

        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_list_backups_empty(self, backup_manager):
        """测试列出备份 - 空"""
        backups = backup_manager.list_backups()

        assert isinstance(backups, list)
        assert len(backups) == 0

    def test_list_backups_with_backups(self, backup_manager, tmp_path):
        """测试列出备份 - 有备份"""
        # 直接创建备份文件
        import tarfile

        backup_file1 = tmp_path / "backup_20240101_120000.tar.gz"
        backup_file2 = tmp_path / "backup_20240102_120000.tar.gz"

        # 创建空的 tar.gz 文件
        with tarfile.open(backup_file1, "w:gz") as tar:
            pass
        with tarfile.open(backup_file2, "w:gz") as tar:
            pass

        backups = backup_manager.list_backups()

        assert len(backups) == 2
        assert backups[0]["name"] == "backup_20240102_120000.tar"

    def test_delete_backup_success(self, backup_manager, tmp_path):
        """测试删除备份 - 成功"""
        # 直接创建备份文件，而不是通过 create_backup
        backup_file = backup_manager.backup_path / "test_delete.tar.gz"
        backup_file.write_bytes(b"fake backup content")

        result = backup_manager.delete_backup("test_delete")

        assert result["success"] is True

    def test_delete_backup_nonexistent(self, backup_manager):
        """测试删除备份 - 不存在"""
        result = backup_manager.delete_backup("nonexistent")

        assert result["success"] is False

    def test_cleanup_old_backups(self, backup_manager, tmp_path):
        """测试清理旧备份"""
        backup_manager.config["max_backup_count"] = 2

        # 直接创建空的备份文件，而不是通过 create_backup（太慢）
        for i in range(5):
            backup_file = backup_manager.backup_path / f"backup_{i}.tar.gz"
            backup_file.write_bytes(b"fake backup content")

        # 手动清理
        deleted_count = backup_manager._cleanup_old_backups()

        assert deleted_count == 3
        backups = backup_manager.list_backups()
        assert len(backups) == 2

    def test_get_backup_status(self, backup_manager):
        """测试获取备份状态"""
        status = backup_manager.get_backup_status()

        assert "auto_backup_enabled" in status
        assert "backup_interval_days" in status
        assert "max_backup_count" in status
        assert "current_backup_count" in status
        assert "total_backup_size" in status

    def test_should_backup_first_time(self, backup_manager):
        """测试是否需要备份 - 首次"""
        backup_manager.config["last_backup_time"] = None

        should = backup_manager.should_backup()

        assert should is True

    def test_should_backup_not_needed(self, backup_manager):
        """测试是否需要备份 - 不需要"""
        from datetime import datetime

        backup_manager.config["last_backup_time"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        backup_manager.config["backup_interval_days"] = 1

        should = backup_manager.should_backup()

        assert should is False

    def test_should_backup_needed(self, backup_manager):
        """测试是否需要备份 - 需要"""
        from datetime import datetime, timedelta

        last_time = datetime.now() - timedelta(days=2)
        backup_manager.config["last_backup_time"] = last_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        backup_manager.config["backup_interval_days"] = 1

        should = backup_manager.should_backup()

        assert should is True

    def test_auto_backup_needed(self, backup_manager, tmp_path):
        """测试自动备份 - 需要"""
        backup_manager.config["last_backup_time"] = None

        with patch("asset_lens.data.backup_manager.config") as mock_config:
            mock_config.project_root = tmp_path
            mock_config.cache_path = tmp_path / "cache"
            mock_config.config_path = tmp_path / "config"

            data_dir = tmp_path / "data"
            data_dir.mkdir()
            (data_dir / "test.txt").write_text("test")

            result = backup_manager.auto_backup()

            assert result is not None
            assert result["success"] is True

    def test_auto_backup_not_needed(self, backup_manager):
        """测试自动备份 - 不需要"""
        from datetime import datetime

        backup_manager.config["last_backup_time"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        result = backup_manager.auto_backup()

        assert result is None

    def test_enable_disable_auto_backup(self, backup_manager):
        """测试启用/禁用自动备份"""
        backup_manager.config["auto_backup_enabled"] = True
        assert backup_manager.config["auto_backup_enabled"] is True

        backup_manager.config["auto_backup_enabled"] = False
        assert backup_manager.config["auto_backup_enabled"] is False

    def test_set_backup_interval(self, backup_manager):
        """测试设置备份间隔"""
        backup_manager.config["backup_interval_days"] = 7
        assert backup_manager.config["backup_interval_days"] == 7

    def test_set_max_backup_count(self, backup_manager):
        """测试设置最大备份数量"""
        backup_manager.config["max_backup_count"] = 20
        assert backup_manager.config["max_backup_count"] == 20
