"""
Custom integration to integrate nudge_apps with Home Assistant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from homeassistant.helpers.device_registry import DeviceInfo

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SENSOR]

from .const import MyConfigEntry, MyData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MyConfigEntry,
) -> bool:
    entry.runtime_data = MyData(score_device_unique_id="", device_info=DeviceInfo())
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
