from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util
from google.cloud import firestore


from custom_components.nudgeplatform.const import EnergyElectricDevices, NudgeType
from custom_components.nudgeplatform.nudges import (
    Budget,
    Goal,
    NudgePeriod,
    get_energy_entities,
    get_own_total_consumtion,
)

from .const import (
    CONF_AUTARKY_GOAL,
    CONF_BUDGET_YEARLY_ELECTRICITY,
    CONF_BUDGET_YEARLY_HEAT,
    CONF_LAST_YEAR_CONSUMED,
    CONF_NUMBER_OF_PERSONS,
    DOMAIN,
    STEP_IDS,
)

class Autarky(Goal):
    def __init__(
        self,
        device_info: DeviceInfo,
        nudge_period: NudgePeriod,
        attr_name: str,
        entry_id: str,
        goal: float,
        energy_entities: dict[EnergyElectricDevices, str],
    ) -> None:
        super().__init__(
            device_info=device_info,
            nudge_period=nudge_period,
            attr_name=attr_name,
            entry_id=entry_id,
            goal=goal,
        )
        self._attr_native_value = 0.0
        self._attr_native_unit_of_measurement = "%"
        self.energy_entities = energy_entities

    async def get_autarky(self) -> float:
        own_consumption, total_consumption = await get_own_total_consumtion(
            energy_entities=self.energy_entities,
            period=self._nudge_period,
            hass=self.hass,
        )
        if total_consumption == 0:
            autarky = 0
        else:
            autarky = (own_consumption / total_consumption) * 100
        return autarky

    async def async_update(self) -> None:
        self._last_update = datetime.now(tz=dt_util.DEFAULT_TIME_ZONE)
        self._attr_native_value = await self.get_autarky()
        self.async_write_ha_state()

db = firestore.Client(project="HomeAssistantHouseholdNudge")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    yearly_goal = config_entry.data.get(CONF_LAST_YEAR_CONSUMED, 0)
    number_of_persons = config_entry.data.get(CONF_NUMBER_OF_PERSONS, {""})

    energy_entities, gas, water = await get_energy_entities(hass=hass)

    entities = []
    autarky_goal = config_entry.data.get(CONF_AUTARKY_GOAL)

    if autarky_goal:
        entities.extend(
            create_autarky_device(config_entry, energy_entities, autarky_goal)
        )

    electricity_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_ELECTRICITY)

    if electricity_budget_goal:
        entities.extend(create_budget_device(
                config_entry=config_entry,
                nudge_type=NudgeType.ELECTRICITY_BUDGET,
                energy_entities=energy_entities,
                budget_yearly_goal=electricity_budget_goal,
        ))

    heat_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_HEAT)
    if heat_budget_goal and gas:
        entities.extend(
            create_budget_device(
                config_entry=config_entry,
                nudge_type=NudgeType.HEAT_BUDGET,
                budget_entities={gas},
                budget_yearly_goal=heat_budget_goal,
            )
        )
    water_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_HEAT)
    if water_budget_goal and water:
        entities.extend(
            create_budget_device(
                config_entry=config_entry,
                nudge_type=NudgeType.WATER_BUDGET,
                budget_entities={water},
                budget_yearly_goal=water_budget_goal,
            )
        )

    async_add_entities(entities)


def create_budget_device(
    config_entry: ConfigEntry,
    nudge_type: NudgeType,
    budget_yearly_goal: float,
    energy_entities: dict[EnergyElectricDevices, str] | None = None,
    budget_entities: set[str] | None = None,
)-> list[Budget]:
    nudge_medium_type = STEP_IDS[nudge_type]
    device_info = DeviceInfo(
        identifiers={(f"{DOMAIN}_{nudge_medium_type}", config_entry.entry_id)},
        entry_type=DeviceEntryType.SERVICE,
        name=f"Household {nudge_medium_type}",
        translation_key=f"household_{nudge_medium_type}",
    )
    budget_goals = Budget.calculate_goals(yearly_goal=budget_yearly_goal)

    budgets = [
        Budget(
            entry_id=f"{config_entry.entry_id}_{nudge_medium_type}",
            goal=budget_goals[nudge_period],
            device_info=device_info,
            nudge_period=nudge_period,
            attr_name=f"{nudge_period.name}_{config_entry.title}",
            energy_entities=energy_entities,
            budget_entities=budget_entities,
        )
        for nudge_period in NudgePeriod
    ]
    return budgets


def create_autarky_device(config_entry, energy_entities, autarky_goal)-> list[Autarky]:
    nudge_medium_type = STEP_IDS[NudgeType.AUTARKY_GOAL]
    device_info_autarky = DeviceInfo(
        identifiers={(f"{DOMAIN}_{nudge_medium_type}", config_entry.entry_id)},
        entry_type=DeviceEntryType.SERVICE,
        name=f"Household {nudge_medium_type}",
        translation_key=f"household_{nudge_medium_type}",
    )
    autarky_entities = [
        Autarky(
            device_info=device_info_autarky,
            nudge_period=nudge_period,
            attr_name=f"{nudge_period.name}_{config_entry.title}",
            entry_id=f"{config_entry.entry_id}_{nudge_medium_type}",
            goal=autarky_goal,
            energy_entities=energy_entities,
        )
        for nudge_period in NudgePeriod
    ]
    return autarky_entities



