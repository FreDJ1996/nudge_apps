from datetime import datetime
from typing import Final

from custom_components.nudgeplatform.const import NudgeType
from .const import CONF_LAST_YEAR_CONSUMED, CONF_NUMBER_OF_PERSONS, DOMAIN
import homeassistant.components.energy.data as energydata
from homeassistant.util import dt as dt_util

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

from custom_components.nudgeplatform.nudges import Budget, NudgePeriod
from custom_components.nudgeplatform.nudges import (
    Goal,
    STATISTIC_PERIODS,
    get_start_time,
)
import homeassistant.components.energy.data as energydata
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.components.recorder.util import get_instance
from enum import Enum, auto


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entry_id = config_entry.entry_id
    yearly_goal = config_entry.data.get(CONF_LAST_YEAR_CONSUMED, 0)
    number_of_persons = config_entry.data.get(CONF_NUMBER_OF_PERSONS, {""})

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        entry_type=DeviceEntryType.SERVICE,
        name="Nudge Household",
    )

    autarky_entities = [
        Autarky(
            device_info=device_info,
            nudge_period=NudgePeriod.Daily,
            attr_name=f"{NudgePeriod.Daily}_{config_entry.title}",
            entry_id=config_entry.entry_id
        )
    ]

    #    budget_goals = Budget.calculate_goals(yearly_goal=yearly_goal)
    #    budgets = [
    #        Budget(
    #            entry_id=entry_id,
    #            goal=budget_goals[budget_type],
    #            budget_entities=budget_entities,
    #            attr_name=f"{budget_type.name}_{config_entry.title}",
    #            device_info=device_info,
    #            budget_type=budget_type,
    #        )
    #        for budget_type in NudgePeriod
    #    ]

    async_add_entities(autarky_entities)


class EnergyDevices(Enum):
    BatteryExport = auto()
    BatteryImport = auto()
    SolarProduction = auto()
    GridExport = auto()
    GridImport = auto()


class Autarky(Goal):
    def __init__(
        self, device_info: DeviceInfo, nudge_period: NudgePeriod, attr_name: str, entry_id: str
    ) -> None:
        super().__init__(device_info=device_info, nudge_period=nudge_period,attr_name=attr_name,entry_id=entry_id)
        self._attr_native_value = 0.0
        self._attr_native_unit_of_measurement = "%"
        self._statistic_ids: list[str] = list()
        self.energy_entities = {}
        self.energy_values = {device: 0.0 for device in EnergyDevices}

    async def get_energy_entities(self) -> None:
        # Autarkiegrad (%) = (Eigenverbrauch (kWh) / Gesamtverbrauch (kWh)) * 100
        # Eigenverbrauch =  Batterie Export-Batterie Import + Solar Produktion - Strom Export
        # Gesamtverbrauch = Eigenverbrauch + Strom Import
        energy_manager = await energydata.async_get_manager(self.hass)

        energy_manager_data: energydata.EnergyPreferences | None = energy_manager.data

        if energy_manager_data:
            energy_sources = energy_manager_data.get("energy_sources", [])
            for source in energy_sources:
                if source["type"] == "grid":
                    grid_imports = source.get("flow_from")
                    for grid_import in grid_imports:
                        self.energy_entities[grid_import["stat_energy_from"]] = (
                            EnergyDevices.GridImport
                        )
                        self._statistic_ids.append(grid_import["stat_energy_from"])
                    grid_exports = source.get("flow_to")
                    for grid_export in grid_exports:
                        self.energy_entities[grid_export["stat_energy_to"]] = (
                            EnergyDevices.GridExport
                        )
                        self._statistic_ids.append(grid_export["stat_energy_to"])
                elif source["type"] == "battery":
                    self.energy_entities[source.get("stat_energy_to")] = (
                        EnergyDevices.BatteryExport
                    )

                    self._statistic_ids.append(source.get("stat_energy_to"))
                    self.energy_entities[source.get("stat_energy_from")] = (
                        EnergyDevices.BatteryImport
                    )
                    self._statistic_ids.append(source.get("stat_energy_from"))
                elif source["type"] == "solar":
                    self.energy_entities[source.get("stat_energy_from")] = (
                        EnergyDevices.SolarProduction
                    )
                    self._statistic_ids.append(source.get("stat_energy_from"))


    async def get_statistics(self) -> None:
        period = STATISTIC_PERIODS[self._nudge_period]
        start_time = get_start_time(self._nudge_period)
        end_time = None
        units = None

        type_statistic: Final = "change"
        stats = await get_instance(hass=self.hass).async_add_executor_job(
            statistics_during_period,
            self.hass,
            start_time,
            end_time,
            self._statistic_ids,
            period,
            units,
            {type_statistic},
        )

        self.energy_values = {device: 0.0 for device in EnergyDevices}
        
        for entity, values in stats.items():
            sum_entity = 0.0
            for stat in values:
                sum_value = stat.get(type_statistic)
                if sum_value is not None:
                    sum_entity += sum_value
            self.energy_values[self.energy_entities[entity]] += sum_entity

        # Autarkiegrad (%) = (Eigenverbrauch (kWh) / Gesamtverbrauch (kWh)) * 100
        # Eigenverbrauch =  Batterie Export-Batterie Import + Solar Produktion - Strom Export
        # Gesamtverbrauch = Eigenverbrauch + Strom Import
        own_consumption = (
            self.energy_values[EnergyDevices.BatteryExport]
            - self.energy_values[EnergyDevices.BatteryImport]
            + self.energy_values[EnergyDevices.SolarProduction]
            - self.energy_values[EnergyDevices.GridExport]
        )
        total_consumption = (
            own_consumption + self.energy_values[EnergyDevices.GridImport]
        )
        self._attr_native_value = (own_consumption/total_consumption)*100

    async def async_added_to_hass(self) -> None:
        await self.get_energy_entities()
        await self.get_statistics()

    async def async_update(self) -> None:
        self._last_update = datetime.now(tz=dt_util.DEFAULT_TIME_ZONE)
        await self.get_statistics()

