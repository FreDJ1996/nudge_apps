"""Constants for nudgeplatform."""

from enum import Enum, auto

DOMAIN = "nudgeplatform"

CONF_CHOOSE_ACTION = "action"

CONF_NUDGE_PERSON = "username"
CONF_BUDGET_YEARLY = "budget_yearly"
CONF_TRACKED_SENSOR_ENTITIES = "sensor_entities"
SERVICE_SET_RANK_FOR_USER = "set_rank_for_user"
SERVICE_ADD_POINTS_TO_USER = "add_points_to_user"

BADGES = [
    "Sparfuchs",
    "Energiespar-Anfänger",
    "Energieeffizienz-Experte",
    "Nachhaltigkeits-Champion",
]

class NudgeIcons(Enum):
    Energy = "mdi:lightning-bolt"


class NudgePeriod(Enum):
    Daily = auto()
    Weekly = auto()
    Monthly = auto()
    Yearly = auto()


class NudgeType(Enum):
    ELECTRICITY_BUDGET = auto()
    HEAT_BUDGET = auto()
    WATER_BUDGET = auto()
    AUTARKY_GOAL = auto()
    CO2_BUDGET = auto()
    MONEY_BUDGET = auto()


class EnergyElectricDevices(Enum):
    BatteryExport = auto()
    BatteryImport = auto()
    SolarProduction = auto()
    GridExport = auto()
    GridImport = auto()


