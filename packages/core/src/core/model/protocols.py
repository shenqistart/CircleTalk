"""领域协议定义 - 使用 Protocol 实现结构化子类型（structural subtyping）。

本模块定义了系统中资源实体应该遵守的协议（Protocol）。
Protocol 使用结构化子类型（duck typing at compile time），
类不需要显式继承 Protocol，只要实现了所需的属性和方法即可。

参考: PEP 544 - Protocols: Structural subtyping (static duck typing)
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ResourceEntity(Protocol):
    """
    资源实体协议，定义所有 CRUD 资源必须具备的基本属性。

    所有通过 CRUDRouterFactory 管理的资源实体都应该满足此协议，
    无需显式继承，只需要提供这些属性即可通过类型检查。

    Attributes:
        id: 资源的唯一标识符

    Note:
        - @runtime_checkable 允许使用 isinstance() 运行时检查
        - 这是结构化子类型，类不需要显式声明实现此 Protocol
        - Pyright/mypy 会在编译时验证类型兼容性
    """

    id: str
    "资源的唯一标识符"
