"""管理員端點（正式環境建議加 Auth 保護）。

GET  /api/admin/export-db  — 下載 SQLite 資料庫檔案至本地
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.db.database import DB_PATH

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/export-db")
def export_db():
    """下載 backend/data/app.db。

    回傳 SQLite 檔案，瀏覽器會自動另存新檔。
    """
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="資料庫檔案不存在")

    return FileResponse(
        path=str(DB_PATH),
        media_type="application/octet-stream",
        filename="app.db",
        headers={"Content-Disposition": "attachment; filename=app.db"},
    )
