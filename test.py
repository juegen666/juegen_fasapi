import pytest
import asyncio
from unittest import mock
from tortoise import Tortoise
from fastapi.testclient import TestClient
from fastapi import FastAPI
from model.enum.user import UserStatus, UserType, SexType
from model.user import User
from schemas.internal.user import CreateUserRequest, UpdateUserRequest, UserListRequest
from schemas.internal.user import LoginRequest, UserListItem
from core.auth import get_admin_user
from schemas.Baseresponse import success_response, error_response
import os

# 设置环境变量以避免SECRET_KEY警告
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"

# 为测试准备Tortoise ORM配置
TEST_DB_URL = "sqlite://:memory:"

# Tortoise ORM测试配置
TORTOISE_TEST_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {"file_path": ":memory:"}
        }
    },
    "apps": {
        "models": {
            "models": ["model.user"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
}

# 提供event_loop fixture
@pytest.fixture(scope="session")
def event_loop():
    """创建一个session范围的事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 在测试之前初始化数据库，测试之后关闭数据库
@pytest.fixture(scope="session", autouse=True)
async def initialize_database():
    """初始化测试数据库"""
    await Tortoise.init(config=TORTOISE_TEST_CONFIG)
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()

# 在每个测试函数之前准备测试数据
@pytest.fixture(autouse=True)
async def prepare_test_data():
    """准备测试数据"""
    # 清空已有数据
    await User.all().delete()
    
    # 创建测试数据
    from utils.crypto import PasswordManager
    await User.create(
        username="admin",
        password=PasswordManager.hash("admin123"),
        nickname="管理员",
        user_type=UserType.SUPERUSER,
        user_status=UserStatus.ACTIVE,
        sex=SexType.MALE,
        user_email="admin@example.com",
        user_phone="13800138000"
    )
    
    await User.create(
        username="user1",
        password=PasswordManager.hash("user123"),
        nickname="普通用户",
        user_type=UserType.NORMAL,
        user_status=UserStatus.ACTIVE,
        sex=SexType.FEMALE,
        user_email="user1@example.com",
        user_phone="13800138001"
    )
    
    await User.create(
        username="disabled",
        password=PasswordManager.hash("disabled123"),
        nickname="禁用用户",
        user_type=UserType.NORMAL,
        user_status=UserStatus.DISABLED,
        sex=SexType.UNKNOWN,
        user_email="disabled@example.com",
        user_phone="13800138002"
    )
    
    yield

# 创建测试客户端
@pytest.fixture
def client():
    """创建测试客户端"""
    # 创建一个测试用的FastAPI应用
    app = FastAPI()
    
    # 模拟依赖注入，返回一个固定的用户ID作为已认证用户
    async def override_get_admin_user():
        return {"user_id": 1, "user_type": UserType.SUPERUSER}
    
    # 添加测试路由
    from api.internal.user.user import router as user_router
    
    # 替换依赖项
    app.include_router(user_router)
    app.dependency_overrides[get_admin_user] = override_get_admin_user
    
    return TestClient(app)

# 测试登录接口
@pytest.mark.asyncio
async def test_login_success(client):
    # 模拟login_user函数的返回值
    with mock.patch('api.internal.user.user.login_user', return_value=success_response(
        message="登录成功",
        data="mock_token"
    )):
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = client.post("/user/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "登录成功"
        assert data["data"] == "mock_token"

# 测试登录失败接口
@pytest.mark.asyncio
async def test_login_failed_wrong_password(client):
    # 模拟login_user函数对于错误密码的返回值
    with mock.patch('api.internal.user.user.login_user', return_value=error_response("用户名或密码错误")):
        login_data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        response = client.post("/user/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
        assert data["message"] == "用户名或密码错误"

# 测试创建用户接口
@pytest.mark.asyncio
async def test_create_user(client):
    # 模拟create_user函数的返回值
    with mock.patch('api.internal.user.user.create_user', return_value=success_response(
        message="用户创建成功",
        data={"id": 4, "username": "newuser"}
    )):
        user_data = {
            "username": "newuser",
            "password": "newpass123",
            "nickname": "新用户",
            "user_type": UserType.NORMAL,
            "user_status": UserStatus.ACTIVE,
            "sex": SexType.MALE,
            "remarks": "测试创建用户",
            "user_phone": "13800138003",
            "user_email": "newuser@example.com"
        }
        response = client.post("/user/createuser", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "用户创建成功"
        assert data["data"]["username"] == "newuser"

# 测试获取用户详情接口
@pytest.mark.asyncio
async def test_get_user_info(client):
    # 模拟get_user函数的返回值
    with mock.patch('api.internal.user.user.get_user', return_value=success_response(
        message="获取用户详情成功",
        data={
            "id": 1,
            "username": "admin",
            "nickname": "管理员",
            "user_type": UserType.SUPERUSER,
            "user_status": UserStatus.ACTIVE,
            "user_phone": "13800138000",
            "user_email": "admin@example.com",
            "avatar": None
        }
    )):
        response = client.get("/user/getuserinfo/1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "获取用户详情成功"
        assert data["data"]["username"] == "admin"

# 测试更新用户接口
@pytest.mark.asyncio
async def test_update_user(client):
    # 模拟update_user函数的返回值
    with mock.patch('api.internal.user.user.update_user', return_value=success_response(
        message="用户更新成功"
    )):
        update_data = {
            "username": "admin",
            "nickname": "超级管理员",
            "user_type": UserType.SUPERUSER,
            "user_status": UserStatus.ACTIVE
        }
        response = client.post("/user/updateuser/1", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "用户更新成功"

# 测试删除用户接口
@pytest.mark.asyncio
async def test_delete_user(client):
    # 模拟delete_user函数的返回值
    with mock.patch('api.internal.user.user.delete_user', return_value=success_response(
        message="用户删除成功"
    )):
        response = client.post("/user/deleteuser/3")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "用户删除成功"

# 测试获取用户列表接口
@pytest.mark.asyncio
async def test_get_user_list(client):
    # 模拟get_user_list函数的返回值
    with mock.patch('api.internal.user.user.get_user_list', return_value=success_response(
        message="用户列表获取成功",
        data={
            "items": [
                {
                    "id": 1,
                    "username": "admin",
                    "nickname": "管理员",
                    "user_type": UserType.SUPERUSER,
                    "user_status": UserStatus.ACTIVE,
                    "user_phone": "13800138000",
                    "user_email": "admin@example.com",
                    "avatar": None
                },
                {
                    "id": 2,
                    "username": "user1",
                    "nickname": "普通用户",
                    "user_type": UserType.NORMAL,
                    "user_status": UserStatus.ACTIVE,
                    "user_phone": "13800138001",
                    "user_email": "user1@example.com",
                    "avatar": None
                }
            ],
            "page_info": {
                "total": 2,
                "page": 1,
                "page_size": 10,
                "total_pages": 1
            }
        }
    )):
        # 构造请求参数
        response = client.get("/user/getuserlist", params={
            "page": 1,
            "page_size": 10,
            "user_status": UserStatus.ACTIVE
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "用户列表获取成功"
        assert len(data["data"]["items"]) == 2
        assert data["data"]["page_info"]["total"] == 2

# 运行测试
if __name__ == "__main__":
    pytest.main(["-xvs", "test.py"]) 