import logging
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import EntityRegistry

from .const import CONF_NUDGE_PERSON, SERVICE_ADD_POINTS_FOR_USER

_LOGGER = logging.getLogger(__name__)

@callback
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize nudgeplatform config entry."""
    users: list[NudgePerson] = []

    users.append(NudgePerson(config_entry=config_entry))

    # Register the service
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_ADD_POINTS_FOR_USER,
        {
         vol.Required("points"): cv.positive_int,
        }, "async_add_points_to_user"
    )
    async_add_entities(users)


class NudgePerson(SensorEntity):
    """Nudge Person for Nudging."""

    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__()
        self._attr_unique_id = config_entry.entry_id
        self.username = config_entry.data[CONF_NUDGE_PERSON]
        self._attr_name = self.username
        self._attr_native_value: int = 0

    async def async_add_points_to_user(self, points: int) -> None:
        self._attr_native_value += points
        self.async_write_ha_state()
