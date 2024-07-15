import logging
import voluptuous as vol
import json
import homeassistant.helpers.config_validation as cv
from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL
from homeassistant.core import HomeAssistant, ServiceCall
from .api import GreenelyApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_FETCH_FACILITIES = "fetch_facilities"

SERVICE_FETCH_FACILITIES_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional("output_json", default=False): cv.boolean,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the Greenely integration."""

    async def async_fetch_facilities(call: ServiceCall):
        """Service to fetch facility id."""
        email = call.data[CONF_EMAIL]
        password = call.data[CONF_PASSWORD]

        api = GreenelyApi(email, password)
        if not api.check_auth():
            await hass.services.async_call(
                NOTIFY_DOMAIN,
                "persistent_notification",
                {"message": "Invalid credentials", "title": "Greenely facility ids"},
                blocking=True,
            )

        else:
            facilityIds = api.get_facility_ids()
            _LOGGER.info("Facilities fetched successfully")

            facilityIdsOutput = []

            for entity in facilityIds:
                facilityInfo = f"ID: {entity['id']}, Street: {entity['street']}, Zip Code: {entity['zip_code']}, City: {entity['city']}, Is Primary: {entity['is_primary']} "
                facilityIdsOutput.append(facilityInfo)

            facilityIdsMessage = "\n".join(facilityIdsOutput)
            await hass.services.async_call(
                NOTIFY_DOMAIN,
                "persistent_notification",
                {"message": facilityIdsMessage, "title": "Greenely facility ids"},
                blocking=True,
            )

            if call.data["output_json"]:
                message = json.dumps(facilityIds)
                await hass.services.async_call(
                    NOTIFY_DOMAIN,
                    "persistent_notification",
                    {"message": message, "title": "Greenely facility ids json"},
                    blocking=True,
                )

    hass.services.async_register(
        DOMAIN,
        SERVICE_FETCH_FACILITIES,
        async_fetch_facilities,
        schema=SERVICE_FETCH_FACILITIES_SCHEMA,
    )
