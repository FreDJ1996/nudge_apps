"""Constants for nudgeplatform."""

from enum import Enum, auto

DOMAIN = "nudgeplatform"

CONF_CHOOSE_ACTION = "action"

CONF_NUDGE_PERSON = "username"
CONF_BUDGET_YEARLY = "budget_yearly"
CONF_TRACKED_SENSOR_ENTITIES = "sensor_entities"
SERVICE_SET_RANK_FOR_USER = "set_rank_for_user"
SERVICE_ADD_POINTS_TO_USER = "add_points_to_score"
SERVICE_UPDATE_STREAK = "update_streak"

BADGES = [
    "Sparfuchs",
    "Energiespar-Anfänger",
    "Energieeffizienz-Experte",
    "Nachhaltigkeits-Champion",
]


class NudgeType(Enum):
    ELECTRICITY_BUDGET = auto()
    HEAT_BUDGET = auto()
    WATER_BUDGET = auto()
    AUTARKY_GOAL = auto()
    E_MOBILITY_Budget = auto()
    CO2_BUDGET = auto()
    MONEY_BUDGET = auto()


NUDGE_ICONS = {
    NudgeType.ELECTRICITY_BUDGET: "mdi:lightning-bolt",
    NudgeType.HEAT_BUDGET: "mdi:lightning-bolt",
    NudgeType.WATER_BUDGET: "mdi:lightning-bolt",
    NudgeType.AUTARKY_GOAL: "mdi:lightning-bolt",
    NudgeType.CO2_BUDGET: "mdi:lightning-bolt",
    NudgeType.MONEY_BUDGET: "mdi:lightning-bolt",
}


class NudgePeriod(Enum):
    Daily = auto()
    Weekly = auto()
    Monthly = auto()
    Yearly = auto()


class EnergyElectricDevices(Enum):
    BATTERY_EXPORT = auto()
    BatteryImport = auto()
    SolarProduction = auto()
    GridExport = auto()
    GridImport = auto()
    HeatPump = auto()
    ECharger = auto()
