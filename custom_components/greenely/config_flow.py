"""Config flow for Greenely integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .api import GreenelyApi

from .const import (
    DOMAIN,
    GREENELY_DAILY_PRODUCED_ELECTRICITY,
    GREENELY_DAILY_USAGE,
    GREENELY_DATE_FORMAT,
    GREENELY_FACILITY_ID,
    GREENELY_HOMEKIT_COMPATIBLE,
    GREENELY_HOURLY_OFFSET_DAYS,
    GREENELY_HOURLY_USAGE,
    GREENELY_PRICES,
    GREENELY_PRODUCED_ELECTRICITY_DAYS,
    GREENELY_TIME_FORMAT,
    GREENELY_USAGE_DAYS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(GREENELY_FACILITY_ID): int,
    }
)


class Greenelyhub:
    """Class to authenticate with the host."""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.api = GreenelyApi(self.email, self.password)

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        return self.api.check_auth()

    async def get_facility_id(self) -> int:
        return int(self.api.get_facility_id())


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    hub = Greenelyhub(data[CONF_EMAIL], data[CONF_PASSWORD])

    if not await hub.authenticate():
        raise InvalidAuth

    facilityId = data.get(GREENELY_FACILITY_ID, await hub.get_facility_id())

    # Return info that you want to store in the config entry.
    return {
        "title": f"Greenely Facility {facilityId}",
        "facility_id": facilityId,
    }


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Greenely."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigFlow,
    ) -> GreenelyOptionsFlow:
        """Create the options flow."""
        return GreenelyOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                options = {
                    GREENELY_DAILY_USAGE: True,
                    GREENELY_FACILITY_ID: info["facility_id"],
                }
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                    options=options,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class GreenelyOptionsFlow(OptionsFlow):
    """Handle a option flow for Greenely."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize Greenely options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the Greenely options."""
        if user_input is not None:
            return self.async_create_entry(title="Manage Sensors", data=user_input)

        return self.async_show_form(
            step_id="init", data_schema=self._get_options_schema()
        )

    def _get_options_schema(self):
        return vol.Schema(
            {
                vol.Optional(
                    GREENELY_PRICES,
                    default=self.config_entry.options.get(GREENELY_PRICES, True),
                ): bool,
                vol.Optional(
                    GREENELY_DAILY_USAGE,
                    default=self.config_entry.options.get(GREENELY_DAILY_USAGE, True),
                ): bool,
                vol.Optional(
                    GREENELY_HOURLY_USAGE,
                    default=self.config_entry.options.get(GREENELY_HOURLY_USAGE, False),
                ): bool,
                vol.Optional(
                    GREENELY_DAILY_PRODUCED_ELECTRICITY,
                    default=self.config_entry.options.get(
                        GREENELY_DAILY_PRODUCED_ELECTRICITY, False
                    ),
                ): bool,
                vol.Optional(
                    GREENELY_USAGE_DAYS,
                    default=self.config_entry.options.get(GREENELY_USAGE_DAYS, 10),
                ): int,
                vol.Optional(
                    GREENELY_PRODUCED_ELECTRICITY_DAYS,
                    default=self.config_entry.options.get(
                        GREENELY_PRODUCED_ELECTRICITY_DAYS, 10
                    ),
                ): int,
                vol.Optional(
                    GREENELY_DATE_FORMAT,
                    default=self.config_entry.options.get(
                        GREENELY_DATE_FORMAT, "%b %d %Y"
                    ),
                ): str,
                vol.Optional(
                    GREENELY_TIME_FORMAT,
                    default=self.config_entry.options.get(
                        GREENELY_TIME_FORMAT, "%H:%M"
                    ),
                ): str,
                vol.Optional(
                    GREENELY_HOURLY_OFFSET_DAYS,
                    default=self.config_entry.options.get(
                        GREENELY_HOURLY_OFFSET_DAYS, 1
                    ),
                ): int,
                vol.Optional(
                    GREENELY_FACILITY_ID,
                    default=self.config_entry.options.get(GREENELY_FACILITY_ID),
                ): int,
                vol.Optional(
                    GREENELY_HOMEKIT_COMPATIBLE,
                    default=self.config_entry.options.get(
                        GREENELY_HOMEKIT_COMPATIBLE, False
                    ),
                ): bool,
            }
        )

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
