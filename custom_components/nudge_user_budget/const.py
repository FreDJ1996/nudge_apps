"""Constants."""

DOMAIN = "nudge_user_budget"
from homeassistant.config_entries import ConfigEntry
from dataclasses import dataclass
from homeassistant.helpers.device_registry import DeviceInfo

type MyConfigEntry = ConfigEntry[MyData]

CONF_BUDGET_YEARLY_ELECTRICITY = "budget_yearly_electricity"
CONF_BUDGET_ELECTRICITY_REDUCTION_GOAL = "budget_electricity_reduction_goal"


@dataclass
class MyData:
    score_device_unique_id: str
    device_info: DeviceInfo
