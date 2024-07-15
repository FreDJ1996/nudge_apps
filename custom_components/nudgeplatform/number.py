from homeassistant.components.number import (
    RestoreNumber,
    NumberMode
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import EntityCategory


from .const import (
    CONF_NUDGE_PERSON,
    DOMAIN,
)


@callback
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize nudgeplatform config entry."""

    entities = []

    entities.append(
        User(
            entry_id=config_entry.entry_id,
            username=config_entry.data[CONF_NUDGE_PERSON],
        )
    )

    async_add_entities(entities)


class User(RestoreNumber):
    """Nudge Person for Nudging."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "points"
    def __init__(self, entry_id: str, username: str) -> None:
        super().__init__()
        self._attr_unique_id = f"{entry_id}_User"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=username,
        )

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        await super().async_added_to_hass()
        last_number_data = await self.async_get_last_number_data()
        self._attr_native_value = last_number_data.native_value if last_number_data is not None else 0

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if value.is_integer():
            self._attr_native_value = int(value)
            self.async_write_ha_state()
