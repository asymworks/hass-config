"""Support for the Airly sensor service."""
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    CONF_NAME,
)
from homeassistant.helpers.entity import Entity

from .const import (
    ATTR_API_AQI,
    ATTR_API_AQI_LEVEL,
    ATTR_API_PM25,
    ATTR_API_O3,
    DOMAIN,
    SENSOR_AQI_LEVEL,
)

ATTRIBUTION = "Data provided by AirNow"

ATTR_ICON = "icon"
ATTR_LABEL = "label"
ATTR_UNIT = "unit"

PARALLEL_UPDATES = 1

SENSOR_TYPES = {
    ATTR_API_AQI: {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:blur",
        ATTR_LABEL: ATTR_API_AQI,
        ATTR_UNIT: 'aqi',
    },
    ATTR_API_AQI_LEVEL: {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:blur",
        ATTR_LABEL: SENSOR_AQI_LEVEL,
        ATTR_UNIT: None,
    },
    ATTR_API_PM25: {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:blur",
        ATTR_LABEL: ATTR_API_PM25,
        ATTR_UNIT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    },
    ATTR_API_O3: {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:blur",
        ATTR_LABEL: ATTR_API_O3,
        ATTR_UNIT: CONCENTRATION_PARTS_PER_MILLION,
    },
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Airly sensor entities based on a config entry."""
    name = config_entry.data[CONF_NAME]

    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = []
    for sensor in SENSOR_TYPES:
        sensors.append(AirNowSensor(coordinator, name, sensor))

    async_add_entities(sensors, False)


class AirNowSensor(Entity):
    """Define an AirNow sensor."""

    def __init__(self, coordinator, name, kind):
        """Initialize."""
        # TODO: Migrate to CoordinatorEntity after 0.115 release
        self.coordinator = coordinator
        self._name = name
        self.kind = kind
        self._device_class = None
        self._state = None
        self._icon = None
        self._unit_of_measurement = None
        self._attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Update the entity.
        Only used by the generic entity update service.
        """

        # Ignore manual update requests if the entity is disabled
        if not self.enabled:
            return

        await self.coordinator.async_request_refresh()

    @property
    def name(self):
        """Return the name."""
        return f"{self._name} {SENSOR_TYPES[self.kind][ATTR_LABEL]}"

    @property
    def state(self):
        """Return the state."""
        self._state = self.coordinator.data[self.kind]
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def icon(self):
        """Return the icon."""
        self._icon = SENSOR_TYPES[self.kind][ATTR_ICON]
        return self._icon

    @property
    def device_class(self):
        """Return the device_class."""
        return SENSOR_TYPES[self.kind][ATTR_DEVICE_CLASS]

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self.coordinator.latitude}-{self.coordinator.longitude}-{self.kind.lower()}"

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return SENSOR_TYPES[self.kind][ATTR_UNIT]
