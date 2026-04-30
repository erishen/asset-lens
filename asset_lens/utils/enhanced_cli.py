"""
Enhanced CLI Utilities with colors and progress bars.
增强版 CLI 工具 - 支持彩色输出和进度条
"""

import sys
from collections.abc import Iterator, Sized
from dataclasses import dataclass
from enum import Enum
from typing import Any

try:
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
    from rich.syntax import Syntax
    from rich.table import Table

    RICH_AVAILABLE = True
    del rprint  # Remove unused import
except ImportError:
    RICH_AVAILABLE = False

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    import click

    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False


class Color(Enum):
    """颜色枚举"""

    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"
    BLACK = "black"


@dataclass
class ProgressBarConfig:
    """进度条配置"""

    description: str = "Processing"
    total: int = 100
    unit: str = "items"
    color: str = "cyan"


class EnhancedCLI:
    """增强版 CLI 工具"""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.use_colors = RICH_AVAILABLE or sys.stdout.isatty()

    def print_colored(self, message: str, color: Color = Color.WHITE, bold: bool = False):
        """打印彩色文本"""
        if RICH_AVAILABLE and self.console:
            style = f"{color.value} bold" if bold else color.value
            self.console.print(message, style=style)
        elif CLICK_AVAILABLE:
            click_style = click.style(message, fg=color.value, bold=bold)
            click.echo(click_style)
        else:
            print(message)

    def print_success(self, message: str):
        """打印成功消息"""
        self.print_colored(f"✅ {message}", Color.GREEN, bold=True)

    def print_error(self, message: str):
        """打印错误消息"""
        self.print_colored(f"❌ {message}", Color.RED, bold=True)

    def print_warning(self, message: str):
        """打印警告消息"""
        self.print_colored(f"⚠️  {message}", Color.YELLOW, bold=True)

    def print_info(self, message: str):
        """打印信息消息"""
        self.print_colored(f"ℹ️  {message}", Color.BLUE)

    def print_header(self, title: str, width: int = 60):
        """打印标题"""
        if RICH_AVAILABLE and self.console:
            self.console.print(Panel(title, width=width, style="bold cyan"))
        else:
            print("\n" + "=" * width)
            print(title.center(width))
            print("=" * width + "\n")

    def print_subheader(self, title: str, width: int = 60):
        """打印子标题"""
        if RICH_AVAILABLE and self.console:
            self.console.print(f"\n[bold]{title}[/bold]", style="cyan")
            self.console.print("─" * width, style="dim")
        else:
            print("\n" + "-" * width)
            print(title)
            print("-" * width + "\n")

    def print_table(self, title: str, headers: list[str], rows: list[list[str]]):
        """打印表格"""
        if RICH_AVAILABLE and self.console:
            table = Table(title=title, show_header=True, header_style="bold cyan")
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*row)
            self.console.print(table)
        else:
            print(f"\n{title}")
            print("-" * 60)
            print(" | ".join(headers))
            print("-" * 60)
            for row in rows:
                print(" | ".join(row))
            print("-" * 60 + "\n")

    def print_key_value(self, key: str, value: Any, indent: int = 0, color: Color | None = None):
        """打印键值对"""
        prefix = " " * indent
        if color:
            self.print_colored(f"{prefix}{key}: {value}", color)
        else:
            print(f"{prefix}{key}: {value}")

    def print_json(self, data: dict[str, Any], title: str | None = None):
        """打印 JSON 数据"""
        import json

        if title:
            self.print_subheader(title)

        if RICH_AVAILABLE and self.console:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
            self.console.print(syntax)
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))

    def create_progress_bar(self, config: ProgressBarConfig):
        """创建进度条"""
        if RICH_AVAILABLE and self.console:
            return RichProgressBar(config, self.console)
        elif TQDM_AVAILABLE:
            return TqdmProgressBar(config)
        else:
            return SimpleProgressBar(config)

    def progress_iterator(self, iterable: Iterator, description: str = "Processing", total: int | None = None):
        """带进度条的迭代器"""
        if total is None:
            try:
                if isinstance(iterable, Sized):
                    total = len(iterable)
            except (TypeError, AttributeError):
                total = None

        if RICH_AVAILABLE and self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console,
            ) as progress:
                task = progress.add_task(description, total=total)
                for item in iterable:
                    yield item
                    progress.advance(task)
        elif TQDM_AVAILABLE:
            for item in tqdm(iterable, desc=description, total=total):
                yield item
        else:
            for item in iterable:
                yield item

    def confirm(self, message: str, default: bool = False) -> bool:
        """确认操作"""
        if CLICK_AVAILABLE:
            return click.confirm(message, default=default)
        else:
            response = input(f"{message} (y/n): ").lower()
            return response == "y" if response else default

    def prompt(self, message: str, default: str | None = None) -> str:
        """提示输入"""
        if CLICK_AVAILABLE:
            result = click.prompt(message, default=default)
            return str(result) if result is not None else (default or "")
        else:
            prompt_msg = f"{message}"
            if default:
                prompt_msg += f" [{default}]"
            prompt_msg += ": "
            return input(prompt_msg) or default or ""

    def clear_screen(self):
        """清屏"""
        if CLICK_AVAILABLE:
            click.clear()
        else:
            import os

            os.system("clear" if os.name == "posix" else "cls")


class RichProgressBar:
    """Rich 进度条"""

    def __init__(self, config: ProgressBarConfig, console):
        self.config = config
        self.console = console
        self.progress: Progress | None = None
        self.task: int | None = None

    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        )
        self.progress.__enter__()
        self.task = self.progress.add_task(self.config.description, total=self.config.total)
        return self

    def __exit__(self, *args):
        if self.progress:
            self.progress.__exit__(*args)

    def update(self, advance: int = 1):
        """更新进度"""
        if self.progress and self.task is not None:
            self.progress.advance(self.task, advance)  # type: ignore

    def set_description(self, description: str):
        """设置描述"""
        if self.progress and self.task is not None:
            self.progress.update(self.task, description=description)  # type: ignore


class TqdmProgressBar:
    """Tqdm 进度条"""

    def __init__(self, config: ProgressBarConfig):
        self.config = config
        self.pbar = None

    def __enter__(self):
        self.pbar = tqdm(total=self.config.total, desc=self.config.description, unit=self.config.unit)
        return self

    def __exit__(self, *args):
        if self.pbar:
            self.pbar.close()

    def update(self, advance: int = 1):
        """更新进度"""
        if self.pbar:
            self.pbar.update(advance)

    def set_description(self, description: str):
        """设置描述"""
        if self.pbar:
            self.pbar.set_description(description)


class SimpleProgressBar:
    """简单进度条"""

    def __init__(self, config: ProgressBarConfig):
        self.config = config
        self.current = 0

    def __enter__(self):
        self.current = 0
        print(f"{self.config.description}: 0/{self.config.total}")
        return self

    def __exit__(self, *args):
        print(f"{self.config.description}: {self.current}/{self.config.total} ✓")

    def update(self, advance: int = 1):
        """更新进度"""
        self.current += advance
        percent = (self.current / self.config.total * 100) if self.config.total > 0 else 0
        print(f"{self.config.description}: {self.current}/{self.config.total} ({percent:.1f}%)")

    def set_description(self, description: str):
        """设置描述"""
        self.config.description = description


enhanced_cli = EnhancedCLI()
