from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.nudge_household.platform import (
    CONF_NUDGE_PERSON,
    NudgeType,
    Score,
    Streak,
    register_services,
)

from .const import DOMAIN, MyConfigEntry


@callback
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
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

    streak = Streak(
        NudgeType.ELECTRICITY_BUDGET,
        entry_id=config_entry.entry_id,
        device_info=device_info,
    )
    entities.append(streak)

    score = Score(
            entry_id=config_entry.entry_id,
            device_info=device_info,
            nudge_type=NudgeType.ELECTRICITY_BUDGET,
            streak=streak,
            domain=DOMAIN
        )

    entities.append(score)

    register_services()

    config_entry.runtime_data.score_device_unique_id = score.get_unique_id()
    config_entry.runtime_data.device_info = device_info
    async_add_entities(entities)




