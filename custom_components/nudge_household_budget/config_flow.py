import homeassistant.components.energy.data as energydata
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.energy import (
    is_configured as energy_dashboard_is_configured,
)
from homeassistant.helpers import selector

from custom_components.nudgeplatform.const import (
    NudgeType,
)

from .const import (
    CONF_AUTARKY_GOAL,
    CONF_HEAT_OPTIONS,
    CONF_HEAT_SOURCE,
    CONF_LAST_YEAR_CONSUMED,
    CONF_NUMBER_OF_PERSONS,
    CONF_TITLE,
    DOMAIN,
    CONF_BUDGET_YEARLY_ELECTRICITY,
    CONF_BUDGET_YEARLY_HEAT,
    CONF_HOUSEHOLD_INFOS
)

STEP_IDS = {
    NudgeType.ELECTRICITY_BUDGET: "electricity",
    NudgeType.AUTARKY_GOAL: "autarky",
}

DATA_SCHEMAS = {
    NudgeType.ELECTRICITY_BUDGET: vol.Schema(
        {
            vol.Required(
                CONF_BUDGET_YEARLY_ELECTRICITY
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1000,
                    max=10000,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="kWh",
                )
            )
        }
    ),
    NudgeType.HEAT_BUDGET: vol.Schema(
        {
            vol.Required(
                CONF_BUDGET_YEARLY_HEAT
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1000,
                    max=10000,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="kWh",
                )
            )
        }
    ),
    NudgeType.AUTARKY_GOAL: vol.Schema(
        {
            vol.Required(CONF_AUTARKY_GOAL): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=100,
                    mode=selector.NumberSelectorMode.SLIDER,
                    unit_of_measurement="%",
                )
            )
        }
    ),
}

SCHMEMA_HOUSEHOLD_INFOS = vol.Schema(
    {
        vol.Required(CONF_NUMBER_OF_PERSONS): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(CONF_HEAT_SOURCE): selector.SelectSelector(
            selector.SelectSelectorConfig(options=CONF_HEAT_OPTIONS)
        ),
        vol.Optional(CONF_LAST_YEAR_CONSUMED): selector.NumberSelector(
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

    def __init__(self) -> None:
        self.data = {}
        self.nudge_support = {}

    async def validate_input(self, user_input) -> dict[NudgeType, bool]:
        nudge_support = {nudge_type: False for nudge_type in NudgeType}

        energy_manager = await energydata.async_get_manager(self.hass)

        energy_manager_data: energydata.EnergyPreferences | None = energy_manager.data

        if energy_manager_data is not None:
            energy_sources: list[energydata.SourceType] = energy_manager_data[
                "energy_sources"
            ]
        for source in energy_sources:
            if source["type"] == "grid":
                nudge_support[NudgeType.ELECTRICITY_BUDGET] = True
            elif (
                source["type"] == "gas"
                and user_input[CONF_HEAT_SOURCE] == CONF_HEAT_OPTIONS[0]
            ):
                nudge_support[NudgeType.HEAT_BUDGET] = True
            elif source["type"] == "solar":
                nudge_support[NudgeType.AUTARKY_GOAL] = True
            elif source["type"] == "water":
                nudge_support[NudgeType.WATER_BUDGET] = True
        return nudge_support

    async def async_step_user(self, user_input=None):
        if not await energy_dashboard_is_configured(self.hass):
            return self.async_abort(reason="Energy dashboard not configured")
        if user_input is not None:
            self.data = user_input
            self.nudge_support = await self.validate_input(user_input=user_input)
            for nudge_type, is_configured in self.nudge_support.items():
                if is_configured:
                    self.nudge_support[nudge_type] = False
                    return self.async_show_form(
                        step_id=STEP_IDS[nudge_type],
                        data_schema=DATA_SCHEMAS[nudge_type],
                    )

            return self.async_create_entry(title=CONF_TITLE, data=self.data)

        return self.async_show_form(step_id="user", data_schema=SCHMEMA_HOUSEHOLD_INFOS)

    async def async_step_electricity(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.data.update(user_input)
            for nudge_type, is_configured in self.nudge_support.items():
                if is_configured:
                    self.nudge_support[nudge_type] = False
                    return self.async_show_form(
                        step_id=STEP_IDS[nudge_type],
                        data_schema=DATA_SCHEMAS[nudge_type],
                    )
            return self.async_create_entry(title=CONF_TITLE, data=self.data)

        return self.async_show_form(
            step_id=STEP_IDS[NudgeType.ELECTRICITY_BUDGET],
            data_schema=DATA_SCHEMAS[NudgeType.ELECTRICITY_BUDGET],
            errors=errors,
        )

    async def async_step_autarky(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.data.update(user_input)
            for nudge_type, is_configured in self.nudge_support.items():
                if is_configured:
                    self.nudge_support[nudge_type] = False
                    return self.async_show_form(
                        step_id=STEP_IDS[nudge_type],
                        data_schema=SCHMEMA_HOUSEHOLD_INFOS,
                    )
            return self.async_create_entry(title=CONF_TITLE, data=self.data)

        return self.async_show_form(
            step_id=STEP_IDS[NudgeType.AUTARKY_GOAL],
            data_schema=DATA_SCHEMAS[NudgeType.AUTARKY_GOAL],
            errors=errors,
        )
