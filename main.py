from fastapi import FastAPI, Request, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import traceback
from tortoise.contrib.fastapi import register_tortoise
# 导入数据模型和数据库配置
from core.loguru import logger
from config import config
from core.lifespan import lifespan
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from middleware.logger_middleware import register_middleware
from schemas.Baseresponse import error_response
# 创建FastAPI实例
app = FastAPI(
    title=config.PROJECT_NAME,
    description=config.PROJECT_DESCRIPTION,
    version=config.VERSION,
    lifespan=lifespan,
    debug=config.DEBUG  # 确保设置debug模式
)

# 在应用启动前注册中间件
register_middleware(app)
logger.info("中间件注册成功")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 在 main.py 中，直接使用主 app 实例添加路由
@app.get("/api/test123")
async def index():
    
    # return error_response(message="失败了登录")
    raise HTTPException(status_code=500, detail="测试错误")

# 自定义错误处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误，输出详细错误信息到控制台"""
    error_detail = str(exc)
    logger.error(f"请求验证错误: {error_detail}")
    logger.error(f"错误详情: {exc.errors()}")
    if hasattr(exc, 'body'):
        logger.error(f"客户端提交的数据: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "请求数据验证失败"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常，记录详细信息"""
    logger.error(f"HTTP错误: {exc.detail} (状态码: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "message": "请求处理失败"}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常，输出详细堆栈到控制台"""
    error_msg = str(exc)
    trace = traceback.format_exc()
    logger.error(f"未处理的异常: {error_msg}")
    logger.error(f"异常堆栈: \n{trace}")
    logger.error(f"请求路径: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "message": error_msg if config.DEBUG else "请联系管理员"}
    )

# 注册数据库
register_tortoise(
    app,
    config=config.DATABASE_CONFIG,
    generate_schemas=False,  # 不自动生成数据库表，我们使用 Aerich 来管理迁移
    add_exception_handlers=False,  # 关闭自动异常处理，使用我们自定义的处理器
)



# 运行服务器（当直接运行此文件时）
if __name__ == "__main__":
    logger.info("启动服务器")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
