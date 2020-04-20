from oc_stats.common import ROOT_DIR

CACHE_DIR = ROOT_DIR.parent / "cache"
_GLOBAL_CACHE_ENABLED = False


def set_global_cache_enabled(is_enabled: bool) -> None:
    global _GLOBAL_CACHE_ENABLED
    _GLOBAL_CACHE_ENABLED = is_enabled


def is_global_cache_enabled() -> bool:
    global _GLOBAL_CACHE_ENABLED
    return _GLOBAL_CACHE_ENABLED
