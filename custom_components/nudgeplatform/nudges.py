from enum import Enum, auto
import enum
import logging
from typing import TYPE_CHECKING, Dict, Final, List
from zoneinfo import ZoneInfo

from numpy import integer
from pytz import UTC
import pytz
from sqlalchemy import true
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.helpers.event import (
    async_track_time_interval,
    async_track_time_change,
)
from datetime import date, datetime, timedelta
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.components.recorder.util import get_instance
from .const import (
    CONF_BUDGET_YEARLY,
    CONF_NUDGE_PERSON,
    DOMAIN,
    CONF_BUDGET_YEARLY,
    CONF_NUDGE_PERSON,
    CONF_TRACKED_SENSOR_ENTITIES,
    NudgePeriod,
)
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.util import dt as dt_util
from .number import User
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)


STATISTIC_PERIODS = {
    NudgePeriod.Daily: "day",
    NudgePeriod.Weekly: "week",
    NudgePeriod.Monthly: "month",
    NudgePeriod.Yearly: "month",
}


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


class Goal(SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = True

    def __init__(
        self,
        entry_id: str,
        device_info: DeviceInfo,
        attr_name: str,
        nudge_period: NudgePeriod,
    ) -> None:
        super().__init__()
        self._attr_unique_id = f"{entry_id}_{nudge_period.name}"
        self._attr_native_value = 0
        self._attr_native_unit_of_measurement = "%"
        self._nudge_period = nudge_period
        self._attr_name = attr_name
        self._attr_device_info = device_info
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
        budget_entities: set[str],
        attr_name: str,
        device_info: DeviceInfo | None,
        budget_type: NudgePeriod,
        entity_id_user: str = "",
        show_actual: bool = False,
    ) -> None:
        super().__init__()
        self._attr_unique_id = f"{entry_id}_{budget_type.name}"
        self._budget_type = budget_type
        self._show_actual = show_actual
        self._attr_name = attr_name
        self._goal = goal
        self._attr_icon = NudgeIcons.Energy.value
        self._actual = 0.0
        self._user_entity_id = entity_id_user
        self._budget_entities = budget_entities
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
        if self._show_actual:
            attributes["attribute"] = "actual"
            attributes["unit_of_measurement"] = "kWh"
            attributes["max"] = self._goal

        return attributes

    async def async_update(self) -> None:
        statistic_ids = self._budget_entities
        period = STATISTIC_PERIODS[self._budget_type]
        start_time = get_start_time(self._budget_type)
        end_time = None
        units = None

        type_statistic: Final = "change"
        stats = await get_instance(hass=self.hass).async_add_executor_job(
            statistics_during_period,
            self.hass,
            start_time,
            end_time,
            statistic_ids,
            period,
            units,
            {type_statistic},
        )
        sum_budget = 0.0
        for entity in stats.values():
            for stat in entity:
                sum_value = stat.get(type_statistic)
                if sum_value is not None:
                    sum_budget += sum_value
        self._actual = sum_budget
        self._attr_native_value = round(self._actual / self._goal * 100)
        self._last_update = datetime.now(tz=dt_util.DEFAULT_TIME_ZONE)
        self.async_write_ha_state()

    @callback
    async def send_points_to_user(self, now: datetime) -> None:
        if self._user_entity_id == "":
            return
        points = -1 if self._actual > self._goal else 1
        await self.hass.services.async_call(
            domain=DOMAIN,
            service="add_points_to_user",
            service_data={"points": points},
            target={"entity_id": self._user_entity_id},
        )
