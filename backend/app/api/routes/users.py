from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/users", tags=["用户管理"])

# 模拟数据
FAKE_USERS = [
    {"id": 1, "username": "alex", "role": "admin"},
    {"id": 2, "username": "dev_user", "role": "developer"},
]


@router.get("", summary="获取用户列表")
def get_users():
    return FAKE_USERS


@router.get("/{user_id}", summary="获取指定用户")
def get_user(user_id: int):
    for user in FAKE_USERS:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
