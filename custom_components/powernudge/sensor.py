"""Platform for sensor integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

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
from homeassistant.helpers.device_registry import DeviceInfo

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
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

METER_TYPES = [
    "none",
    QUARTER_HOURLY,
    HOURLY,
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
        registry, config_entry.options[CONF_SOURCE_SENSOR]
    )

    device_info = None
    cron_pattern = None
    delta_values = config_entry.options[CONF_METER_DELTA_VALUES]
    meter_offset = timedelta(days=config_entry.options[CONF_METER_OFFSET])
    meter_type = config_entry.options[CONF_METER_TYPE]
    nudge_goal: int = config_entry.options[CONF_NUDGE_GOAL]
    nudge_goal_type = config_entry.options[CONF_GOAL_TYPE]
    meter_type = DAILY
    name = config_entry.title
    net_consumption = config_entry.options[CONF_METER_NET_CONSUMPTION]
    periodically_resetting = config_entry.options[CONF_METER_PERIODICALLY_RESETTING]
    sensor_always_available = config_entry.options.get(
        CONF_SENSOR_ALWAYS_AVAILABLE, False
    )

    device_info = DeviceInfo(
        identifiers={("EntryId",entry_id)},
    )

    nudges = []
    label_registry = lr.async_get(hass)
    name_of_label = "test" #config_entry.data.get(CONF_SOURCE_PERSON).__str__()
    #energy_goal = config_entry.data.get(CONF_NUDGE_GOAL)
    #energy_goal_type = config_entry.data.get(CONF_GOAL_TYPE)
    #unique_id = f"{config_entry.entry_id}_{energy_goal_type}"
    label_for_entities = None
    if not (
        label_for_entities := label_registry.async_get_label_by_name(name_of_label)
    ):
        label_for_entities = label_registry.async_create(
            name=name_of_label, color="red"
        )
    label_ids = {label_for_entities.label_id}

    params_utility_meter = {
        "cron_pattern": cron_pattern,
        "delta_values": delta_values,
        "meter_offset": meter_offset,
        "meter_type": meter_type,
        "name": name,
        "net_consumption": net_consumption,
        "parent_meter": entry_id,
        "periodically_resetting": periodically_resetting,
        "source_entity": source_entity_id,
        "tariff_entity": None,  # Wert bleibt None
        "tariff": None,  # Wert bleibt None
        "unique_id": entry_id,
        "device_info": device_info,
        "sensor_always_available": sensor_always_available,
    }
    nudges.append(
        Nudge(
            label_ids=label_ids,
            nudge_goal=nudge_goal,
            nudge_goal_type=nudge_goal_type,
            kwargs=params_utility_meter,
        )
    )

    async_add_entities(nudges)


class Nudge(UtilityMeterSensor):
    _attr_should_poll = False

    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(
        self, label_ids: set[str], nudge_goal: int, nudge_goal_type: str, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._attr_name = "Power"
        self._attr_extra_state_attributes = {
            CONF_NUDGE_GOAL: nudge_goal,
            CONF_GOAL_TYPE: nudge_goal_type,
        }
        self.person_labels = label_ids

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    async def async_added_to_hass(self) -> None:
        """
        Run when entity about to be added to hass.

        To be extended by integrations.
        """
        registry = er.async_get(self.hass)
        registry.async_update_entity(self.entity_id, labels=self.person_labels)

    async def async_will_remove_from_hass(self) -> None:
        """
        Run when entity will be removed from hass.

        To be extended by integrations.
        """

    @callback
    def async_registry_entry_updated(self) -> None:
        """
        Run when the entity registry entry has been updated.

        To be extended by integrations.
        """

    async def async_removed_from_registry(self) -> None:
        """
        Run when entity has been removed from entity registry.

        To be extended by integrations.
        """
