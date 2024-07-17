from .const import CONF_LAST_YEAR_CONSUMED, CONF_NUMBER_OF_PERSONS, DOMAIN
import homeassistant.components.energy.data as energydata

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
)
from homeassistant.helpers import (
    entity_platform,
)
from homeassistant.helpers import (
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.nudgeplatform.budget import Budget, BudgetType


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

    energy_manager = await energydata.async_get_manager(hass)
    budget_entities = set()

    energy_manager_data: energydata.EnergyPreferences|None = energy_manager.data

    if energy_manager_data is not None:
        energy_sources: list[energydata.SourceType] = energy_manager_data["energy_sources"]
        for source in energy_sources:
            if source["type"] == "grid":
               budget_entities.add(source["flow_from"][0]["stat_energy_from"])


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