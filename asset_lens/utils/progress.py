"""
Progress bar utility for asset-lens.
进度条工具模块
"""

import sys
from typing import Optional


class ProgressBar:
    """简单的进度条类"""
    
    def __init__(
        self,
        total: int,
        width: int = 50,
        prefix: str = "",
        suffix: str = "",
        fill: str = "█",
        empty: str = "░",
    ):
        """
        初始化进度条
        
        Args:
            total: 总任务数
            width: 进度条宽度
            prefix: 前缀字符串
            suffix: 后缀字符串
            fill: 填充字符
            empty: 空白字符
        """
        self.total = total
        self.width = width
        self.prefix = prefix
        self.suffix = suffix
        self.fill = fill
        self.empty = empty
        self.current = 0
    
    def update(self, current: int, description: Optional[str] = None) -> None:
        """
        更新进度条
        
        Args:
            current: 当前进度
            description: 描述信息（可选）
        """
        self.current = current
        percent = current / self.total if self.total > 0 else 0
        filled_width = int(self.width * percent)
        empty_width = self.width - filled_width
        
        bar = self.fill * filled_width + self.empty * empty_width
        percent_str = f"{percent * 100:.1f}%"
        
        line = f"\r{self.prefix}|{bar}| {percent_str} {self.suffix}"
        
        if description:
            line += f" - {description}"
        
        sys.stdout.write(line)
        sys.stdout.flush()
    
    def increment(self, description: Optional[str] = None) -> None:
        """
        增加进度
        
        Args:
            description: 描述信息（可选）
        """
        self.update(self.current + 1, description)
    
    def finish(self, message: Optional[str] = None) -> None:
        """
        完成进度条
        
        Args:
            message: 完成消息（可选）
        """
        self.update(self.total)
        sys.stdout.write("\n")
        
        if message:
            print(message)


def create_progress_bar(
    total: int,
    description: str = "Processing",
) -> ProgressBar:
    """
    创建进度条
    
    Args:
        total: 总任务数
        description: 描述信息
        
    Returns:
        进度条对象
    """
    return ProgressBar(
        total=total,
        prefix=f"{description}: ",
        suffix=f"({total} items)",
    )


class Spinner:
    """简单的旋转加载动画"""
    
    CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    
    def __init__(self, message: str = "Loading"):
        """
        初始化旋转动画
        
        Args:
            message: 显示消息
        """
        self.message = message
        self.current = 0
    
    def update(self) -> None:
        """更新旋转动画"""
        char = self.CHARS[self.current % len(self.CHARS)]
        sys.stdout.write(f"\r{char} {self.message}...")
        sys.stdout.flush()
        self.current += 1
    
    def finish(self, message: Optional[str] = None) -> None:
        """
        完成旋转动画
        
        Args:
            message: 完成消息（可选）
        """
        sys.stdout.write("\r")
        sys.stdout.flush()
        
        if message:
            print(f"✓ {message}")
        else:
            print(f"✓ {self.message} completed")


class TaskProgress:
    """任务进度跟踪器"""
    
    def __init__(self, tasks: list[str]):
        """
        初始化任务进度跟踪器
        
        Args:
            tasks: 任务名称列表
        """
        self.tasks = tasks
        self.current_task = 0
        self.completed = []
    
    def start_task(self, task_name: str) -> None:
        """
        开始任务
        
        Args:
            task_name: 任务名称
        """
        print(f"\n▶ {task_name}...")
    
    def complete_task(self, task_name: str, success: bool = True) -> None:
        """
        完成任务
        
        Args:
            task_name: 任务名称
            success: 是否成功
        """
        status = "✓" if success else "✗"
        print(f"  {status} {task_name} {'完成' if success else '失败'}")
        self.completed.append(task_name)
    
    def summary(self) -> None:
        """打印任务摘要"""
        total = len(self.tasks)
        completed = len(self.completed)
        print(f"\n{'='*50}")
        print(f"任务完成: {completed}/{total}")
        print(f"{'='*50}")
