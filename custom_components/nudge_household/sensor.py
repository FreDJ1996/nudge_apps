from datetime import datetime
from xml import dom

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from custom_components.nudgeplatform.const import EnergyElectricDevices, NudgeType
from custom_components.nudgeplatform.nudges import (
    Budget,
    Nudge,
    NudgePeriod,
    get_energy_entities,
    get_own_total_consumtion,
)
from custom_components.nudgeplatform.number import Score
from homeassistant.helpers import entity_registry, device_registry
from homeassistant.const import Platform

from .const import (
    CONF_AUTARKY_GOAL,
    CONF_BUDGET_YEARLY_ELECTRICITY,
    CONF_BUDGET_YEARLY_HEAT,
    CONF_LAST_YEAR_CONSUMED,
    CONF_SIZE_HOUSEHOLD,
    DOMAIN,
    STEP_IDS,
    CONF_NAME_HOUSEHOLD,
    MyConfigEntry,
)


class Autarky(Nudge):
    def __init__(
        self,
        device_info: DeviceInfo,
        nudge_period: NudgePeriod,
        attr_name: str,
        entry_id: str,
        goal: float,
        energy_entities: dict[EnergyElectricDevices, str],
        score_entity: str | None,
        domain: str,
    ) -> None:
        super().__init__(
            device_info=device_info,
            nudge_period=nudge_period,
            attr_name=attr_name,
            entry_id=entry_id,
            goal=goal,
            score_entity=score_entity,
            nudge_type=NudgeType.AUTARKY_GOAL,
            domain=domain,
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    yearly_goal = config_entry.data.get(CONF_LAST_YEAR_CONSUMED, 0)
    number_of_persons = config_entry.data.get(CONF_SIZE_HOUSEHOLD, {""})
    name_household = config_entry.data.get(CONF_NAME_HOUSEHOLD, "")
    energy_entities, gas, water = await get_energy_entities(hass=hass)

    entities = []
    er = entity_registry.async_get(hass)
    score_device_unique_ids = config_entry.runtime_data.score_device_unique_ids
    nudge_type_score_entity_ids: dict[NudgeType, str | None] = {}
    for nudge_type, unique_id in score_device_unique_ids.items():
        if unique_id:
            nudge_type_score_entity_ids[nudge_type] = er.async_get_entity_id(
                platform=DOMAIN, domain=Platform.NUMBER, unique_id=unique_id
            )

    autarky_goal = config_entry.data.get(CONF_AUTARKY_GOAL)
    if autarky_goal:
        entities.extend(
            create_autarky_device(
                config_entry,
                energy_entities,
                autarky_goal,
                score_entity=nudge_type_score_entity_ids[NudgeType.AUTARKY_GOAL],
            )
        )

    electricity_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_ELECTRICITY)

    if electricity_budget_goal:
        nudge_type = NudgeType.ELECTRICITY_BUDGET
        entities.extend(
            create_budget_device(
                config_entry=config_entry,
                nudge_type=nudge_type,
                energy_entities=energy_entities,
                budget_yearly_goal=electricity_budget_goal,
                score_entity=nudge_type_score_entity_ids[nudge_type],
            )
        )

    heat_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_HEAT)
    if heat_budget_goal and gas:
        nudge_type = NudgeType.HEAT_BUDGET
        entities.extend(
            create_budget_device(
                config_entry=config_entry,
                nudge_type=nudge_type,
                budget_entities={gas},
                budget_yearly_goal=heat_budget_goal,
                score_entity=nudge_type_score_entity_ids[nudge_type],
            )
        )
    water_budget_goal = config_entry.data.get(CONF_BUDGET_YEARLY_HEAT)
    if water_budget_goal and water:
        nudge_type = NudgeType.WATER_BUDGET
        entities.extend(
            create_budget_device(
                config_entry=config_entry,
                nudge_type=nudge_type,
                budget_entities={water},
                budget_yearly_goal=water_budget_goal,
                score_entity=nudge_type_score_entity_ids[nudge_type],
            )
        )

    async_add_entities(entities)


def create_budget_device(
    config_entry: ConfigEntry,
    nudge_type: NudgeType,
    budget_yearly_goal: float,
    score_entity: str | None,
    energy_entities: dict[EnergyElectricDevices, str] | None = None,
    budget_entities: set[str] | None = None,
) -> list[Budget]:
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
            attr_name=f"{config_entry.title}_{nudge_type.name}_{nudge_period.name}",
            energy_entities=energy_entities,
            budget_entities=budget_entities,
            score_entity=score_entity,
            nudge_type=nudge_type,
            domain=DOMAIN,
        )
        for nudge_period in NudgePeriod
    ]
    return budgets


def create_autarky_device(
    config_entry: ConfigEntry,
    energy_entities: dict[EnergyElectricDevices, str],
    autarky_goal: int,
    score_entity: str | None,
) -> list[Autarky]:
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
            attr_name=f"{config_entry.title}_{NudgeType.AUTARKY_GOAL}_{nudge_period.name}",
            entry_id=f"{config_entry.entry_id}_{nudge_medium_type}",
            goal=autarky_goal,
            energy_entities=energy_entities,
            score_entity=score_entity,
            domain=DOMAIN,
        )
        for nudge_period in NudgePeriod
    ]
    return autarky_entities
