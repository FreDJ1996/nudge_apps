from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
)
from homeassistant.helpers import (
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.nudgeplatform.const import (
    CONF_BUDGET_YEARLY,
    CONF_NUDGE_PERSON,
    CONF_TRACKED_SENSOR_ENTITIES,
    NudgeType,
    DOMAIN as NUDGE_PLATFORM_DOMAIN
)
from custom_components.nudgeplatform.nudges import Budget, NudgePeriod


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entry_id = config_entry.entry_id
    yearly_goal = config_entry.data.get(CONF_BUDGET_YEARLY, 0)
    entity_id_user = config_entry.data.get(CONF_NUDGE_PERSON, "")
    budget_entities = config_entry.data.get(CONF_TRACKED_SENSOR_ENTITIES, {""})

    start = entity_id_user.find(".") + 1
    end = entity_id_user.find(
        "_", start
    )
    name_user = entity_id_user[start:end]
    name_user = name_user.capitalize()
    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    source_entity_id = er.async_validate_entity_id(registry, entity_id_user)

    source_entity = registry.async_get(source_entity_id)
    dev_reg = dr.async_get(hass)
    # Resolve source entity device
    if (
        (source_entity is not None)
        and (source_entity.device_id is not None)
        and (
            (
                device := dev_reg.async_get(
                    device_id=source_entity.device_id,
                )
            )
            is not None
        )
    ):
        device_info = DeviceInfo(identifiers=device.identifiers)


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
            domain=NUDGE_PLATFORM_DOMAIN
        )
        for budget_type in NudgePeriod
    ]

    async_add_entities(entities)
