"""Platform for sensor integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING
from homeassistant.components.utility_meter.const import (
    DATA_TARIFF_SENSORS,
    DATA_UTILITY,
)
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.components.utility_meter.const import (
    BIMONTHLY,
    DAILY,
    HOURLY,
    MONTHLY,
    QUARTER_HOURLY,
    QUARTERLY,
    WEEKLY,
    YEARLY,
)
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers import (
    entity_registry as er,
)
from homeassistant.helpers import label_registry as lr
from homeassistant.helpers.device_registry import DeviceInfo,DeviceEntryType
from sqlalchemy import false

from .const import (
    CONF_GOAL_TYPE,
    CONF_METER_DELTA_VALUES,
    CONF_METER_NET_CONSUMPTION,
    CONF_METER_OFFSET,
    CONF_METER_PERIODICALLY_RESETTING,
    CONF_METER_TYPE,
    CONF_NUDGE_GOAL,
    CONF_SENSOR_ALWAYS_AVAILABLE,
    CONF_SOURCE_SENSOR,
    CONF_SOURCE_PERSON,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

METER_TYPES = [
    DAILY,
    WEEKLY,
    MONTHLY,
    BIMONTHLY,
    QUARTERLY,
    YEARLY,
]

_LOGGER = logging.getLogger(__name__)

ATTR_SOURCE_ID = "source"
ATTR_STATUS = "status"
ATTR_PERIOD = "meter_period"
ATTR_LAST_PERIOD = "last_period"
ATTR_LAST_VALID_STATE = "last_valid_state"
ATTR_TARIFF = "tariff"

PRECISION = 3
PAUSED = "paused"
COLLECTING = "collecting"


from homeassistant.helpers import device_registry as dr


async def set_device_label(hass, device_id, label_ids:set[str]):
    """Setzt ein Label für ein Gerät in der Device Registry."""
    registry = dr.async_get(hass)
    device = registry.async_get(device_id)
    if device and label_ids:
        registry.async_update_device(device_id, labels=label_ids)
        return True
    return False


# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Powernudge config entry."""
    entry_id = config_entry.entry_id
    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    source_entity_id = er.async_validate_entity_id(
        registry, config_entry.data[CONF_SOURCE_SENSOR]
    )
    device_info = None
    cron_pattern = None
    delta_values = config_entry.data[CONF_METER_DELTA_VALUES]
    meter_offset = timedelta(days=config_entry.data[CONF_METER_OFFSET])
    nudge_goal_year: int = config_entry.data[CONF_NUDGE_GOAL]
    name = config_entry.title
    net_consumption = config_entry.data[CONF_METER_NET_CONSUMPTION]
    periodically_resetting = config_entry.data[CONF_METER_PERIODICALLY_RESETTING]
    sensor_always_available = config_entry.data.get(
        CONF_SENSOR_ALWAYS_AVAILABLE, False
    )
    nudges = []
    label_registry = lr.async_get(hass)

    name_of_person= config_entry.data.get(CONF_SOURCE_PERSON)
    label_ids = set()

    if name_of_person is not None:
        name_of_person = str(name_of_person)
        name_of_person = name_of_person.rsplit(".",1)[1]
        if not (
            label_for_entities := label_registry.async_get_label_by_name(name_of_person)
        ):
            label_for_entities = label_registry.async_create(
                name=name_of_person, color="red"
            )
        label_ids = {label_for_entities.label_id}


    device_info = DeviceInfo(
    identifiers={(DOMAIN,entry_id)},
    entry_type=DeviceEntryType.SERVICE,
    name=name,
)
    params_utility_meter = {
        "cron_pattern": cron_pattern,
        "delta_values": delta_values,
        "meter_offset": meter_offset,
        "meter_type": "",
        "name": name,
        "net_consumption": net_consumption,
        "parent_meter": entry_id,
        "periodically_resetting": periodically_resetting,
        "source_entity": source_entity_id,
        "tariff_entity": None,  # Wert bleibt None
        "tariff": None,  # Wert bleibt None
        "unique_id": "",
        "device_info": device_info,
        "sensor_always_available": sensor_always_available,
    }

    #Calculate Nudge Goals
    nudge_goals =    {
        DAILY: nudge_goal_year/365,
        WEEKLY: nudge_goal_year/52,
        MONTHLY: nudge_goal_year/12,
        BIMONTHLY: nudge_goal_year/26,
        QUARTERLY: nudge_goal_year/4,
        YEARLY: nudge_goal_year
    }


    for meter_type in METER_TYPES:
        params_utility_meter["meter_type"] = meter_type
        params_utility_meter["unique_id"] = f"{entry_id}_{meter_type}"
        params_utility_meter["name"] = f"{name}_{meter_type}"
        nudges.append(
            Nudge(
                label_ids=label_ids,
                nudge_goal=nudge_goals[meter_type],
                params_utility_meter=params_utility_meter,
            )
        )

    await set_device_label(hass,entry_id,label_ids)

    if DATA_UTILITY not in hass.data:
        hass.data[DATA_UTILITY] = {}
    hass.data[DATA_UTILITY][entry_id] = {DATA_TARIFF_SENSORS: nudges}
    async_add_entities(nudges)


class Nudge(UtilityMeterSensor):

    def __init__(
        self, label_ids: set[str], nudge_goal: int, params_utility_meter: dict
    ) -> None:
        super().__init__(**params_utility_meter)
        self._nudge_goal = nudge_goal
        self._person_labels = label_ids

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes of the sensor."""
        return {
            **super().extra_state_attributes,
            CONF_NUDGE_GOAL: self._nudge_goal
        }

    async def async_added_to_hass(self) -> None:
        """
        Run when entity about to be added to hass.

        To be extended by integrations.
        """
        await super().async_added_to_hass()
        registry = er.async_get(self.hass)
        registry.async_update_entity(self.entity_id, labels=self._person_labels)
