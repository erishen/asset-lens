"""
Logging system for asset-lens.
日志系统模块
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Literal


class SensitiveInfoFilter(logging.Filter):
    """过滤敏感信息的日志过滤器"""

    SENSITIVE_PATTERNS = [
        "api_key",
        "password",
        "secret",
        "token",
        "credential",
        "authorization",
        "bearer",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤包含敏感信息的日志记录"""
        message = record.getMessage().lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                record.msg = "[SENSITIVE INFO FILTERED]"
                break
        return True


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录，添加颜色"""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class ContextFilter(logging.Filter):
    """添加上下文信息的日志过滤器"""

    def __init__(self, context: dict | None = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def get_log_level() -> int:
    """从环境变量获取日志级别"""
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str, logging.INFO)


def get_log_format(include_context: bool = False) -> str:
    """获取日志格式"""
    base_format = "%(asctime)s | %(levelname)-8s | %(name)s"
    if include_context:
        base_format += " | %(filename)s:%(lineno)d"
    base_format += " | %(message)s"
    return base_format


def setup_logger(
    name: str = "asset_lens",
    level: int | None = None,
    log_file: Path | None = None,
    use_color: bool = True,
    rotation: Literal["size", "time", "none"] = "none",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    context: dict | None = None,
) -> logging.Logger:
    """
    设置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别（None 则从环境变量读取）
        log_file: 日志文件路径（可选）
        use_color: 是否使用彩色输出
        rotation: 日志轮转方式（size: 按大小, time: 按时间, none: 不轮转）
        max_bytes: 单个日志文件最大大小（仅 rotation="size" 时有效）
        backup_count: 保留的日志文件数量
        context: 上下文信息字典

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)

    if level is None:
        level = get_log_level()

    logger.setLevel(level)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if use_color and sys.stdout.isatty():
        formatter: logging.Formatter = ColoredFormatter(
            fmt=get_log_format(),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            fmt=get_log_format(),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveInfoFilter())
    if context:
        console_handler.addFilter(ContextFilter(context))
    logger.addHandler(console_handler)

    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_formatter = logging.Formatter(
            fmt=get_log_format(include_context=True),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if rotation == "size":
            file_handler: logging.Handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
        elif rotation == "time":
            file_handler = TimedRotatingFileHandler(
                log_file,
                when="midnight",
                backupCount=backup_count,
                encoding="utf-8",
            )
        else:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")

        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(SensitiveInfoFilter())
        if context:
            file_handler.addFilter(ContextFilter(context))
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "asset_lens") -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return logging.getLogger(name)


def configure_root_logger(
    level: int | None = None,
    log_file: Path | None = None,
    rotation: Literal["size", "time", "none"] = "none",
) -> None:
    """
    配置根日志记录器

    Args:
        level: 日志级别
        log_file: 日志文件路径
        rotation: 日志轮转方式
    """
    if level is None:
        level = get_log_level()

    logging.basicConfig(
        level=level,
        format=get_log_format(include_context=True),
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        if rotation == "size":
            handler: logging.Handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
        elif rotation == "time":
            handler = TimedRotatingFileHandler(
                log_file,
                when="midnight",
                backupCount=5,
                encoding="utf-8",
            )
        else:
            handler = logging.FileHandler(log_file, encoding="utf-8")

        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                fmt=get_log_format(include_context=True),
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logging.root.addHandler(handler)


logger = setup_logger()
