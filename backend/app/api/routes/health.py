from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["系统运维"]
)

@router.get("", summary="健康检查接口")
def check_health():
    return {"status": "healthy", "database": "connected"}