import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN,CONF_NUDGE_PERSON


class UserCreatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for user creation."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
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
            data_schema=vol.Schema({vol.Required(CONF_NUDGE_PERSON): str}),
            errors=errors,
        )

