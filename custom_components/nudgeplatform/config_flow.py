import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_NUDGE_PERSON, DOMAIN

DATA_SCHEMA = vol.Schema({vol.Required(CONF_NUDGE_PERSON): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for user creation."""

    VERSION = 1

    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None) ->config_entries.ConfigFlowResult:
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
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
