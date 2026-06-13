"""Baostock 全局会话管理器 - 单例模式，避免重复 login/logout"""

import logging
import sys
from io import StringIO
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)


class _BaostockSession:
    """Baostock 全局会话（单例）"""

    _instance: "_BaostockSession | None" = None
    _logged_in: bool = False
    _bs: Any = None

    @classmethod
    def get(cls) -> "_BaostockSession":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    def login(self) -> bool:
        """登录 Baostock（如果已登录则跳过）"""
        if self._logged_in:
            return True
        try:
            import baostock as bs

            self._bs = bs
            # 抑制 stdout 输出
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            try:
                lg = bs.login()
            finally:
                sys.stdout = old_stdout

            if lg.error_code != "0":
                logger.error(f"Baostock 登录失败: {lg.error_msg}")
                return False

            self._logged_in = True
            logger.debug("Baostock 已登录")
            return True
        except ImportError:
            logger.warning("Baostock 未安装")
            return False
        except Exception as e:
            logger.error(f"Baostock 登录异常: {e}")
            return False

    def logout(self):
        """登出 Baostock（仅在程序结束时调用）"""
        if not self._logged_in or self._bs is None:
            return
        try:
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            try:
                self._bs.logout()
            finally:
                sys.stdout = old_stdout
            self._logged_in = False
            logger.debug("Baostock 已登出")
        except Exception as e:
            logger.debug(f"Baostock 登出异常: {e}")

    @property
    def bs(self):
        """获取 baostock 模块（确保已登录）"""
        if not self._logged_in:
            self.login()
        return self._bs


# 全局单例
baostock_session = _BaostockSession.get()


@contextmanager
def baostock_ctx():
    """Baostock 会话上下文管理器，确保登录状态"""
    session = _BaostockSession.get()
    logged_in_by_us = False
    if not session.is_logged_in:
        logged_in_by_us = session.login()
    try:
        yield session.bs
    finally:
        # 不主动 logout，复用全局会话
        pass


def baostock_cleanup():
    """程序结束时清理 Baostock 会话"""
    _BaostockSession.get().logout()
