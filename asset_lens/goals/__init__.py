"""
Goals Module - 资产目标与进度追踪
支持设置长期目标并追踪达成进度
"""

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class InvestmentGoal:
    """投资目标"""
    name: str
    target_amount: float
    target_date: str
    owner: str = "personal"
    description: str = ""
    priority: str = "medium"  # low, medium, high
    created_at: str = ""
    current_amount: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d")

    @property
    def progress(self) -> float:
        """计算进度百分比"""
        if self.target_amount <= 0:
            return 0.0
        return min(100.0, (self.current_amount / self.target_amount) * 100)

    @property
    def remaining_amount(self) -> float:
        """剩余金额"""
        return max(0.0, self.target_amount - self.current_amount)

    @property
    def days_remaining(self) -> int:
        """剩余天数"""
        try:
            target = datetime.strptime(self.target_date, "%Y-%m-%d")
            today = datetime.now()
            return max(0, (target - today).days)
        except ValueError:
            return 0

    @property
    def monthly_savings_needed(self) -> float:
        """每月需要储蓄金额"""
        months = max(1, self.days_remaining / 30)
        return self.remaining_amount / months

    @property
    def status(self) -> str:
        """目标状态"""
        if self.progress >= 100:
            return "completed"
        elif self.progress >= 75:
            return "on_track"
        elif self.progress >= 50:
            return "in_progress"
        elif self.days_remaining <= 0:
            return "overdue"
        else:
            return "behind"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "target_amount": self.target_amount,
            "target_date": self.target_date,
            "owner": self.owner,
            "description": self.description,
            "priority": self.priority,
            "created_at": self.created_at,
            "current_amount": self.current_amount,
            "progress": round(self.progress, 2),
            "remaining_amount": self.remaining_amount,
            "days_remaining": self.days_remaining,
            "monthly_savings_needed": round(self.monthly_savings_needed, 2),
            "status": self.status,
        }


class GoalsManager:
    """目标管理器"""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path.home() / ".asset_lens" / "goals.json"
        self._goals: list[InvestmentGoal] = []
        self._load_goals()

    def _load_goals(self) -> None:
        """加载目标配置"""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)

            self._goals = [
                InvestmentGoal(
                    name=g.get("name", ""),
                    target_amount=g.get("target_amount", 0),
                    target_date=g.get("target_date", ""),
                    owner=g.get("owner", "personal"),
                    description=g.get("description", ""),
                    priority=g.get("priority", "medium"),
                    created_at=g.get("created_at", ""),
                    current_amount=g.get("current_amount", 0),
                )
                for g in data.get("goals", [])
            ]
        except Exception:
            self._goals = []

    def _save_goals(self) -> None:
        """保存目标配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "goals": [
                {
                    "name": g.name,
                    "target_amount": g.target_amount,
                    "target_date": g.target_date,
                    "owner": g.owner,
                    "description": g.description,
                    "priority": g.priority,
                    "created_at": g.created_at,
                    "current_amount": g.current_amount,
                }
                for g in self._goals
            ],
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_goal(
        self,
        name: str,
        target_amount: float,
        target_date: str,
        owner: str = "personal",
        description: str = "",
        priority: str = "medium",
    ) -> InvestmentGoal:
        """添加目标"""
        goal = InvestmentGoal(
            name=name,
            target_amount=target_amount,
            target_date=target_date,
            owner=owner,
            description=description,
            priority=priority,
        )
        self._goals.append(goal)
        self._save_goals()
        return goal

    def remove_goal(self, name: str) -> bool:
        """删除目标"""
        for i, goal in enumerate(self._goals):
            if goal.name == name:
                del self._goals[i]
                self._save_goals()
                return True
        return False

    def update_progress(self, name: str, current_amount: float) -> bool:
        """更新目标进度"""
        for goal in self._goals:
            if goal.name == name:
                goal.current_amount = current_amount
                self._save_goals()
                return True
        return False

    def get_goal(self, name: str) -> InvestmentGoal | None:
        """获取目标"""
        for goal in self._goals:
            if goal.name == name:
                return goal
        return None

    def get_goals_by_owner(self, owner: str) -> list[InvestmentGoal]:
        """按所有者获取目标"""
        return [g for g in self._goals if g.owner == owner]

    def get_all_goals(self) -> list[InvestmentGoal]:
        """获取所有目标"""
        return self._goals.copy()

    def get_summary(self) -> dict[str, Any]:
        """获取目标摘要"""
        total_target = sum(g.target_amount for g in self._goals)
        total_current = sum(g.current_amount for g in self._goals)

        by_status: dict[str, int] = {}
        for goal in self._goals:
            status = goal.status
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_goals": len(self._goals),
            "total_target": total_target,
            "total_current": total_current,
            "overall_progress": round((total_current / total_target * 100) if total_target > 0 else 0, 2),
            "by_status": by_status,
            "goals": [g.to_dict() for g in self._goals],
        }

    def update_from_portfolio(self, total_assets: float, owner: str = "personal") -> None:
        """从投资组合更新进度"""
        for goal in self._goals:
            if goal.owner == owner:
                goal.current_amount = total_assets
        self._save_goals()


goals_manager = GoalsManager()


__all__ = [
    "InvestmentGoal",
    "GoalsManager",
    "goals_manager",
]
