"""The AirNow integration."""
import asyncio
import datetime
import logging

import voluptuous as vol

from pyairnow import WebServiceAPI
from pyairnow.conv import aqi_to_concentration
from pyairnow.errors import AirNowError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.helpers.config_validation as cv

from .const import (
    ATTR_API_AQI,
    ATTR_API_AQI_LEVEL,
    ATTR_API_AQI_DESCRIPTION,
    ATTR_API_AQI_PARAM,
    ATTR_API_CATEGORY,
    ATTR_API_CAT_LEVEL,
    ATTR_API_CAT_DESCRIPTION,
    ATTR_API_O3,
    ATTR_API_PM25,
    ATTR_API_POLLUTANT,
    ATTR_API_REPORT_DATE,
    ATTR_API_REPORT_HOUR,
    ATTR_API_STATE,
    ATTR_API_STATION,
    ATTR_API_STATION_LATITUDE,
    ATTR_API_STATION_LONGITUDE,
    DOMAIN,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_LATITUDE): cv.latitude,
                vol.Optional(CONF_LONGITUDE): cv.longitude,
                vol.Optional(CONF_RADIUS): int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["air_quality", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the AirNow component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up AirNow from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]
    distance = entry.data[CONF_RADIUS]

    # Reports are published hourly but update twice per hour
    update_interval = datetime.timedelta(minutes=30)

    # Setup the Coordinator
    session = async_get_clientsession(hass)
    coordinator = AirNowDataUpdateCoordinator(
        hass, session, api_key, latitude, longitude, distance, update_interval
    )

    # Sync with Coordinator
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    # Store Entity and Initialize Platforms
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class AirNowDataUpdateCoordinator(DataUpdateCoordinator):
    """Define an object to hold Airly data."""

    def __init__(
        self, hass, session, api_key, latitude, longitude, distance, update_interval
    ):
        """Initialize."""
        self.latitude = latitude
        self.longitude = longitude
        self.distance = distance

        self.airnow = WebServiceAPI(api_key, session=session)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Update data via library."""
        data = {}
        obs = []
        try:
            obs = await self.airnow.observations.latLong(
                self.latitude,
                self.longitude,
                distance=self.distance,
            )

        except (AirNowError, ClientConnectorError) as error:
            raise UpdateFailed(error) from error

        if len(obs) == 0:
            raise UpdateFailed("No data was returned from AirNow")

        max_aqi = 0
        max_aqi_level = 0
        max_aqi_desc = ""
        max_aqi_poll = ""
        for ob in obs:
            # Convert AQIs to Concentration
            pollutant = ob[ATTR_API_AQI_PARAM]
            concentration = aqi_to_concentration(ob[ATTR_API_AQI], pollutant)
            data[ob[ATTR_API_AQI_PARAM]] = concentration

            # Overall AQI is the max of all pollutant AQIs
            if ob[ATTR_API_AQI] > max_aqi:
                max_aqi = ob[ATTR_API_AQI]
                max_aqi_level = ob[ATTR_API_CATEGORY][ATTR_API_CAT_LEVEL]
                max_aqi_desc = ob[ATTR_API_CATEGORY][ATTR_API_CAT_DESCRIPTION]
                max_aqi_poll = pollutant

            # Copy other data from PM2.5 Value
            if ob[ATTR_API_AQI_PARAM] == ATTR_API_PM25:
                # Copy Report Details
                data[ATTR_API_REPORT_DATE] = ob[ATTR_API_REPORT_DATE]
                data[ATTR_API_REPORT_HOUR] = ob[ATTR_API_REPORT_HOUR]

                # Copy Station Details
                data[ATTR_API_STATE] = ob[ATTR_API_STATE]
                data[ATTR_API_STATION] = ob[ATTR_API_STATION]
                data[ATTR_API_STATION_LATITUDE] = ob[ATTR_API_STATION_LATITUDE]
                data[ATTR_API_STATION_LONGITUDE] = ob[ATTR_API_STATION_LONGITUDE]

        # Store Overall AQI
        data[ATTR_API_AQI] = max_aqi
        data[ATTR_API_AQI_LEVEL] = max_aqi_level
        data[ATTR_API_AQI_DESCRIPTION] = max_aqi_desc
        data[ATTR_API_POLLUTANT] = max_aqi_poll

        return data
