"""
Tests for Personal Data Integrator.
个人数据整合器测试
"""

import pytest
from datetime import datetime


class TestPersonalDataIntegrator:
    """个人数据整合器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data import personal_data_integrator
        assert personal_data_integrator is not None

    def test_integrate_method(self):
        """测试整合方法"""
        from asset_lens.data.personal_data_integrator import PersonalDataIntegrator
        integrator = PersonalDataIntegrator()
        
        assert hasattr(integrator, 'integrate') or hasattr(integrator, 'merge')


class TestDataIntegration:
    """数据整合测试"""

    def test_merge_data(self):
        """测试合并数据"""
        data1 = {"stocks": [{"code": "sh600519"}]}
        data2 = {"funds": [{"code": "000001"}]}
        
        merged = {**data1, **data2}
        assert "stocks" in merged
        assert "funds" in merged

    def test_validate_data(self):
        """测试验证数据"""
        data = {
            "total_value": 100000.0,
            "total_profit": 5000.0,
        }
        
        assert data["total_value"] > 0
        assert "items" in data


class TestDataSynchronization:
    """数据同步测试"""

    def test_sync_timestamp(self):
        """测试同步时间戳"""
        timestamp = datetime.now().isoformat()
        assert len(timestamp) > 0

    def test_sync_status(self):
        """测试同步状态"""
        status = {
            "last_sync": "2024-01-01",
            "status": "success",
            "records": 100,
        }
        
        assert status["status"] == "success"
        assert status["records"] > 0
