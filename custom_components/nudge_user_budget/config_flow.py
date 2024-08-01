import homeassistant.helpers.config_validation as cv
from sqlalchemy import false
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor.const import DOMAIN as SENSOR_DOMAIN, SensorDeviceClass
from homeassistant.components.number.const import DOMAIN as NUMBER_DOMAIN
from homeassistant.helpers import selector
from .const import DOMAIN

from custom_components.nudgeplatform.const import (
    CONF_BUDGET_YEARLY,
    CONF_NUDGE_PERSON,
    CONF_TRACKED_SENSOR_ENTITIES,
    DOMAIN as NUDGE_PLATFORM_DOMAIN,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NUDGE_PERSON): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=NUMBER_DOMAIN,
                multiple=False,
                filter=selector.EntityFilterSelectorConfig(integration=NUDGE_PLATFORM_DOMAIN)
            )
        ),
        vol.Required(CONF_BUDGET_YEARLY): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1000,
                max=10000,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="kWh",
            )
        ),
        vol.Required(CONF_TRACKED_SENSOR_ENTITIES): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                multiple=True,
                filter=selector.EntityFilterSelectorConfig(device_class=SensorDeviceClass.ENERGY),
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
            entity_id_user = user_input.get(CONF_NUDGE_PERSON, "")

            start = entity_id_user.find(".") + 1
            end = entity_id_user.find(
                "_", start
            )
            name_user:str = entity_id_user[start:end]
            name_user = name_user.capitalize()
            title = "Budget " + str(name_user)

            return self.async_create_entry(
                title=title, data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )