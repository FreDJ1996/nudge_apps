from homeassistant.components.number import RestoreNumber, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import EntityCategory
from homeassistant.helpers import entity_platform
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    CONF_NUDGE_PERSON,
    DOMAIN,
    SERVICE_SET_RANK_FOR_USER,
    SERVICE_ADD_POINTS_TO_USER,
    NudgeType,
)


def register_services() -> None:
    # Register the service
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_RANK_FOR_USER,
        {
            vol.Required("ranking_position"): cv.positive_int,
            vol.Required("ranking_length"): cv.positive_int,
        },
        "set_ranking_position",
    )
    platform.async_register_entity_service(
        SERVICE_ADD_POINTS_TO_USER,
        {
            vol.Required("points"): cv.positive_int,
        },
        SERVICE_ADD_POINTS_TO_USER,
    )


@callback
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize nudgeplatform config entry."""

    entities = []
    name = config_entry.data[CONF_NUDGE_PERSON]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        entry_type=DeviceEntryType.SERVICE,
        name=name,
    )

    entities.append(
        User(
            entry_id=config_entry.entry_id,
            device_info=device_info,
            nudge_type=NudgeType.ELECTRICITY_BUDGET,
            name=name,
        )
    )
    register_services()
    async_add_entities(entities)


class Score(RestoreNumber):
    """Nudge Person for Nudging."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "points"

    def __init__(
        self,
        nudge_type: NudgeType,
        device_info: DeviceInfo | None = None,
    ) -> None:
        super().__init__()
        self._attr_device_info = device_info
        self.ranking_position = "0/0"
        self._attr_native_value: int = 0
        self._nudge_type = nudge_type

    async def set_ranking_position(
        self, ranking_position: int, ranking_length: int
    ) -> None:
        self.ranking_position = f"{ranking_position}/{ranking_length}"

    async def add_points_to_user(self, points: int) -> None:
        self._attr_native_value += points

    def get_unique_id(self)-> str|None:
        return self._attr_unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes of the sensor."""
        return {"rank": self.ranking_position}

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        last_number_data = await self.async_get_last_number_data()
        if last_number_data and last_number_data.native_value:
            self._attr_native_value = int(last_number_data.native_value)
        else:
            self._attr_native_value = 0

    #async def async_set_native_value(self, value: float) -> None:
    #    """Update the current value."""
    #    if value.is_integer():
    #        self._attr_native_value = int(value)
    #        self.async_write_ha_state()

class User(Score):
    def __init__(
        self,
        entry_id: str,
        nudge_type: NudgeType,
        name: str,
        device_info: DeviceInfo | None = None,
    ) -> None:
        super().__init__(
            nudge_type=nudge_type,
            device_info=device_info,
        )
        self._attr_name = f"user_{name}"
        self._attr_unique_id = entry_id
