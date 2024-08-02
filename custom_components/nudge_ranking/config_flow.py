import homeassistant.helpers.config_validation as cv
from sqlalchemy import false
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor.const import DOMAIN as SENSOR_DOMAIN, SensorDeviceClass
from homeassistant.components.number.const import DOMAIN as NUMBER_DOMAIN,NumberDeviceClass
from homeassistant.helpers import selector
from .const import DOMAIN,RANKING_PERSONS

from custom_components.nudgeplatform.const import (
    DOMAIN as NUDGE_PLATFORM_DOMAIN,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(RANKING_PERSONS): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=NUMBER_DOMAIN,
                multiple=True,
                filter=selector.EntityFilterSelectorConfig(integration=NUDGE_PLATFORM_DOMAIN,device_class=NumberDeviceClass.AQI)
            )
        ),
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""

    VERSION = 1
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes

    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            title = "Ranking"

            return self.async_create_entry(
                title=title, data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )