"""The Greenely integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant


from .api import GreenelyApi

PLATFORMS: list[Platform] = [Platform.SENSOR]


type GreenelyConfigEntry = ConfigEntry[GreenelyData]  # noqa: F821


@dataclass
class GreenelyData:
    """Runtime data definition."""

    api: GreenelyApi
    facilitiyId: str


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: GreenelyConfigEntry) -> bool:
    """Set up Greenely from a config entry."""

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    api = GreenelyApi(email, password)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    if api.check_auth():
        facilitiyId = api.get_facility_id()
        entry.runtime_data = GreenelyData(api, facilitiyId)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)

    return True


async def async_update_options(hass: HomeAssistant, entry: GreenelyConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: GreenelyConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
