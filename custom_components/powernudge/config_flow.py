"""Config flow for test integration."""


import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor.const import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import (
    CONF_GOAL_TYPE,
    CONF_METER_DELTA_VALUES,
    CONF_METER_NET_CONSUMPTION,
    CONF_METER_OFFSET,
    CONF_METER_PERIODICALLY_RESETTING,
    CONF_NUDGE_GOAL,
    CONF_SENSOR_ALWAYS_AVAILABLE,
    CONF_SOURCE_PERSON,
    CONF_SOURCE_SENSOR,
    DOMAIN,
)

GOAL_TYPES = ["TAG", "MONAT", "JAHR"]


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(CONF_SOURCE_SENSOR): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=SENSOR_DOMAIN),
        ),
        vol.Required(CONF_METER_OFFSET): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=28,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="days",
            ),
        ),
        vol.Required(
            CONF_METER_NET_CONSUMPTION
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_DELTA_VALUES
        ): selector.BooleanSelector(),
        vol.Required(
            CONF_METER_PERIODICALLY_RESETTING
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_SENSOR_ALWAYS_AVAILABLE
        ): selector.BooleanSelector(),
        vol.Required(CONF_GOAL_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(options=GOAL_TYPES)
        ),
        vol.Required(CONF_NUDGE_GOAL): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=1000,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="kWh",
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
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )