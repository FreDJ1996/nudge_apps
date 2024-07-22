import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Final

import homeassistant.components.energy.data as energydata
from homeassistant.components.recorder.statistics import (
    statistics_during_period,
)
from homeassistant.components.recorder.util import get_instance
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import (
    async_track_time_change,
)
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    EnergyElectricDevices,
    NudgePeriod,
)

_LOGGER = logging.getLogger(__name__)


class NudgeIcons(Enum):
    Energy = "mdi:lightning-bolt"


def get_start_time(nudge_period: NudgePeriod) -> datetime:
    now = dt_util.now()
    if nudge_period == NudgePeriod.Daily:
        start_time = now
    if nudge_period == NudgePeriod.Weekly:
        start_time = now - timedelta(
            days=now.weekday()
        )  # Zurück zum Wochenanfang (Montag)
    elif nudge_period == NudgePeriod.Monthly:
        start_time = now
        start_time.replace(day=1)
    elif nudge_period == NudgePeriod.Yearly:
        start_time = now
        start_time.replace(day=1, month=1)

    return start_time.replace(
        hour=0, minute=0, second=0, microsecond=0
    )  # Zeit auf 00:00 Uhr setzen


async def get_energy_entities(hass: HomeAssistant) -> tuple[dict[EnergyElectricDevices, str],str|None,str|None]:
    # Autarkiegrad (%) = (Eigenverbrauch (kWh) / Gesamtverbrauch (kWh)) * 100
    # Eigenverbrauch =  Batterie Export-Batterie Import + Solar Produktion - Strom Export
    # Gesamtverbrauch = Eigenverbrauch + Strom Import
    energy_manager = await energydata.async_get_manager(hass)

    energy_manager_data: energydata.EnergyPreferences | None = energy_manager.data
    energy_entities = {}
    gas = None
    water = None
    if energy_manager_data:
        energy_sources = energy_manager_data.get("energy_sources", [])
        for source in energy_sources:
            if source["type"] == "grid":
                grid_imports = source.get("flow_from")
                for grid_import in grid_imports:
                    energy_entities[EnergyElectricDevices.GridImport] = grid_import[
                        "stat_energy_from"
                    ]
                grid_exports = source.get("flow_to")
                for grid_export in grid_exports:
                    energy_entities[EnergyElectricDevices.GridExport] = grid_export[
                        "stat_energy_to"
                    ]
            elif source["type"] == "battery":
                energy_entities[EnergyElectricDevices.BatteryExport] = source.get(
                    "stat_energy_to"
                )
                energy_entities[EnergyElectricDevices.BatteryImport] = source.get(
                    "stat_energy_from"
                )
            elif source["type"] == "solar":
                energy_entities[EnergyElectricDevices.SolarProduction] = source.get(
                    "stat_energy_from"
                )
            elif source["type"] == "gas":
                gas = source.get(
                    "stat_energy_from"
                )
            elif source["type"] == "water":
                water = source.get(
                    "stat_energy_from"
                )
    return energy_entities,gas,water


async def get_long_term_statistics(
    statistic_ids: set[str], period: NudgePeriod, hass: HomeAssistant
) -> dict[str, float]:
    STATISTIC_PERIODS = {
        NudgePeriod.Daily: "day",
        NudgePeriod.Weekly: "week",
        NudgePeriod.Monthly: "month",
        NudgePeriod.Yearly: "month",
    }

    statistic_period = STATISTIC_PERIODS[period]
    start_time = get_start_time(period)
    end_time = None
    units = None

    type_statistic: Final = "change"
    stats = await get_instance(hass=hass).async_add_executor_job(
        statistics_during_period,
        hass,
        start_time,
        end_time,
        statistic_ids,
        statistic_period,
        units,
        {type_statistic},
    )
    sum_budget = 0.0
    for entity in stats.values():
        for stat in entity:
            sum_value = stat.get(type_statistic)
            if sum_value is not None:
                sum_budget += sum_value
    entities_sum = {}
    for entity, values in stats.items():
        sum_entity = 0.0
        for stat in values:
            sum_value = stat.get(type_statistic)
            if sum_value is not None:
                sum_entity += sum_value
        entities_sum[entity] = sum_entity

    return entities_sum


