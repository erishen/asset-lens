"""
Backup Routes - 备份相关 API
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/status")
async def get_backup_status():
    """获取备份状态"""
    from ...data.backup_manager import backup_manager

    return backup_manager.get_backup_status()


@router.post("/create")
async def create_backup():
    """创建备份"""
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
