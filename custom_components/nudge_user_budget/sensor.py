from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
)
from homeassistant.helpers import entity_registry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import Platform
from custom_components.nudge_household.platform import (
    CONF_BUDGET_YEARLY,
    CONF_NUDGE_PERSON,
    CONF_TRACKED_SENSOR_ENTITIES,
    NudgeType,
)

from .const import DOMAIN, MyConfigEntry,CONF_BUDGET_ELECTRICITY_REDUCTION_GOAL

from custom_components.nudge_household.platform import Budget, NudgePeriod


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entry_id = config_entry.entry_id
    yearly_goal = config_entry.data.get(CONF_BUDGET_YEARLY, 0)
    name_user = config_entry.data.get(CONF_NUDGE_PERSON, "")
    budget_entities = config_entry.data.get(CONF_TRACKED_SENSOR_ENTITIES, {""})
    reduction_goal = config_entry.data.get(CONF_BUDGET_ELECTRICITY_REDUCTION_GOAL,0)

    score_device_unique_id = config_entry.runtime_data.score_device_unique_id

    er = entity_registry.async_get(hass)

    entity_id_user = er.async_get_entity_id(
    platform=DOMAIN,
    domain=Platform.NUMBER,
    unique_id=score_device_unique_id,
    )

    device_info = config_entry.runtime_data.device_info

    budget_goals = Budget.calculate_goals(yearly_goal=yearly_goal)
    entities = [
        Budget(
            entry_id=entry_id,
            goal=budget_goals[budget_type],
            score_entity=entity_id_user,
            budget_entities=budget_entities,
            attr_name=f"{name_user} {budget_type.name}",
            device_info=device_info,
            nudge_period=budget_type,
            nudge_type=NudgeType.ELECTRICITY_BUDGET,
            domain=DOMAIN,
            reduction_goal=reduction_goal
        )
        for budget_type in NudgePeriod
    ]

    async_add_entities(entities)
