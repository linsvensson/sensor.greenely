import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers import discovery

from .const import (
    DOMAIN,
    API,
    CONFIG,
    CONF_DATA,
    DATA_LIST,
    CONF_DATE_FORMAT, 
    CONF_TIME_FORMAT, 
    CONF_USAGE_DAYS,
    CONF_SOLD_MEASURE, 
    CONF_SHOW_HOURLY, 
    CONF_SOLD_DAILY, 
    CONF_HOURLY_OFFSET_DAYS,
)

from .api import GreenelyApi

PLATFORMS = [Platform.SENSOR]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
               vol.Required(CONF_EMAIL): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                #vol.Optional(CONF_DATA, default=[]): cv.ensure_list,
                vol.Optional(
                        CONF_DATA, default=DATA_LIST
                    ): vol.All(
                        cv.ensure_list,
                        [vol.In(DATA_LIST)],
                    ),
                vol.Optional(CONF_USAGE_DAYS, default=10): cv.positive_int,
                vol.Optional(CONF_SOLD_MEASURE, default=2): cv.positive_int,
                vol.Optional(CONF_SOLD_DAILY, default=False): cv.boolean,
                vol.Optional(CONF_DATE_FORMAT, default='%b %d %Y'): cv.string,
                vol.Optional(CONF_TIME_FORMAT, default='%H:%M'): cv.string,
                vol.Optional(CONF_SHOW_HOURLY, default=False): cv.boolean,
                vol.Optional(CONF_HOURLY_OFFSET_DAYS, default=1): cv.positive_int,
            }
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

NAME = DOMAIN
ISSUEURL = "https://github.com/linsvensson/sensor.greenely/issues"

STARTUP = f"""
-------------------------------------------------------------------
{NAME}
This is a custom component
If you have any issues with this you need to open an issue here:
{ISSUEURL}
-------------------------------------------------------------------
"""

async def _dry_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up using yaml config file."""
    
    platform_config = config[DOMAIN]
    
    # If platform is not enabled, skip.
    if not platform_config:
        return False

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
        api = GreenelyApi(platform_config[CONF_EMAIL], platform_config[CONF_PASSWORD])
        hass.data[DOMAIN][API] = api
        hass.data[DOMAIN][CONFIG] = platform_config

    return True

async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up using yaml config file."""
    res = await _dry_setup(hass, config)
    
    for platform in PLATFORMS:
        hass.async_create_task(
            discovery.async_load_platform(hass, platform, DOMAIN, {}, config)
        )
    return res

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up greenely as config entry."""
    res = await _dry_setup(hass, entry.data)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, PLATFORMS)
    )

    return res

async def options_update_listener(
    hass: HomeAssistant, config_entry: ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    if unload_ok:
        for unsub in hass.data[DOMAIN].listeners:
            unsub()
        hass.data.pop(DOMAIN)

        return True

    return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)