from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from typing import TYPE_CHECKING
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor.const import SensorStateClass

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize nudgeplatform config entry."""
    users: list[NudgePerson] = []

    users.append(NudgePerson(config_entry=config_entry))

    async_add_entities(users)



class NudgePerson(SensorEntity):

    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__()
        self._attr_unique_id = config_entry.entry_id
        self.username = config_entry.data["username"]
        self._attr_name = self.username
        self._attr_native_value = 0
