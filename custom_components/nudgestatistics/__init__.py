import datetime
import voluptuous as vol
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.components.recorder.util import get_instance
from homeassistant.const import CONF_ENTITY_ID, SERVICE_RELOAD
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
import homeassistant.helpers.config_validation as cv

DOMAIN = "statistic_service"

SERVICE_GET_STATISTIC = "get_statistic"

CONF_STATISTIC_ID = "statistic_id"
CONF_PERIOD = "period"
CONF_TYPE = "type"
CONF_START_TIME = "start_time"
CONF_END_TIME = "end_time"

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_PERIOD): cv.string,
        vol.Required(CONF_TYPE): cv.string,
        vol.Optional(CONF_START_TIME): cv.datetime,
        vol.Optional(CONF_END_TIME): cv.datetime,
    }
)

async def async_setup(hass: HomeAssistant, config):
    """Set up the statistic service."""

    async def async_get_statistic(call: ServiceCall) -> ServiceResponse :
        """Handle the get_statistic service call."""
        entity_id = call.data[CONF_ENTITY_ID]
        period = call.data[CONF_PERIOD]
        type = call.data[CONF_TYPE]
        start_time: datetime.datetime = call.data.get(
            CONF_START_TIME, datetime.datetime.now(tz=datetime.UTC)
        )
        end_time = call.data.get(CONF_END_TIME)


        stats = await get_instance(hass=hass).async_add_executor_job(
         statistics_during_period,
            hass, start_time, end_time, {entity_id},period,None,{type}
        ,
        )
        return stats[entity_id][0].__dict__



    hass.services.async_register(
    DOMAIN,
    SERVICE_GET_STATISTIC,
    async_get_statistic,schema=SERVICE_SCHEMA,supports_response=SupportsResponse.ONLY
)


    return True
