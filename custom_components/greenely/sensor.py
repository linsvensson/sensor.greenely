"""Greenely sensors"""
from datetime import datetime, timedelta

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.entity import Entity

from .api import GreenelyApi

from .const import (
    DOMAIN,
    SENSOR_USAGE_NAME,
    SENSOR_SOLD_NAME,
    SENSOR_PRICES_NAME,
    CONF_USAGE,
    CONF_SOLD,
    CONF_PRICES,
    CONF_DATE_FORMAT, 
    CONF_TIME_FORMAT, 
    CONF_USAGE_DAYS,
    CONF_SOLD_MEASURE, 
    CONF_SHOW_HOURLY, 
    CONF_SOLD_DAILY, 
    CONF_HOURLY_OFFSET_DAYS,
    MONITORED_CONDITIONS_DEFAULT
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

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_USAGE): cv.boolean,
    vol.Optional(CONF_SOLD): cv.boolean,
    vol.Optional(CONF_PRICES): cv.boolean,
    vol.Optional(CONF_USAGE_DAYS, default=10): cv.positive_int,
    vol.Optional(CONF_SOLD_MEASURE, default=2): cv.positive_int,
    vol.Optional(CONF_SOLD_DAILY, default=False): cv.boolean,
    vol.Optional(CONF_DATE_FORMAT, default='%b %d %Y'): cv.string,
    vol.Optional(CONF_TIME_FORMAT, default='%H:%M'): cv.string,
    vol.Optional(CONF_SHOW_HOURLY, default=False): cv.boolean,
    vol.Optional(CONF_HOURLY_OFFSET_DAYS, default=1): cv.positive_int,
})

SCAN_INTERVAL = timedelta(minutes=60)

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    email = config.get(CONF_EMAIL)
    password = config.get(CONF_PASSWORD)
    
    date_format = config.get(CONF_DATE_FORMAT)
    time_format = config.get(CONF_TIME_FORMAT)
    show_usage = config.get(CONF_USAGE)
    show_sold = config.get(CONF_SOLD)
    show_prices = config.get(CONF_PRICES)
    usage_days = config.get(CONF_USAGE_DAYS)
    sold_measure = config.get(CONF_SOLD_MEASURE)
    show_hourly = config.get(CONF_SHOW_HOURLY)
    sold_daily = config.get(CONF_SOLD_DAILY)
    hourly_offset_days = config.get(CONF_HOURLY_OFFSET_DAYS)
    if hourly_offset_days > usage_days:
        hourly_offset_days = usage_days
        
    api = GreenelyApi(email, password)

    _LOGGER.debug('Setting up sensor(s)...')

    sensors = []
    if show_usage:
        sensors .append(GreenelyUsageSensor(SENSOR_USAGE_NAME, api, usage_days, show_hourly, hourly_offset_days, date_format, time_format))
    if show_sold:
        sensors .append(GreenelySoldSensor(SENSOR_SOLD_NAME, api, sold_measure, sold_daily, date_format))
    if show_prices:
        sensors .append(GreenelyPricesSensor(SENSOR_PRICES_NAME, api, date_format))
    async_add_entities(sensors , True)

class GreenelyPricesSensor(Entity):
    def __init__(self, name, api, date_format):
        self._name = name
        self._icon = "mdi:account-cash"
        self._state = 0
        self._state_attributes = {}
        self._unit_of_measurement = 'kr'
        self._date_format = date_format
        self._api = api

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

    def update(self):
        """Update state and attributes."""
        _LOGGER.debug('Checking jwt validity...')
        if self._api.check_auth():
            data = self._api.get_price_data()
            if data:
                value = data['current_month']['value'] if data['current_month'] else 0
                self._state_attributes['current_month_value'] = (value / 100) if value != 0 and value != None else 0
                for condition in MONITORED_CONDITIONS_DEFAULT:
                    if condition == 'current_month':
                        self.make_data_attribute(condition, data.get(condition, None), 'cost_in_kr')
                    elif condition == 'current_price':
                        self._state = str(data.get(condition, None) / 100)
                    else:
                        self._state_attributes[condition] = data.get(condition, None)
            spot_price_data = self._api.get_spot_price()
            if spot_price_data:
                _LOGGER.debug('Fetching daily prices...')
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                todaysData = []
                tomorrowsData = []
                yesterdaysData = []
                for d in spot_price_data['data']:
                    timestamp = datetime.strptime(spot_price_data['data'][d]['localtime'], '%Y-%m-%d %H:%M')
                    if timestamp.date() == today.date():
                        if spot_price_data['data'][d]['price'] != None:
                            todaysData.append(self.make_attribute(spot_price_data, d))
                    elif timestamp.date() == (today.date() + timedelta(days=1)):
                        if spot_price_data['data'][d]['price'] != None:
                            tomorrowsData.append(self.make_attribute(spot_price_data, d))
                    elif timestamp.date() == (today.date() - timedelta(days=1)):
                        if spot_price_data['data'][d]['price'] != None:
                            yesterdaysData.append(self.make_attribute(spot_price_data, d))
                self._state_attributes['current_day'] = todaysData
                self._state_attributes['next_day'] = tomorrowsData
                self._state_attributes['previous_day'] = yesterdaysData
        else:
            _LOGGER.error('Unable to log in!')

    def make_attribute(self, response, value):
        if response: 
            newPoint = {}
            price = response['data'][value]['price']
            dt_object = datetime.strptime(response['data'][value]['localtime'], '%Y-%m-%d %H:%M')
            newPoint['date'] = dt_object.strftime(self._date_format)
            newPoint['time'] = dt_object.strftime("%H:%M")
            if price != None:
                newPoint['price'] = str(price / 1000)
            else:
                newPoint['price'] = 0
            return newPoint

    def make_data_attribute(self, name, response, nameOfPriceAttr):
        if response: 
            points = response.get('points', None)
            data = []
            for point in points:
                price = point[nameOfPriceAttr]
                if price != None:
                    newPoint = {}
                    dt_object = datetime.utcfromtimestamp(point['timestamp'])
                    newPoint['date'] = dt_object.strftime(self._date_format)
                    newPoint['time'] = dt_object.strftime("%H:%M")
                    newPoint['price'] = str(price / 100)
                    data.append(newPoint)
            self._state_attributes[name] = data
     
class GreenelyUsageSensor(Entity):
    def __init__(self, name, api, usage_days, show_hourly, hourly_offset_days, date_format, time_format):
        self._name = name
        self._icon = "mdi:power-socket-eu"
        self._state = 0
        self._state_attributes = {}
        self._unit_of_measurement = 'kWh'
        self._usage_days = usage_days
        self._show_hourly = show_hourly
        self._date_format = date_format
        self._time_format = time_format
        self._hourly_offset_days = hourly_offset_days
        self._api = api

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

    def update(self):
        _LOGGER.debug('Checking jwt validity...')
        if self._api.check_auth():
            # Get todays date
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            _LOGGER.debug('Fetching usage data...')
            data = []
            for i in range(self._usage_days):
                previous_day = today - timedelta(days=i)
                response = self._api.get_usage(str(previous_day.year), str(previous_day.month), str(previous_day.day))
                if response:
                    usage = self.make_attribute(previous_day, today, response)
                    if usage:
                        data.append(usage)
            self._state_attributes['days'] = data
        else:
            _LOGGER.error('Unable to log in!')

    def make_attribute(self, date, today, response):
        points = response.get('points', None)
        yesterday = today - timedelta(days = 1)
        hourly_day = today - timedelta(days = self._hourly_offset_days)
        daily_usage = 0
        data = {}
        hourly_data = []
        for point in points:
            usage = point['usage']
            if (date == hourly_day):
                daily_data = {}
                time = datetime.utcfromtimestamp(point['timestamp'])
                daily_data['time'] = time.strftime(self._time_format)
                hourly_day_usage = point['usage']
                daily_data['usage'] = str(hourly_day_usage / 1000) if hourly_day_usage != 0 and hourly_day_usage != None else str(0)
                hourly_data.append(daily_data)
            if usage != None and usage != 0:
                daily_usage += usage
        if daily_usage != 0:
            data['date'] = date.strftime(self._date_format)
            data['usage'] = str(daily_usage / 1000)
        if (date == yesterday):
            self._state = data['usage'] if daily_usage != 0 else 0
        if (date == hourly_day):
            if self._show_hourly:
                self._state_attributes['hourly'] = hourly_data
        return data

class GreenelySoldSensor(Entity):
    def __init__(self, name, api, sold_measure, sold_daily, date_format):
        self._name = name
        self._icon = "mdi:solar-power"
        self._state = 0
        self._state_attributes = {}
        self._unit_of_measurement = 'kWh'
        self._date_format = date_format
        self._sold_measure = sold_measure
        self._sold_daily = sold_daily
        self._api = api

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

    def update(self):
        _LOGGER.debug('Checking jwt validity...')
        if self._api.check_auth():
            _LOGGER.debug('Fetching sold data...')
            response = self._api.get_sold(self._sold_measure, self._sold_daily)
            if response:
                self.make_attribute(response)
        else:
            _LOGGER.error('Unable to log in!')

    def make_attribute(self, response):
        total_sold = 0
        months = []
        jsonObject = json.loads(json.dumps(response))
        for key in jsonObject:
            data = {}
            value = jsonObject[key]
            usage = value['usage']

            date = datetime.strptime(value['localtime'], "%Y-%m-%d %H:%M")
            data['date'] = date.strftime(self._date_format)
            data['usage'] = str(usage / 1000) if usage != 0 else 0
            data['is_complete'] = value['is_complete']

            total_sold += usage
            if data:
                months.append(data)
        self._state = str(total_sold / 1000) if total_sold != 0 else 0
        self._state_attributes['sold_data'] = months
