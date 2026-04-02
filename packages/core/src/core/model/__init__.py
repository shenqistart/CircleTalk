"""核心模型 Mixin 导出。"""

from core.model.audit_mixin import AuditMixin, TimestampMixin
from core.model.fts_mixin import FTSMixin
from core.model.ui_config_mixin import UIConfigMixin

__all__ = [
    "AuditMixin",
    "FTSMixin",
    "TimestampMixin",
    "UIConfigMixin",
]
