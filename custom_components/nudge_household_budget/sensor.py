from custom_components.nudgeplatform.sensor import Budget,BudgetType
from const import CONF_LAST_YEAR_CONSUMED,CONF_NUMBER_OF_PERSONS, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)
from homeassistant.components.energy.sensor import async_get_manager
from homeassistant.helpers.device_registry import DeviceInfo,DeviceEntryType


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entry_id = config_entry.entry_id
    yearly_goal = config_entry.data.get(CONF_LAST_YEAR_CONSUMED,0)
    number_of_persons = config_entry.data.get(CONF_NUMBER_OF_PERSONS,{""})

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry_id)}, entry_type=DeviceEntryType.SERVICE
    ,name="Nudge Household")

    energy_manager = await async_get_manager(hass)

    energy_manager_data = energy_manager.data

    if energy_manager_data is not None:
        budget_entities = energy_manager_data.get("")
        
    budget_entities = set()


    budget_goals = Budget.calculate_goals(yearly_goal=yearly_goal)
    budgets = [
        Budget(
            entry_id=entry_id,
            goal=budget_goals[budget_type],
            budget_entities=budget_entities,
            attr_name=f"{budget_type.name}_{config_entry.title}" ,
            device_info=device_info,
            budget_type=budget_type
        ) for budget_type in BudgetType
    ]

    async_add_entities(budgets)