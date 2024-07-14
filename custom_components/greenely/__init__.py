"""The Greenely integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

from .services import async_setup_services
from .api import GreenelyApi
from .const import GREENELY_FACILITY_ID

PLATFORMS: list[Platform] = [Platform.SENSOR]


type GreenelyConfigEntry = ConfigEntry[GreenelyData]


@dataclass
class GreenelyData:
    """Runtime data definition."""

    api: GreenelyApi
    facilitiyId: int


async def async_setup_entry(hass: HomeAssistant, entry: GreenelyConfigEntry) -> bool:
    """Set up Greenely from a config entry."""

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    api = GreenelyApi(email, password)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    if api.check_auth():
        facilityId = (
            api.get_facility_id()
            if entry.data.get(GREENELY_FACILITY_ID, "") == ""
            else entry.data[GREENELY_FACILITY_ID]
        )
        entry.runtime_data = GreenelyData(api, facilityId)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await async_setup_services(hass)
    return True


async def async_update_options(hass: HomeAssistant, entry: GreenelyConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GreenelyConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
