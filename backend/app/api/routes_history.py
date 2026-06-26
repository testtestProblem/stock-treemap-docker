"""歷史績效端點。

GET /api/history/performance — 階段 5 實作
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/performance")
def get_performance():
    # TODO 階段 5 實作
    return {"message": "階段 5 尚未實作"}
