from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.hacs import entity
from custom_components.nudgeplatform.const import NudgeType
from custom_components.nudgeplatform.number import Score, register_services,TotalScore

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
    score_entities = set()
    name_household = config_entry.data.get(CONF_NAME_HOUSEHOLD, "")

    score_device_unique_ids: dict[NudgeType, str] = {}

    identifier = (f"{DOMAIN}_score", config_entry.entry_id)
    device_info = DeviceInfo(
        identifiers={identifier},
        entry_type=DeviceEntryType.SERVICE,
        name=name_household,
        translation_key="household_scoreboard",
    )

    nudge_types: set[NudgeType]=set()

    autarky_goal = config_entry.data.get(CONF_AUTARKY_GOAL)
    if autarky_goal:
        nudge_types.add(NudgeType.AUTARKY_GOAL)

    electricity_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_ELECTRICITY)
    if electricity_budget_goal:
        nudge_types.add(NudgeType.ELECTRICITY_BUDGET)

    heat_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_HEAT)
    if heat_budget_goal:
        nudge_types.add(NudgeType.HEAT_BUDGET)

    water_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_HEAT)
    if water_budget_goal:
        nudge_types.add(NudgeType.WATER_BUDGET)

    entry_id = config_entry.entry_id
    for nudge_type in nudge_types:
        entity = Score(
            entry_id=entry_id,
            nudge_type=nudge_type,
            device_info=device_info,
        )
        score_device_unique_ids[nudge_type] = entity.get_unique_id()
        score_entities.add(entity)
    register_services()

    config_entry.runtime_data.score_device_unique_ids = score_device_unique_ids

    score_entities.add(TotalScore(entity_uuids_scores=score_device_unique_ids,domain=DOMAIN,device_info=device_info,entry_id=entry_id))

    async_add_entities(score_entities)


