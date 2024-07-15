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
    DOMAIN,RANKING_PERSONS
)
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

@callback
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize nudgeplatform config entry."""

    entry_id = config_entry.entry_id
    users: list[str] = config_entry.data.get(RANKING_PERSONS,list(""))
    if(len(users)> 0):
        entities = [Ranking(users,entry_id)]
        async_add_entities(entities)


class Ranking(SensorEntity):
    _attr_should_poll = True

    def __init__(self, user_score_entities: list[str], entry_id: str) -> None:
        self._attr_name = "Ranking"
        self._attr_unique_id = entry_id
        self._attr_native_value = None
        self._user_score_entities = user_score_entities

    def async_update(self) -> None:
        ranking = {}
        for entity_ids in self._user_score_entities:
            state = self.hass.states.get(entity_ids)
            if state:
                try:
                    value = int(state.state)
                    ranking[entity_ids] = value
                except ValueError:
                    pass  # Nicht-numerischen Wert ignorieren

        sorted_ranking = sorted(ranking.items(), key=lambda item: item[1], reverse=True)
        self._attr_native_value = sorted_ranking[0][1] if sorted_ranking else None
        self._attr_extra_state_attributes = dict(sorted_ranking)