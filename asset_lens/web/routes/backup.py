"""
Backup Routes - 备份相关 API
"""

import os

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/backup", tags=["backup"])

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")


@router.get("/status")
async def get_backup_status():
    """获取备份状态"""
    # Demo 模式下返回模拟状态
    if DEMO_MODE:
        return {
            "enabled": False,
            "last_backup": None,
            "backup_count": 0,
            "demo_mode": True,
            "message": "Demo 模式下不支持备份操作",
        }

    from ...data.backup_manager import backup_manager

    return backup_manager.get_backup_status()


@router.post("/create")
async def create_backup():
    """创建备份"""
    # Demo 模式下禁止创建备份
    if DEMO_MODE:
        raise HTTPException(status_code=403, detail="Demo 模式下不支持创建备份")

    from ...data.backup_manager import backup_manager

    result = backup_manager.create_backup()

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("errors", ["备份失败"]))

    return result


@router.get("/list")
async def list_backups():
    """列出备份"""
    from ...data.backup_manager import backup_manager

    backups = backup_manager.list_backups()

    return {
        "count": len(backups),
        "backups": backups,
    }
