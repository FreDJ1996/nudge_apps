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


