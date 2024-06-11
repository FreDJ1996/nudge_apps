"""Constants for powernudge."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "powernudge"
CONF_SOURCE_SENSOR = "source"
CONF_SOURCE_PERSON = "person"
CONF_NUDGE_GOAL = "goal"
CONF_GOAL_TYPE = "goal_type"

CONF_METER = "meter"
CONF_SOURCE_SENSOR = "source"
CONF_METER_TYPE = "cycle"
CONF_METER_OFFSET = "offset"
CONF_METER_DELTA_VALUES = "delta_values"
CONF_METER_NET_CONSUMPTION = "net_consumption"
CONF_METER_PERIODICALLY_RESETTING = "periodically_resetting"
CONF_PAUSED = "paused"
CONF_TARIFFS = "tariffs"
CONF_TARIFF = "tariff"
CONF_TARIFF_ENTITY = "tariff_entity"
CONF_CRON_PATTERN = "cron"
CONF_SENSOR_ALWAYS_AVAILABLE = "always_available"
