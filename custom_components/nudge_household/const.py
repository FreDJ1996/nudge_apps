"""Constants."""

from custom_components.nudgeplatform.const import NudgeType
from homeassistant.config_entries import ConfigEntry
from dataclasses import dataclass

DOMAIN = "nudge_household"
CONF_SIZE_HOUSEHOLD = "number_persons"
CONF_ENERGIE_EFFICIENCY = "final_energy_consumption"
CONF_APARTMENT_SIZE = "apartment_size"
CONF_E_Charger = "e_charger"
CONF_HEAT_PUMP = "heat_pump"
CONF_LAST_YEAR_CONSUMED = "last_year_consumed"
CONF_HEAT_SOURCE = "heat_source"
CONF_TITLE = "Nudge Household"
CONF_HOUSEHOLD_INFOS = "Household Infos"
CONF_AUTARKY_GOAL = "goal_autarky"
CONF_BUDGET_YEARLY_ELECTRICITY = "budget_yearly_electricity"
CONF_BUDGET_YEARLY_HEAT = "budget_yearly_heat"
CONF_NAME_HOUSEHOLD = "name_household"

CONF_HEAT_OPTIONS = [
    "Gas",
    "Elektrisch mit eigenem Sensor",
    "Kein Gas oder elektrisch ohne Sensor",
]

STEP_IDS = {
    NudgeType.ELECTRICITY_BUDGET: "electricity",
    NudgeType.AUTARKY_GOAL: "autarky",
    NudgeType.HEAT_BUDGET: "heat",
    NudgeType.WATER_BUDGET: "water",
    NudgeType.MONEY_BUDGET: "money",
    NudgeType.CO2_BUDGET: "CO2",
}

type MyConfigEntry = ConfigEntry[MyData]


@dataclass
class MyData:
    score_device_unique_ids: dict[NudgeType, str | None]
