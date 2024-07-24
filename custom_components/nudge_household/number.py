from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.hacs import entity
from custom_components.nudgeplatform.const import NudgeType
from custom_components.nudgeplatform.number import Score, register_services

from .const import (
    CONF_NAME_HOUSEHOLD,
    CONF_AUTARKY_GOAL,
    CONF_BUDGET_YEARLY_HEAT,
    CONF_BUDGET_YEARLY_ELECTRICITY,
    DOMAIN,
    MyConfigEntry,
)


@callback
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize nudgeplatform config entry."""
    entities = []
    name_household = config_entry.data.get(CONF_NAME_HOUSEHOLD, "")

    score_device_unique_ids: dict[NudgeType, str | None] = {}

    identifier = (f"{DOMAIN}_score", config_entry.entry_id)
    device_info = DeviceInfo(
        identifiers={identifier},
        entry_type=DeviceEntryType.SERVICE,
        name="Household Scoreboard",
        translation_key="household_scoreboard",
    )
    entry_id = config_entry.entry_id

    autarky_goal = config_entry.data.get(CONF_AUTARKY_GOAL)
    if autarky_goal:
        nudge_type = NudgeType.AUTARKY_GOAL
        entity = HousholdScore(
            entry_id=entry_id,
            name=name_household,
            nudge_type=nudge_type,
            device_info=device_info,
        )
        score_device_unique_ids[nudge_type] = entity.get_unique_id()

        entities.append(entity)

    electricity_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_ELECTRICITY)
    if electricity_budget_goal:
        nudge_type = NudgeType.ELECTRICITY_BUDGET
        entity = HousholdScore(
            entry_id=entry_id,
            name=name_household,
            nudge_type=nudge_type,
            device_info=device_info,
        )
        score_device_unique_ids[nudge_type] = entity.get_unique_id()
        entities.append(entity)

    heat_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_HEAT)
    if heat_budget_goal:
        nudge_type = NudgeType.HEAT_BUDGET
        entity = HousholdScore(
            entry_id=entry_id,
            name=name_household,
            nudge_type=nudge_type,
            device_info=device_info,
        )
        entities.append(entity)
        score_device_unique_ids[nudge_type] = entity.get_unique_id()
        entities.append(entity)

    water_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_HEAT)
    if water_budget_goal:
        nudge_type = NudgeType.WATER_BUDGET
        entity = HousholdScore(
            entry_id=entry_id,
            name=name_household,
            nudge_type=nudge_type,
            device_info=device_info,
        )
        entities.append(entity)
        score_device_unique_ids[nudge_type] = entity.get_unique_id()
        entities.append(entity)

    register_services()

    config_entry.runtime_data.score_device_unique_ids = score_device_unique_ids

    async_add_entities(entities)


class HousholdScore(Score):
    def __init__(
        self,
        entry_id: str,
        nudge_type: NudgeType,
        name: str,
        device_info: DeviceInfo | None = None,
    ) -> None:
        super().__init__(nudge_type=nudge_type, device_info=device_info)
        self._attr_name = f"{nudge_type.name}_{name}"
        self._attr_unique_id = f"{entry_id}_household_{nudge_type.name}"
