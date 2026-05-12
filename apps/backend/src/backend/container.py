"""Bedrock 应用的扁平化依赖注入容器。"""

from dependency_injector import containers, providers

from backend.domain.repository.user_repository import UserRepository
from backend.domain.service.user_service import UserService


class AppContainer(containers.DeclarativeContainer):
    """根 DI 容器，所有 provider 扁平注册，无子容器。"""

    # --- Repository 层 ---
    user_repository = providers.Singleton(UserRepository)

    # --- Service 层 ---
    user_service = providers.Singleton(UserService, repository=user_repository)
