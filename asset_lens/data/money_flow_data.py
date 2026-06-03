from dataclasses import dataclass
from typing import Any


@dataclass
class MoneyFlowData:
    code: str
    date: str = ""
    main_net_inflow: float = 0.0
    main_net_inflow_ratio: float = 0.0
    retail_net_inflow: float = 0.0
    retail_net_inflow_ratio: float = 0.0
    super_net_inflow: float = 0.0
    super_net_inflow_ratio: float = 0.0
    big_net_inflow: float = 0.0
    big_net_inflow_ratio: float = 0.0
    medium_net_inflow: float = 0.0
    medium_net_inflow_ratio: float = 0.0
    small_net_inflow: float = 0.0
    small_net_inflow_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "date": self.date,
            "main_net_inflow": self.main_net_inflow,
            "main_net_inflow_ratio": self.main_net_inflow_ratio,
            "retail_net_inflow": self.retail_net_inflow,
            "retail_net_inflow_ratio": self.retail_net_inflow_ratio,
            "super_net_inflow": self.super_net_inflow,
            "super_net_inflow_ratio": self.super_net_inflow_ratio,
            "big_net_inflow": self.big_net_inflow,
            "big_net_inflow_ratio": self.big_net_inflow_ratio,
            "medium_net_inflow": self.medium_net_inflow,
            "medium_net_inflow_ratio": self.medium_net_inflow_ratio,
            "small_net_inflow": self.small_net_inflow,
            "small_net_inflow_ratio": self.small_net_inflow_ratio,
        }
