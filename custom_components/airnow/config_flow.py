"""Config flow for AirNow integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_RADIUS,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from pyairnow import WebServiceAPI
from pyairnow.errors import AirNowError, InvalidKeyError

from .const import DEFAULT_NAME, DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: core.HomeAssistant, data):
    """
    Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)
    client = WebServiceAPI(data[CONF_API_KEY], session=session)

    # Check that we can connect to AirNow with the given API Key
    try:
        await client.observations.latLong(34.053718, -118.244842)
    except InvalidKeyError:
        raise InvalidAuth
    except AirNowError:
        raise CannotConnect

    # Check that the provided latitude/longitude provide a response
    try:
        lat = data[CONF_LATITUDE]
        lng = data[CONF_LONGITUDE]
        range = data[CONF_RADIUS]
        data = await client.observations.latLong(lat, lng, distance=range)
        if len(data) == 0:
            raise InvalidLocation
    except InvalidKeyError:
        raise InvalidAuth
    except AirNowError:
        raise CannotConnect

    # Validation Succeeded
    return True


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AirNow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                # Set a unique id based on latitude/longitude
                await self.async_set_unique_id(
                    f"{user_input[CONF_LATITUDE]}-{user_input[CONF_LONGITUDE]}"
                )
                self._abort_if_unique_id_configured()

                # Validate inputs
                info = await validate_input(self.hass, user_input)

                # Create Entry
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except InvalidLocation:
                errors["base"] = "invalid_location"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(
                        CONF_LATITUDE, default=self.hass.config.latitude
                    ): cv.latitude,
                    vol.Optional(
                        CONF_LONGITUDE, default=self.hass.config.longitude
                    ): cv.longitude,
                    vol.Optional(CONF_RADIUS, default=150): int,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidLocation(exceptions.HomeAssistantError):
    """Error to indicate the location is invalid."""
