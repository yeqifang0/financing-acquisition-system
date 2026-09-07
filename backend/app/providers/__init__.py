"""多数据源路由层。

优先级（可配置）:
  1. cnbizapi   — CNBizAPI，永久免费（search/basic/verify 免费）
  2. hanhai     — 瀚海数据，注册即送 1000 次
  3. qichacha   — 企查查，20 次免费试用
  4. mock       — 模拟数据（兜底）
"""
import os
from .base import EnterpriseProvider

_PROVIDERS: list[EnterpriseProvider] = []
_initialized = False


def _init_providers():
    """延迟初始化所有数据源。"""
    global _initialized
    if _initialized:
        return
    _initialized = True

    # 延迟 import 避免循环依赖
    # 1. CNBizAPI（永久免费）
    try:
        from .cnbizapi import CNBizAPIProvider
        _PROVIDERS.append(CNBizAPIProvider())
    except Exception:
        pass

    # 2. 瀚海数据（1000 次免费）
    try:
        from .hanhai import HanhaiProvider
        _PROVIDERS.append(HanhaiProvider())
    except Exception:
        pass

    # 3. 企查查（20 次试用）
    try:
        from .qichacha_provider import QichachaProvider
        _PROVIDERS.append(QichachaProvider())
    except Exception:
        pass

    # 4. Mock（兜底）
    try:
        from .mock_provider import MockProvider
        _PROVIDERS.append(MockProvider())
    except Exception:
        pass


def get_providers() -> list[EnterpriseProvider]:
    _init_providers()
    return list(_PROVIDERS)


def get_available_providers() -> list[EnterpriseProvider]:
    """返回可用的数据源列表（按优先级排序）。"""
    _init_providers()
    return [p for p in _PROVIDERS if p.is_available()]


def collect_leads(keyword: str, count: int = 20) -> tuple[list[dict], str]:
    """按优先级依次尝试采集，返回 (leads, provider_name)。"""
    _init_providers()

    # 强制 mock 模式
    if os.getenv("QICHACHA_USE_MOCK", "0") == "1":
        from .mock_provider import MockProvider
        p = MockProvider()
        return p.collect_leads(keyword, count), p.name

    errors = []
    for p in _PROVIDERS:
        if not p.is_available():
            continue
        try:
            leads = p.collect_leads(keyword, count)
            if leads:
                return leads, p.name
        except Exception as e:
            errors.append(f"{p.name}: {e}")
            continue

    # 最后兜底：mock
    from .mock_provider import MockProvider
    p = MockProvider()
    leads = p.collect_leads(keyword, count)
    return leads, p.name + "(fallback)"


def get_provider_status() -> list[dict]:
    """返回所有数据源的连接状态（供 /api/config 展示）。"""
    _init_providers()
    result = []
    for p in _PROVIDERS:
        status = {"name": p.name, "label": p.label, "free_tier": p.free_tier, "note": p.note}
        try:
            test = p.test_connection()
            status.update(test)
        except Exception as e:
            status["auth_ok"] = False
            status["detail"] = str(e)
        result.append(status)
    return result
