from enum import Enum, auto
import enum
import logging
from typing import TYPE_CHECKING, Dict, Final
from zoneinfo import ZoneInfo

from pytz import UTC
import pytz
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
    SERVICE_ADD_POINTS_FOR_USER,
    DOMAIN,CONF_BUDGET_YEARLY,CONF_NUDGE_PERSON,CONF_TRACKED_SENSOR_ENTITIES,
)
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.util import dt as dt_util


_LOGGER = logging.getLogger(__name__)

BADGES = [
    "Sparfuchs",
    "Energiespar-Anfänger",
    "Energieeffizienz-Experte",
    "Nachhaltigkeits-Champion",
]


@callback
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize nudgeplatform config entry."""
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))
    entities = []

    entities.append(
        User(
            entry_id=config_entry.entry_id,
            username=config_entry.data[CONF_NUDGE_PERSON],
        )
    )

    entry_id = config_entry.entry_id
    yearly_goal = config_entry.options.get(CONF_BUDGET_YEARLY)
    entity_id_user = config_entry.options.get(CONF_NUDGE_PERSON)
    budget_entities = config_entry.options.get(CONF_TRACKED_SENSOR_ENTITIES)

    if entry_id is not None and yearly_goal is not None and entity_id_user is not None and budget_entities is not None:

        budget_goals = Budget.calculate_goals(yearly_goal=yearly_goal)

        device_info= DeviceInfo(identifiers={(DOMAIN, entry_id)})

        budgets = [
            Budget(
                entry_id=config_entry.entry_id,
                goal=budget_goals[budget_type],
                entity_id_user=entity_id_user,
                budget_entities=budget_entities,
                attr_name=f"{budget_type.name}_{config_entry.title}",
                device_info=device_info,
                budget_type=budget_type,
            )
            for budget_type in BudgetType
        ]

        entities.append(budgets)


    # Register the service
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_ADD_POINTS_FOR_USER,
        {
            vol.Required("points"): cv.positive_int,
        },
        "async_add_points_to_user",
    )

    async_add_entities(entities)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class BudgetType(Enum):
    Daily = auto()
    Weekly = auto()
    Monthly = auto()
    Yearly = auto()


STATISTIC_PERIODS = {
    BudgetType.Daily: "day",
    BudgetType.Weekly: "week",
    BudgetType.Monthly: "month",
    BudgetType.Yearly: "month",
}


class NudgeType(Enum):
    Energy = "mdi:lightning-bolt"


class Budget(SensorEntity):
    """Nudget For Person"""

    _attr_state_class = SensorStateClass.MEASUREMENT

    @staticmethod
    def calculate_goals(yearly_goal: float) -> dict[BudgetType, float]:
        goals = {BudgetType.Yearly: yearly_goal}
        goals[BudgetType.Daily] = yearly_goal / 365
        goals[BudgetType.Weekly] = goals[BudgetType.Daily] * 7
        goals[BudgetType.Monthly] = goals[BudgetType.Yearly] / 12

        return goals

    def get_start_time(self) -> datetime:
        now = dt_util.now()
        if self._budget_type == BudgetType.Daily:
            start_time = now
        if self._budget_type == BudgetType.Weekly:
            start_time = now - timedelta(
                days=now.weekday()
            )  # Zurück zum Wochenanfang (Montag)
        elif self._budget_type == BudgetType.Monthly:
            start_time = now
            start_time.replace(day=1)
        elif self._budget_type == BudgetType.Yearly:
            start_time = now
            start_time.replace(day=1, month=1)

        return start_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        )  # Zeit auf 00:00 Uhr setzen

    def __init__(
        self,
        entry_id: str,
        goal: float,
        entity_id_user: str,
        budget_entities: set[str],
        attr_name: str,
        device_info: DeviceInfo | None,
        budget_type: BudgetType,
        show_actual: bool = False,
    ) -> None:
        super().__init__()
        self._attr_unique_id = f"{entry_id}_{budget_type.name}"
        self._budget_type = budget_type
        self._show_actual = show_actual
        self._attr_name = attr_name
        self._goal = goal
        self._attr_icon = NudgeType.Energy.value
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
        # Regelmäßig die Statistiken der Entities ziehen
        async_track_time_interval(self.hass, self.update_actual, timedelta(seconds=10))

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

    @callback
    async def update_actual(self, now: datetime) -> None:
        statistic_ids = self._budget_entities
        period = STATISTIC_PERIODS[self._budget_type]
        start_time = self.get_start_time()
        end_time = None
        units = None

        type: Final = "change"
        stats = await get_instance(hass=self.hass).async_add_executor_job(
            statistics_during_period,
            self.hass,
            start_time,
            end_time,
            statistic_ids,
            period,
            units,
            {type},
        )
        sum_budget = 0.0
        for entity in stats.values():
            for stat in entity:
                sum_value = stat.get(type)
                if sum_value is not None:
                    sum_budget += sum_value
        self._actual = sum_budget
        self._attr_native_value = round(self._actual / self._goal * 100)
        self._last_update = datetime.now(tz=dt_util.DEFAULT_TIME_ZONE)
        self.async_write_ha_state()

    @callback
    async def send_points_to_user(self, now: datetime) -> None:
        points = -1 if self._actual > self._goal else 1
        await self.hass.services.async_call(
            domain=DOMAIN,
            service="add_points_to_user",
            service_data={"points": points},
            target={"entity_id": self._user_entity_id},
        )


class User(SensorEntity):
    """Nudge Person for Nudging."""

    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, entry_id: str, username: str) -> None:
        super().__init__()
        self._attr_unique_id = f"{entry_id}_User"
        self.username = username
        self._attr_name = self.username
        self._attr_native_value: int = 0
        self.badges: list[str] = []
        self.level: int = 0
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=self.username,
        )

    async def async_add_points_to_user(self, points: int) -> None:
        self._attr_native_value += points
        self.async_write_ha_state()

    async def async_add_badge_to_user(self, badge: str) -> None:
        self.badges.append(badge)

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes of the sensor."""
        return {"badges": self.badges}
