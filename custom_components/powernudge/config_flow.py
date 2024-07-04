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

NUDGE_TYPES = [
    "Strom",
    "Wasser",
    "Gas"
]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.SelectSelector(
            selector.SelectSelectorConfig(options=NUDGE_TYPES),
        ),
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
        vol.Required(CONF_METER_NET_CONSUMPTION): selector.BooleanSelector(),
        vol.Required(CONF_METER_DELTA_VALUES): selector.BooleanSelector(),
        vol.Required(CONF_METER_PERIODICALLY_RESETTING): selector.BooleanSelector(),
        vol.Optional(CONF_SENSOR_ALWAYS_AVAILABLE): selector.BooleanSelector(),
        vol.Required(CONF_SOURCE_PERSON): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(integration="nudgeplatform")
        ),
        vol.Required(CONF_NUDGE_GOAL): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1000,
                max=10000,
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
            if CONF_SOURCE_PERSON in user_input:
                name_of_person = str(user_input[CONF_SOURCE_PERSON])
                name_of_person = name_of_person.rsplit(".",1)[1]
                title = user_input[CONF_NAME]+"_"+str(name_of_person)
            else:
                title = user_input[CONF_NAME]
            return self.async_create_entry(
                title=title, data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )