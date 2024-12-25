from datetime import datetime, timedelta
import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.helpers.entity import Entity

from . import GreenelyData
from .const import (
    DOMAIN,
    GREENELY_DAILY_PRODUCED_ELECTRICITY,
    GREENELY_DAILY_USAGE,
    GREENELY_DATE_FORMAT,
    GREENELY_HOMEKIT_COMPATIBLE,
    GREENELY_HOURLY_OFFSET_DAYS,
    GREENELY_HOURLY_USAGE,
    GREENELY_PRICES,
    GREENELY_PRODUCED_ELECTRICITY_DAYS,
    GREENELY_TIME_FORMAT,
    GREENELY_USAGE_DAYS,
    GREENELY_FACILITY_ID,
    SENSOR_DAILY_PRODUCED_ELECTRICITY_NAME,
    SENSOR_DAILY_USAGE_NAME,
    SENSOR_HOURLY_USAGE_NAME,
    SENSOR_PRICES_NAME,
)

SCAN_INTERVAL = timedelta(minutes=10)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: GreenelyData,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    api = config_entry.runtime_data.api
    facility_id = str(config_entry.options.get(GREENELY_FACILITY_ID))
    usage_days = config_entry.options.get(GREENELY_USAGE_DAYS, 10)
    production_days = config_entry.options.get(GREENELY_PRODUCED_ELECTRICITY_DAYS, 10)
    hourly_offset_days = config_entry.options.get(GREENELY_HOURLY_OFFSET_DAYS, 1)
    date_format = config_entry.options.get(GREENELY_DATE_FORMAT, "%b %d %Y")
    time_format = config_entry.options.get(GREENELY_TIME_FORMAT, "%H:%M")
    homekit_compatible = config_entry.options.get(GREENELY_HOMEKIT_COMPATIBLE, False)

    sensors = []

    api.set_facility_id(facility_id)

    if config_entry.data.get(GREENELY_DAILY_USAGE, True):
        sensors.append(
            GreenelyDailyUsageSensor(
                SENSOR_DAILY_USAGE_NAME,
                api,
                facility_id,
                usage_days,
                date_format,
                time_format,
            )
        )
    if config_entry.data.get(GREENELY_PRICES, True):
        sensors.append(
            GreenelyPricesSensor(
                SENSOR_PRICES_NAME,
                api,
                facility_id,
                date_format,
                time_format,
                homekit_compatible,
            )
        )

    if config_entry.options.get(GREENELY_HOURLY_USAGE, False):
        sensors.append(
            GreenelyHourlyUsageSensor(
                SENSOR_HOURLY_USAGE_NAME,
                api,
                facility_id,
                hourly_offset_days,
                date_format,
                time_format,
            )
        )

    if config_entry.options.get(GREENELY_DAILY_PRODUCED_ELECTRICITY, False):
        sensors.append(
            GreenelyDailyProducedElecticitySensor(
                SENSOR_DAILY_PRODUCED_ELECTRICITY_NAME,
                api,
                facility_id,
                production_days,
                date_format,
                time_format,
            )
        )

    async_add_entities(sensors, True)


class GreenelyDailyUsageSensor(Entity):
    def __init__(self, name, api, facility_id, usage_days, date_format, time_format):
        self._name = name
        self._icon = "mdi:lightning-bolt"
        self._state = 0
        self._state_attributes = {
            "state_class": "measurement",
            "last_reset": "1970-01-01T00:00:00+00:00",
        }
        self._unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._usage_days = usage_days
        self._date_format = date_format
        self._time_format = time_format
        self._api = api
        self._device_class = SensorDeviceClass.ENERGY
        self._facility_id = facility_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._facility_id + "_daily_usage"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        _LOGGER.debug("device_info")
        return DeviceInfo(
            name="Greenely",
            identifiers={(DOMAIN, self._facility_id)},
            manufacturer="Greenely",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def device_class(self):
        """Return the class of the sensor."""
        return self._device_class

    def update(self):
        _LOGGER.debug("Checking jwt validity...")
        if self._api.check_auth():
            # Get todays date
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            _LOGGER.debug("Fetching daily usage data...")
            data = []
            startDate = today - timedelta(days=self._usage_days)
            response = self._api.get_usage(startDate, today, False)
            if response:
                data = self.make_attributes(today, response)
            self._state_attributes["data"] = data
        else:
            _LOGGER.error("Unable to log in!")

    def make_attributes(self, today, response):
        yesterday = today - timedelta(days=1)
        data = []
        keys = iter(response)
        if keys != None:
            for k in keys:
                daily_data = {}
                dateTime = datetime.strptime(response[k]["localtime"], "%Y-%m-%d %H:%M")
                daily_data["localtime"] = dateTime.strftime(self._date_format)
                usage = response[k]["usage"]
                if dateTime == yesterday:
                    self._state = usage / 1000 if usage != None else 0
                daily_data["usage"] = (usage / 1000) if usage != None else 0
                data.append(daily_data)
        return data


class GreenelyHourlyUsageSensor(Entity):
    def __init__(
        self, name, api, facility_id, hourly_offset_days, date_format, time_format
    ):
        self._name = name
        self._icon = "mdi:lightning-bolt"
        self._state = 0
        self._state_attributes = {
            "state_class": "measurement",
            "last_reset": "1970-01-01T00:00:00+00:00",
        }
        self._unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._date_format = date_format
        self._time_format = time_format
        self._hourly_offset_days = hourly_offset_days
        self._api = api
        self._device_class = SensorDeviceClass.ENERGY
        self._facility_id = facility_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._facility_id + "_hourly_usage"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        _LOGGER.debug("device_info")
        return DeviceInfo(
            name="Greenely",
            identifiers={(DOMAIN, self._facility_id)},
            manufacturer="Greenely",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def device_class(self):
        """Return the class of the sensor."""
        return self._device_class

    def update(self):
        _LOGGER.debug("Checking jwt validity...")
        if self._api.check_auth():
            # Get todays date
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            _LOGGER.debug("Fetching hourly usage data...")
            data = []
            startDate = today - timedelta(days=self._hourly_offset_days)
            response = self._api.get_usage(startDate, today, True)
            if response:
                data = self.make_attributes(datetime.now(), response)
            self._state_attributes["data"] = data
        else:
            _LOGGER.error("Unable to log in!")

    def make_attributes(self, today, response):
        yesterday = today - timedelta(days=1)
        data = []
        keys = iter(response)
        if keys != None:
            for k in keys:
                hourly_data = {}
                dateTime = datetime.strptime(response[k]["localtime"], "%Y-%m-%d %H:%M")
                hourly_data["localtime"] = (
                    dateTime.strftime(self._date_format)
                    + " "
                    + dateTime.strftime(self._time_format)
                )
                usage = response[k]["usage"]
                if (
                    dateTime.hour == yesterday.hour
                    and dateTime.day == yesterday.day
                    and dateTime.month == yesterday.month
                    and dateTime.year == yesterday.year
                ):
                    self._state = usage / 1000 if usage != None else 0
                hourly_data["usage"] = (usage / 1000) if usage != None else 0
                data.append(hourly_data)
        return data


class GreenelyPricesSensor(Entity):
    def __init__(
        self, name, api, facility_id, date_format, time_format, homekit_compatible
    ):
        self._name = name
        self._icon = "mdi:account-cash"
        self._state = 0
        self._state_attributes = {}
        self._unit_of_measurement = "SEK/kWh" if homekit_compatible != True else "°C"
        self._date_format = date_format
        self._time_format = time_format
        self._homekit_compatible = homekit_compatible
        self._api = api
        self._facility_id = facility_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._facility_id + "_prices"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        _LOGGER.debug("device_info")
        return DeviceInfo(
            name="Greenely",
            identifiers={(DOMAIN, self._facility_id)},
            manufacturer="Greenely",
            entry_type=DeviceEntryType.SERVICE,
        )

    def update(self):
        """Update state and attributes."""
        _LOGGER.debug("Checking jwt validity...")
        if self._api.check_auth():
            data = self._api.get_price_data()
            totalCost = 0
            if data:
                for d, value in data.items():
                    cost = value["cost"]
                    if cost != None:
                        totalCost += cost
                self._state_attributes["current_month"] = round(totalCost / 100000)
            spot_price_data = self._api.get_spot_price()
            if spot_price_data:
                _LOGGER.debug("Fetching daily prices...")
                today = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                todaysData = []
                tomorrowsData = []
                yesterdaysData = []
                for d in spot_price_data["data"]:
                    timestamp = datetime.strptime(
                        spot_price_data["data"][d]["localtime"], "%Y-%m-%d %H:%M"
                    )
                    if timestamp.date() == today.date():
                        if spot_price_data["data"][d]["price"] != None:
                            todaysData.append(self.make_attribute(spot_price_data, d))
                    elif timestamp.date() == (today.date() + timedelta(days=1)):
                        if spot_price_data["data"][d]["price"] != None:
                            tomorrowsData.append(
                                self.make_attribute(spot_price_data, d)
                            )
                    elif timestamp.date() == (today.date() - timedelta(days=1)):
                        if spot_price_data["data"][d]["price"] != None:
                            yesterdaysData.append(
                                self.make_attribute(spot_price_data, d)
                            )
                self._state_attributes["current_day"] = todaysData
                self._state_attributes["next_day"] = tomorrowsData
                self._state_attributes["previous_day"] = yesterdaysData
        else:
            _LOGGER.error("Unable to log in!")

    def make_attribute(self, response, value):
        if response:
            newPoint = {}
            today = datetime.now()
            price = response["data"][value]["price"]
            dt_object = datetime.strptime(
                response["data"][value]["localtime"], "%Y-%m-%d %H:%M"
            )
            newPoint["date"] = dt_object.strftime(self._date_format)
            newPoint["time"] = dt_object.strftime(self._time_format)
            if price != None:
                rounded = self.format_price(price)
                newPoint["price"] = rounded
                if dt_object.hour == today.hour and dt_object.day == today.day:
                    self._state = rounded
            else:
                newPoint["price"] = 0
            return newPoint

    def format_price(self, price):
        if self._homekit_compatible == True:
            return round(price / 1000)
        else:
            return round(((price / 1000) / 100), 4)

    def make_data_attribute(self, name, response, nameOfPriceAttr):
        if response:
            points = response.get("points", None)
            data = []
            for point in points:
                price = point[nameOfPriceAttr]
                if price != None:
                    newPoint = {}
                    dt_object = datetime.utcfromtimestamp(point["timestamp"])
                    newPoint["date"] = dt_object.strftime(self._date_format)
                    newPoint["time"] = dt_object.strftime(self._time_format)
                    newPoint["price"] = str(price / 100)
                    data.append(newPoint)
            self._state_attributes[name] = data


class GreenelyDailyProducedElecticitySensor(Entity):
    def __init__(
        self,
        name,
        api,
        facility_id,
        produced_electricity_days,
        date_format,
        time_format,
    ):
        self._name = name
        self._icon = "mdi:lightning-bolt"
        self._state = 0
        self._state_attributes = {
            "state_class": "measurement",
            "last_reset": "1970-01-01T00:00:00+00:00",
        }
        self._produced_electricity_days = produced_electricity_days
        self._unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._date_format = date_format
        self._time_format = time_format
        self._api = api
        self._device_class = SensorDeviceClass.ENERGY
        self._facility_id = facility_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._facility_id + "_daily_produced_electricity"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        _LOGGER.debug("device_info")
        return DeviceInfo(
            name="Greenely",
            identifiers={(DOMAIN, self._facility_id)},
            manufacturer="Greenely",
            entry_type=DeviceEntryType.SERVICE,
        )

    def update(self):
        _LOGGER.debug("Checking jwt validity...")
        if self._api.check_auth():
            # Get todays date
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            _LOGGER.debug("Fetching daily produced electricity data...")
            data = []
            startDate = today - timedelta(days=(self._produced_electricity_days - 1))
            endDate = today + timedelta(days=1)
            response = self._api.get_produced_electricity(startDate, endDate, False)
            if response:
                data = self.make_attributes(today, response)
            self._state_attributes["data"] = data
        else:
            _LOGGER.error("Unable to log in!")

    def make_attributes(self, today, response):
        data = []
        keys = iter(response)
        if keys != None:
            for k in keys:
                daily_data = {}
                dateTime = datetime.strptime(response[k]["localtime"], "%Y-%m-%d %H:%M")
                daily_data["localtime"] = dateTime.strftime(self._date_format)
                produced_electricity = response[k]["value"]
                if dateTime == today:
                    self._state = (
                        produced_electricity / 1000
                        if produced_electricity != None
                        else 0
                    )
                daily_data["produced_electricity"] = (
                    (produced_electricity / 1000) if produced_electricity != None else 0
                )
                data.append(daily_data)
        return data
