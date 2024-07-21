"""Constants for nudgeplatform."""

from enum import Enum, auto

DOMAIN = "nudgeplatform"

CONF_CHOOSE_ACTION = "action"

CONF_NUDGE_PERSON = "username"
CONF_BUDGET_YEARLY = "budget_yearly"
CONF_TRACKED_SENSOR_ENTITIES = "sensor_entities"
SERVICE_SET_RANK_FOR_USER = "set_rank_for_user"

BADGES = [
    "Sparfuchs",
    "Energiespar-Anfänger",
    "Energieeffizienz-Experte",
    "Nachhaltigkeits-Champion",
]


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

