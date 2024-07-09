from enum  import Enum
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN
from homeassistant.components.sensor.const import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
)
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from .const import CONF_NUDGE_PERSON, DOMAIN,CONF_CHOOSE_ACTION,CONF_BUDGET_YEARLY,CONF_TRACKED_SENSOR_ENTITIES

USER_SCHEMA = vol.Schema(
    {vol.Required(CONF_NUDGE_PERSON): str}

    )

BUDGET_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NUDGE_PERSON): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                multiple=False,
                filter=selector.EntityFilterSelectorConfig(
                    integration=DOMAIN
                ),
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
                filter=selector.EntityFilterSelectorConfig(
                    device_class=SensorDeviceClass.ENERGY
                ),
            )
        ),
    }
)


class Options(Enum):
    USER = "user"
    BUDGET = "budget"

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for user creation."""
    VERSION = 1

    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            username = user_input[CONF_NUDGE_PERSON]
            # Hier kannst du weitere Validierungen des Benutzernamens durchführen
            if not username:
                errors["base"] = "username_required"

            if not errors:
                return self.async_create_entry(title=username, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
            
        return self.async_show_form(
            step_id="init",
            data_schema=BUDGET_SCHEMA
            )
