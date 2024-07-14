import string
import homeassistant.helpers.config_validation as cv
from sqlalchemy import false
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor.const import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
)
from homeassistant.helpers import selector
from .const import (
    DOMAIN,
    CONF_NUMBER_OF_PERSONS,
    CONF_LAST_YEAR_CONSUMED,
)
from homeassistant.components.energy import (
    is_configured as energy_dashboard_is_configured,
)

from custom_components.nudgeplatform.const import (
    CONF_BUDGET_YEARLY,
    CONF_NUDGE_PERSON,
    CONF_TRACKED_SENSOR_ENTITIES,
    DOMAIN as NUDGE_PLATFORM_DOMAIN,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NUMBER_OF_PERSONS): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_LAST_YEAR_CONSUMED): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1000,
                max=10000,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="kWh",
            )
        )
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
        if not energy_dashboard_is_configured(self.hass):
            errors["base"] = "energy_dashboard_not_configured"
        if user_input is not None:
            title = "Budget Haushalt"
            return self.async_create_entry(title=title, data=user_input)
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
