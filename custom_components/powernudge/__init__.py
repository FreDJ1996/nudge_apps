"""
Custom integration to integrate powernudge with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/powernudge
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration
from homeassistant.config_entries import ConfigEntry


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [
    Platform.SENSOR
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

