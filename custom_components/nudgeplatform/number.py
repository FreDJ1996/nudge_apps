from homeassistant.components.number import RestoreNumber, NumberMode, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import (
    DeviceEntryType,
    DeviceInfo,
    async_get as async_get_device_registry,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import EntityCategory
from homeassistant.helpers import entity_platform
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from homeassistant.helpers.entity_registry import (
    EntityRegistry,
    async_get as async_get_entity_registry,
)
from homeassistant.const import Platform

from .const import (
    CONF_NUDGE_PERSON,
    DOMAIN,
    SERVICE_SET_RANK_FOR_USER,
    SERVICE_ADD_POINTS_TO_USER,
    NudgeType,
    SERVICE_UPDATE_STREAK,
)


def register_services() -> None:
    # Register the service
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_RANK_FOR_USER,
        {
            vol.Required("ranking_position"): cv.positive_int,
            vol.Required("ranking_length"): cv.positive_int,
        },
        "set_ranking_position",
    )
    platform.async_register_entity_service(
        SERVICE_ADD_POINTS_TO_USER,
        {
            vol.Required("points"): cv.positive_int,
        },
        SERVICE_ADD_POINTS_TO_USER,
    )
    platform.async_register_entity_service(
    SERVICE_UPDATE_STREAK,
    {
        vol.Required("goal_reached"): cv.boolean,
    },
    SERVICE_UPDATE_STREAK,
    )


@callback
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize nudgeplatform config entry."""

    entities = []
    name = config_entry.data[CONF_NUDGE_PERSON]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        entry_type=DeviceEntryType.SERVICE,
        name=name,
    )

    entities.append(
        Score(
            entry_id=config_entry.entry_id,
            device_info=device_info,
            nudge_type=NudgeType.ELECTRICITY_BUDGET,
        )
    )
    entities.append(Streak(NudgeType.ELECTRICITY_BUDGET,entry_id=config_entry.entry_id,device_info=device_info))
    register_services()
    async_add_entities(entities)

class Streak(RestoreNumber):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "days"

    def __init__(
            self,
            nudge_type: NudgeType,
            entry_id: str,
            device_info: DeviceInfo | None = None,
        ) -> None:
            super().__init__()
            self._attr_device_info = device_info
            self._attr_native_value: int = 0
            self.nudge_type = nudge_type
            self._attr_name = f"Streak {nudge_type.name.replace("_"," ").capitalize()}"
            self._attr_unique_id: str = f"{entry_id}_{nudge_type.name}_Streak"

    async def update_streak(self, goal_reached: bool)->None:
        if goal_reached:
            self._attr_native_value = 0
        else:
            self._attr_native_value += 1

    def get_unique_id(self) -> str:
        return self._attr_unique_id

class Score(RestoreNumber):
    """Nudge Person for Nudging."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "points"

    def __init__(
        self,
        nudge_type: NudgeType,
        entry_id: str,
        device_info: DeviceInfo | None = None,
    ) -> None:
        super().__init__()
        self._attr_device_info = device_info
        self.ranking_position = "0/0"
        self._attr_native_value: int = 0
        self.nudge_type = nudge_type
        self._attr_name = f"Score {nudge_type.name.replace("_"," ").capitalize()}"
        self._attr_unique_id: str = f"{entry_id}_{nudge_type.name}_Score"

    async def set_ranking_position(
        self, ranking_position: int, ranking_length: int
    ) -> None:
        self.ranking_position = f"{ranking_position}/{ranking_length}"

    async def add_points_to_score(self, goal_reached: bool) -> None:
        if goal_reached:
            self._attr_native_value += 1


    def get_unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes of the sensor."""
        return {"rank": self.ranking_position}

    async def async_added_to_hass(self) -> None:
        """Restore last state."""
        last_number_data = await self.async_get_last_number_data()
        if last_number_data and last_number_data.native_value:
            self._attr_native_value = int(last_number_data.native_value)
        else:
            self._attr_native_value = 0

    async def async_set_native_value(self, value: float) -> None:
       """Update the current value."""
       if value.is_integer():
           self._attr_native_value = int(value)
           self.async_write_ha_state()


class TotalScore(NumberEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "points"

    def __init__(
        self,
        entity_uuids_scores: dict[NudgeType, str],
        domain: str,
        entry_id:str,
        device_info: DeviceInfo | None = None,
    ) -> None:
        super().__init__()
        self._attr_device_info = device_info
        self.ranking_position = "0/0"
        self._attr_native_value: int = 0
        self._entity_ids: dict[NudgeType, str] = {}
        self._entity_uuids_scores = entity_uuids_scores
        self._domain = domain
        self._attr_name = "Total Score"
        self._attr_unique_id: str = f"{entry_id}_total_score"


    @staticmethod
    def get_entity_ids_from_uuid(
        entityRegistry: EntityRegistry, uuids: dict[NudgeType, str], domain: str
    ):
        entity_ids: dict[NudgeType, str] = {}

        for nudgetype,uuid in uuids.items():
            entity_id = entityRegistry.async_get_entity_id(
                platform=domain, domain=Platform.NUMBER, unique_id=uuid
            )
            if entity_id:
                entity_ids[nudgetype] = entity_id

        return entity_ids

    async def async_added_to_hass(self) -> None:
        # Jeden Abend die Punkte aktualisieren
        entity_registry = async_get_entity_registry(self.hass)
        self._entity_ids = TotalScore.get_entity_ids_from_uuid(
            entityRegistry=entity_registry,
            uuids=self._entity_uuids_scores,
            domain=self._domain,
        )

    async def async_update(self) -> None:
        totalpoints: int = 0
        points_per_nudge: dict[NudgeType, int] = {}
        for nudge_type,score_entity in self._entity_ids.items():
            state = self.hass.states.get(score_entity)
            if state:
                value = int(state.state)
                totalpoints += value
                points_per_nudge[nudge_type] = value

        self._attr_native_value = totalpoints
        self._attr_extra_state_attributes = {
            nudge_type.name: score for nudge_type, score in points_per_nudge.items()
        }
        self._attr_extra_state_attributes["Total"] = self.ranking_position

        self.async_write_ha_state()

    def get_entities_for_device_info(self, device_info):
        """Get all entities for a given device_info."""
        entity_registry = async_get_entity_registry(self.hass)
        device_registry = async_get_device_registry(self.hass)

        # Suche das Gerät im Device Registry basierend auf den Identifikatoren
        device = None
        for dev in device_registry.devices.values():
            if any(
                identifier in dev.identifiers
                for identifier in device_info["identifiers"]
            ):
                device = dev
                break

        if device is None:
            return []

        # Verwende die device_id des gefundenen Geräts, um die Entitäten zu ermitteln
        entities = [
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.device_id == device.id
        ]

        return entities
