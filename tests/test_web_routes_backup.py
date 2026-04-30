"""
Tests for Web Routes - Backup API.
备份 API 路由测试
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "asset_lens"))

from asset_lens.web.routes.backup import router


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


class TestGetBackupStatus:
    """测试获取备份状态"""

    def test_get_backup_status(self, client):
        """测试获取备份状态"""
        mock_manager = MagicMock()
        mock_manager.get_backup_status.return_value = {
            "last_backup": "2024-01-01",
            "total_backups": 5,
            "status": "ok",
        }

        with patch.dict(sys.modules, {"asset_lens.data.backup_manager": MagicMock(backup_manager=mock_manager)}):
            response = client.get("/api/backup/status")

            assert response.status_code == 200


class TestCreateBackup:
    """测试创建备份"""

    def test_create_backup_success(self, client):
        """测试创建备份成功"""
        mock_manager = MagicMock()
        mock_manager.create_backup.return_value = {
            "success": True,
            "backup_path": "/backup/2024-01-01",
            "files_backed_up": 10,
        }

        with patch.dict(sys.modules, {"asset_lens.data.backup_manager": MagicMock(backup_manager=mock_manager)}):
            response = client.post("/api/backup/create")

            assert response.status_code == 200

    def test_create_backup_failure(self, client):
        """测试创建备份失败"""
        mock_manager = MagicMock()
        mock_manager.create_backup.return_value = {
            "success": False,
            "errors": ["磁盘空间不足"],
        }

        with patch.dict(sys.modules, {"asset_lens.data.backup_manager": MagicMock(backup_manager=mock_manager)}):
            response = client.post("/api/backup/create")

            assert response.status_code == 500


class TestListBackups:
    """测试列出备份"""

    def test_list_backups(self, client):
        """测试列出备份"""
        mock_manager = MagicMock()
        mock_manager.list_backups.return_value = [
            {"name": "backup_2024-01-01", "size": "100MB", "date": "2024-01-01"},
            {"name": "backup_2024-01-02", "size": "120MB", "date": "2024-01-02"},
        ]

        with patch.dict(sys.modules, {"asset_lens.data.backup_manager": MagicMock(backup_manager=mock_manager)}):
            response = client.get("/api/backup/list")

            assert response.status_code == 200

    def test_list_backups_empty(self, client):
        """测试空备份列表"""
        mock_manager = MagicMock()
        mock_manager.list_backups.return_value = []

        with patch.dict(sys.modules, {"asset_lens.data.backup_manager": MagicMock(backup_manager=mock_manager)}):
            response = client.get("/api/backup/list")

            assert response.status_code == 200
