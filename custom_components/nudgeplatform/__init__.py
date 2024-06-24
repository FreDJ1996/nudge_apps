from typing import Self
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from dataclasses import dataclass
from homeassistant.helpers.storage import Store
from typing import TypedDict,TYPE_CHECKING
from custom_components import nudgeplatform
from .const import DOMAIN
from .sensor import NudgePerson
from homeassistant.const import Platform
from typing import TypedDict



# Definiere einen Typ-Alias für den ConfigEntry
type MyConfigEntry = ConfigEntry[Nudgeplattform]


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass
class Nudge:
    nudgename: str
    goal: int

@dataclass
class User:
    _username: str
    _points_total: int = 0
    _points_per_nudge: dict[Nudge, int] = {}

    def add_point_for_nudge(self, nudge: Nudge, points: int) -> None:
        if nudge not in self._points_per_nudge:
            self._points_per_nudge[nudge] = 0
        self._points_per_nudge[nudge] += points
        self._points_total += points


class NudgeplattformData(TypedDict):
    user: dict[str, str]

@dataclass
class Nudgeplattform:
    username: str

class NudgeplattformManager:
    key = DOMAIN
    def __init__(self, hass):
        self._store = Store[NudgeplattformData](hass, 1, self.key)


async def async_setup_entry(hass: HomeAssistant, entry: MyConfigEntry) -> bool:


    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

