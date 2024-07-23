"""
Custom integration to integrate powernudge with Home Assistant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from custom_components.nudgeplatform.const import NudgeType

from .const import MyConfigEntry,MyData

PLATFORMS: list[Platform] = [
    Platform.NUMBER,Platform.SENSOR]




async def async_setup_entry(
    hass: HomeAssistant,
    entry: MyConfigEntry,
) -> bool:

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
