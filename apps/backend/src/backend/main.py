"""FastAPI 应用入口。"""

import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from core.config.loader import ConfigLoader
from core.context.request import (
    RequestContextParams,
    clear_request_context,
    set_request_context,
)
from core.database.state import DatabaseRegistry
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.container import AppContainer
from backend.domain.api import user_router

logger = logging.getLogger(__name__)


async def initialize_db_engines(config: dict) -> None:
    """阶段一：初始化数据库引擎并注册租户 schema。"""
    db_config = config.get("database", {})
    tenants = config.get("tenants", {})

    db_name = list(tenants.values())[0].get("database", {}).get("name", "bedrock") if tenants else "bedrock"
    url = (
        f"postgresql+psycopg://{db_config.get('username', 'postgres')}"
        f":{db_config.get('password', 'postgres')}"
        f"@{db_config.get('host', 'localhost')}"
        f":{db_config.get('port', 5432)}"
        f"/{db_name}"
    )

    engine = create_async_engine(
        url,
        pool_size=db_config.get("pool_size", 20),
        max_overflow=db_config.get("max_overflow", 5),
        echo=False,
    )

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    DatabaseRegistry.register_shared_engine(engine, factory)

    for tenant_name, tenant_config in tenants.items():
        schema = tenant_config.get("database", {}).get("name", tenant_name)
        DatabaseRegistry.register_tenant_schema(tenant_name, schema)
        logger.info("已注册租户: %s -> schema: %s", tenant_name, schema)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """应用生命周期：启动与关闭。"""
    config = ConfigLoader.load()

    # 阶段一：初始化数据库
    await initialize_db_engines(config)
    logger.info("数据库引擎初始化完成")

    # 装配依赖注入容器
    container = AppContainer()
    container.wire(modules=["backend.domain.api.user"])
    app.state.container = container

    logger.info("Bedrock 后端已在端口 %s 启动", config.get("server", {}).get("port", 8000))

    yield

    # 关闭
    engine = DatabaseRegistry.get_engine()
    await engine.dispose()
    DatabaseRegistry.clear()
    logger.info("Bedrock 后端已关闭")


app = FastAPI(
    title="Bedrock API",
    description="公司级规范示例项目后端 API",
    version="0.1.0",
    lifespan=lifespan,
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next) -> Response:
    """为每个请求设置请求上下文（租户、用户）。"""
    set_request_context(
        RequestContextParams(
            tenant="default",
            username=request.headers.get("X-Username", "anonymous"),
            roles=request.headers.get("X-Roles", "").split(",") if request.headers.get("X-Roles") else [],
            request_id=str(uuid.uuid4()),
        )
    )
    try:
        response = await call_next(request)
        return response
    finally:
        clear_request_context()


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next) -> Response:
    """记录请求方法、路径及响应状态。"""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %d (%.1fms)", request.method, request.url.path, response.status_code, elapsed)
    return response


# 注册路由
app.include_router(user_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "bedrock"}
