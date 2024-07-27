import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.nudgeplatform.const import (
    DOMAIN as NUDGEPLATFORM_DOMAIN,
)
from custom_components.nudgeplatform.const import (
    SERVICE_SET_RANK_FOR_USER,
)

from .const import RANKING_PERSONS

SCAN_INTERVAL = timedelta(minutes=1)

_LOGGER = logging.getLogger(__name__)


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
        entities = [Ranking(users, entry_id)]
        async_add_entities(entities)


class Ranking(SensorEntity):
    _attr_should_poll = True

    def __init__(self, user_score_entities: list[str], entry_id: str) -> None:
        self._attr_name = "Ranking"
        self._attr_unique_id = entry_id
        self._attr_native_value = None
        self._user_score_entities = user_score_entities
        self.ranking = []

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

    async def async_update(self) -> None:
        ranking = {}
        for entity_id in self._user_score_entities:  # Direkte Iteration über IDs
            state = self.hass.states.get(entity_id)
            if state and state.state.isdigit():  # Direkte Prüfung auf Zahl
                ranking[entity_id] = {"name": state.name.split()[0], "value": int(state.state)}

        sorted_ranking = sorted(
            ranking.items(), key=lambda item: item[1]["value"], reverse=True
        )

        if sorted_ranking:
            self._attr_native_value = sorted_ranking[0][1]["value"]

            list_users = []
            for rank, (entity_id, value) in enumerate(sorted_ranking, start=1):
                await self.send_rank_to_user(entity_id, rank, len(sorted_ranking))
                list_users.append(value)

            self._attr_extra_state_attributes = {"rank": list_users}