async def get_own_total_consumtion(
    energy_entities: dict[EnergyElectricDevices, str],
    period: NudgePeriod,
    hass: HomeAssistant,
) -> tuple[float, float]:
    statistic_ids = {energy_entity for energy_entity in energy_entities.values()}
    entities_energy = {value: key for key, value in energy_entities.items()}

    stats = await get_long_term_statistics(
        statistic_ids=statistic_ids, period=period, hass=hass
    )
    energy_values = {device: 0.0 for device in EnergyElectricDevices}

    for entity, value in stats.items():
        energy_values[entities_energy[entity]] += value

    # Autarkiegrad (%) = (Eigenverbrauch (kWh) / Gesamtverbrauch (kWh)) * 100
    # Eigenverbrauch =  Batterie Export-Batterie Import + Solar Produktion - Strom Export
    # Gesamtverbrauch = Eigenverbrauch + Strom Import
    own_consumption = (
        energy_values[EnergyElectricDevices.BatteryExport]
        - energy_values[EnergyElectricDevices.BatteryImport]
        + energy_values[EnergyElectricDevices.SolarProduction]
        - energy_values[EnergyElectricDevices.GridExport]
    )
    total_consumption = (
        own_consumption + energy_values[EnergyElectricDevices.GridImport]
    )
    return own_consumption, total_consumption


class Goal(SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = True

    def __init__(
        self,
        entry_id: str,
        device_info: DeviceInfo,
        attr_name: str,
        nudge_period: NudgePeriod,
        goal: float,
    ) -> None:
        super().__init__()
        self._attr_unique_id = f"{entry_id}_{nudge_period.name}"
        self._attr_native_value = 0
        self._attr_native_unit_of_measurement = "%"
        self._nudge_period = nudge_period
        self._attr_name = attr_name
        self._attr_device_info = device_info
        self._goal = goal
        self._last_update = datetime.now(tz=dt_util.DEFAULT_TIME_ZONE)


class Budget(SensorEntity):
    """Nudget For Person"""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = True

    @staticmethod
    def calculate_goals(yearly_goal: float) -> dict[NudgePeriod, float]:
        goals = {NudgePeriod.Yearly: yearly_goal}
        goals[NudgePeriod.Daily] = yearly_goal / 365
        goals[NudgePeriod.Weekly] = goals[NudgePeriod.Daily] * 7
        goals[NudgePeriod.Monthly] = goals[NudgePeriod.Yearly] / 12

        return goals

    def __init__(
        self,
        entry_id: str,
        goal: float,
        attr_name: str,
        device_info: DeviceInfo | None,
        nudge_period: NudgePeriod,
        energy_entities: dict[EnergyElectricDevices, str] | None = None,
        budget_entities: set[str] | None = None,
        entity_id_user: str | None = None,
        show_actual: bool = False,
    ) -> None:
        super().__init__()
        self._attr_unique_id = f"{entry_id}_{nudge_period.name}"
        self._budget_type = nudge_period
        self._show_actual = show_actual
        self._attr_name = attr_name
        self._goal = goal
        self._attr_icon = NudgeIcons.Energy.value
        self._actual = 0.0
        self._user_entity_id = entity_id_user
        self._budget_entities = budget_entities
        self._energy_entities = energy_entities
        self._attr_native_value: int = 0
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_info = device_info
        self._last_update = datetime.now(tz=dt_util.DEFAULT_TIME_ZONE)

    async def async_added_to_hass(self) -> None:
        # Jeden Abend die Punkte aktualisieren
        async_track_time_change(
            self.hass, self.send_points_to_user, hour=23, minute=59, second=59
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes of the sensor."""
        attributes = {}
        attributes["last_update"] = self._last_update
        attributes["actual"] = self._actual
        attributes["goal"] = self._goal
        # TODO
        if self._show_actual:
            attributes["attribute"] = "actual"
            attributes["unit_of_measurement"] = "kWh"
            attributes["max"] = self._goal

        return attributes

    async def async_update(self) -> None:
        sum_budget = 0.0
        if self._budget_entities:
            stats = await get_long_term_statistics(
                self._budget_entities, self._budget_type, self.hass
            )
            for value in stats.values():
                sum_budget += value
        elif self._energy_entities:
            own_consumtion, total_consumtion = await get_own_total_consumtion(
                energy_entities=self._energy_entities,
                period=self._budget_type,
                hass=self.hass,
            )
            sum_budget = own_consumtion

        self._actual = sum_budget
        self._attr_native_value = round(self._actual / self._goal * 100)
        self._last_update = datetime.now(tz=dt_util.DEFAULT_TIME_ZONE)
        self.async_write_ha_state()

    @callback
    async def send_points_to_user(self, now: datetime) -> None:
        if not self._user_entity_id:
            return
        points = -1 if self._actual > self._goal else 1
        await self.hass.services.async_call(
            domain=DOMAIN,
            service="add_points_to_user",
            service_data={"points": points},
            target={"entity_id": self._user_entity_id},
        )
