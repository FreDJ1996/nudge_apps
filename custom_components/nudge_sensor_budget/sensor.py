from custom_components.nudgeplatform.sensor import Budget
from custom_components.nudgeplatform.const import CONF_BUDGET_YEARLY,CONF_NUDGE_PERSON,CONF_TRACKED_SENSOR_ENTITIES

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceInfo


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entry_id = config_entry.entry_id
    yearly_goal = config_entry.data.get(CONF_BUDGET_YEARLY,0)
    entity_id_user = config_entry.data.get(CONF_NUDGE_PERSON, "")
    budget_entities = config_entry.data.get(CONF_TRACKED_SENSOR_ENTITIES,{""})

    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    source_entity_id = er.async_validate_entity_id(
        registry, entity_id_user
    )

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
        device_info = DeviceInfo(
            identifiers=device.identifiers
        )
    else:
        device_info = None

    async_add_entities({Budget(entry_id=entry_id, yearly_goal=yearly_goal,entity_id_user=entity_id_user,budget_entities=budget_entities,attr_name=config_entry.title,device_info=device_info)})