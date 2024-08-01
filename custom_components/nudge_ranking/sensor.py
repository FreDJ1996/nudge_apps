import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    callback,
    SupportsResponse,
    ServiceResponse,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import (
    DeviceEntryType,
    DeviceInfo,
    async_get as async_get_device_registry,
)
from custom_components.nudge_household.const import DOMAIN_NUDGE_HOUSEHOLD
from custom_components.nudgeplatform.const import (
    DOMAIN as NUDGEPLATFORM_DOMAIN,
)
from custom_components.nudgeplatform.const import (
    SERVICE_SET_RANK_FOR_USER,
)
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from homeassistant.helpers import entity_platform
from .const import RANKING_PERSONS, SERVICE_GET_RANKING_POSITION,DOMAIN

SCAN_INTERVAL = timedelta(minutes=1)

_LOGGER = logging.getLogger(__name__)


def register_services() -> None:
    # Register the service
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_GET_RANKING_POSITION,
        {
            vol.Required("entity_id"): cv.string,
        },
        SERVICE_GET_RANKING_POSITION,
        supports_response=SupportsResponse.ONLY,
    )


@callback
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize nudgeplatform config entry."""
    entry_id = config_entry.entry_id
    users: list[str] = config_entry.data.get(RANKING_PERSONS, list(""))
    if len(users) > 0:
        entities = [RankingScoreboard(users, entry_id)]
        async_add_entities(entities)
        # for user in users


class Ranking(SensorEntity):
    _attr_should_poll = True

    def __init__(
        self,
        user_score_entity: str,
        entry_id: str,
        device_info: DeviceInfo,
        ranking_uuid: str,
    ) -> None:
        self._attr_name = "Ranking Scoreboard"
        self._attr_unique_id = entry_id
        self._attr_native_value = 0
        self._attr_device_info = device_info
        self._user_score_entitiy = user_score_entity
        self.entity_ranking: dict[str, int] = {}
        self.ranking_entity_id = "sensor.ranking"

    async def async_update(self) -> None:
        await self.hass.services.async_call(
            domain=DOMAIN,
            service=SERVICE_GET_RANKING_POSITION,
            service_data={
                "entity_id": self._user_score_entitiy,
            },
            target={"entity_id": self.ranking_entity_id},
        )


class RankingScoreboard(SensorEntity):
    _attr_should_poll = True

    def __init__(self, user_score_entities: list[str], entry_id: str) -> None:
        self._attr_name = "Ranking Scoreboard"
        self._attr_unique_id = entry_id
        self._attr_native_value = None
        self._user_score_entities = user_score_entities
        self.entity_ranking: dict[str, int] = {}

    async def send_rank_to_user(
        self, user_entity_id: str, ranking_position: int, ranking_length: int
    ) -> None:
        await self.hass.services.async_call(
            domain=NUDGEPLATFORM_DOMAIN,
            service=SERVICE_SET_RANK_FOR_USER,
            service_data={
                "ranking_position": ranking_position,
                "ranking_length": ranking_length,
            },
            target={"entity_id": user_entity_id},
        )

    async def get_ranking_position(self, entity_id: str) -> ServiceResponse:
        return {"rank": self.entity_ranking[entity_id]}

    async def async_update(self) -> None:
        ranking = {}
        for entity_id in self._user_score_entities:  # Direkte Iteration über IDs
            state = self.hass.states.get(entity_id)
            if state and state.state.isdigit():  # Direkte Prüfung auf Zahl
                ranking[entity_id] = {
                    "name": state.name.split()[0],
                    "value": int(state.state),
                }

        sorted_ranking = sorted(
            ranking.items(), key=lambda item: item[1]["value"], reverse=True
        )

        if sorted_ranking:
            self._attr_native_value = sorted_ranking[0][1]["value"]

            list_users = []
            for rank, (entity_id, value) in enumerate(sorted_ranking, start=1):
                self.entity_ranking[entity_id] = rank
                await self.send_rank_to_user(entity_id, rank, len(sorted_ranking))
                list_users.append(value)

            self._attr_extra_state_attributes = {"rank": list_users}
