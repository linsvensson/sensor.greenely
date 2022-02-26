import json
import logging
from datetime import datetime, timedelta

import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.entity import Entity

__version__ = '1.0.0'

_LOGGER = logging.getLogger(__name__)

SENSOR_USAGE_NAME = 'Greenely Usage'
SENSOR_SOLD_NAME = 'Greenely Sold'
SENSOR_PRICES_NAME = 'Greenely Prices'

DATE_FORMAT_DEFAULT = '%b %d %Y'
TIME_FORMAT_DEFAULT = '%H:%M'
USAGE_DAYS_DEFAULT = 10
SOLD_MEASURE_DEFAULT = 2
SHOW_HOURLY_DEFAULT = False
SOLD_DAILY_DEFAULT = False

CONF_EMAIL = 'email'
CONF_PASSWORD = 'password'

CONF_USAGE_DAYS = 'usage_days'
CONF_USAGE = 'usage'
CONF_SOLD = 'sold'
CONF_SOLD_MEASURE = 'sold_measure'
CONF_SOLD_DAILY = 'sold_daily'
CONF_PRICES = 'prices'
CONF_SHOW_HOURLY = 'show_hourly'
CONF_DATE_FORMAT = 'date_format'
CONF_TIME_FORMAT = 'time_format'

MONITORED_CONDITIONS_DEFAULT = [
    'is_retail_customer',
    'current_price',
    'referral_discount_in_kr',
    'has_unpaid_invoices',
    'yearly_savings_in_kr',
    'timezone',
    'retail_termination_date',
    'current_day',
    'next_day',
    'current_month'
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_USAGE): cv.boolean,
    vol.Optional(CONF_SOLD): cv.boolean,
    vol.Optional(CONF_PRICES): cv.boolean,
    vol.Optional(CONF_USAGE_DAYS): cv.positive_int,
    vol.Optional(CONF_SOLD_MEASURE): cv.positive_int,
    vol.Optional(CONF_SOLD_DAILY): cv.boolean,
    vol.Optional(CONF_DATE_FORMAT): cv.string,
    vol.Optional(CONF_TIME_FORMAT): cv.string,
    vol.Optional(CONF_SHOW_HOURLY): cv.boolean,
})

SCAN_INTERVAL = timedelta(minutes=60)

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the Greenely sensor."""
    email = config.get(CONF_EMAIL)
    password = config.get(CONF_PASSWORD)
    
    date_format = config.get(CONF_DATE_FORMAT)
    if date_format is None:
        date_format = DATE_FORMAT_DEFAULT 
    time_format = config.get(CONF_TIME_FORMAT)
    if time_format is None:
        time_format = TIME_FORMAT_DEFAULT 
    show_usage = config.get(CONF_USAGE)
    if show_usage is None:
        show_usage = True
    show_sold = config.get(CONF_SOLD)
    if show_sold is None:
        show_sold = False
    show_prices = config.get(CONF_PRICES)
    if show_prices is None:
        show_prices = True
    usage_days = config.get(CONF_USAGE_DAYS)
    if usage_days is None:
        usage_days = USAGE_DAYS_DEFAULT
    sold_measure = config.get(CONF_SOLD_MEASURE)
    if sold_measure is None:
        sold_measure = SOLD_MEASURE_DEFAULT
    show_hourly = config.get(CONF_SHOW_HOURLY)
    if show_hourly is None:
        show_hourly = SHOW_HOURLY_DEFAULT
    sold_daily = config.get(CONF_SOLD_DAILY)
    if sold_daily is None:
        sold_daily = SOLD_DAILY_DEFAULT
        
    api = GreenelyAPI(email, password)
    entities = []
    if show_usage:
        entities.append(GreenelyUsageSensor(SENSOR_USAGE_NAME, api, usage_days, show_hourly, date_format, time_format))
    if show_sold:
        entities.append(GreenelySoldSensor(SENSOR_SOLD_NAME, api, sold_measure, sold_daily, date_format))
    if show_prices:
        entities.append(GreenelyPricesSensor(SENSOR_PRICES_NAME, api, date_format))
    async_add_entities(entities, True)

class GreenelyPricesSensor(Entity):
    """Representation of a Greenely sensor."""

    def __init__(self, name, api, date_format):
        """Initialize a Greenely sensor."""
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
            data = self._api.get_data()
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
                    timestamp = datetime.utcfromtimestamp(int(d))
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
    """Representation of a Greenely usage sensor."""

    def __init__(self, name, api, usage_days, show_hourly, date_format, time_format):
        """Initialize a Greenely usage sensor."""
        self._name = name
        self._icon = "mdi:power-socket-eu"
        self._state = 0
        self._state_attributes = {}
        self._unit_of_measurement = 'kWh'
        self._usage_days = usage_days
        self._show_hourly = show_hourly
        self._date_format = date_format
        self._time_format = time_format
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
        daily_usage = 0
        data = {}
        yesterday_data = []
        for point in points:
            usage = point['usage']
            if (date == yesterday):
                daily_data = {}
                time = datetime.utcfromtimestamp(point['timestamp'])
                daily_data['time'] = time.strftime(self._time_format)
                yesterday_usage = point['usage']
                daily_data['usage'] = str(yesterday_usage / 1000) if yesterday_usage != 0 and yesterday_usage != None else str(0)
                yesterday_data.append(daily_data)
            if usage != None and usage != 0:
                daily_usage += usage
        if daily_usage != 0:
            data['date'] = date.strftime(self._date_format)
            data['usage'] = str(daily_usage / 1000)
        if (date == yesterday):
             self._state = data['usage'] if daily_usage != 0 else 0
             if self._show_hourly:
                self._state_attributes['hourly'] = yesterday_data
        return data

class GreenelySoldSensor(Entity):
    """Representation of a Greenely sold sensor."""

    def __init__(self, name, api, sold_measure, sold_daily, date_format):
        """Initialize a Greenely sold sensor."""
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

class GreenelyAPI():
    """Greenely API."""

    def __init__(self, email, password):
        """Initialize Greenely API."""
        self._jwt = ''
        self._url_check_auth = 'https://api2.greenely.com/v1/checkauth'
        self._url_login = 'https://api2.greenely.com/v1/login'
        self._url_retail = 'https://api2.greenely.com/v2/retail/overview'
        self._url_data = 'https://api2.greenely.com/v3/data/'
        self._url_sold = 'https://api2.greenely.com/v1/facilities/'
        self._url_spot_price = 'https://api2.greenely.com/v1/facilities/'
        self._url_facilities = 'https://api2.greenely.com/v1/facilities/primary?includes=retail_state&includes=consumption_limits&includes=parameters'
        self._headers = {'Accept-Language':'sv-SE', 
            'User-Agent':'Android 2 111',
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization':self._jwt}    
        self._email = email
        self._password = password
        self._facility_id = ''

    def get_data(self):
        """Get the price data from the Greenely API."""
        response = requests.get(self._url_retail, headers = self._headers)
        data = {}
        if response.status_code == requests.codes.ok:
            data = response.json()
            return data['data']
        else:
            _LOGGER.error('Failed to get price data, %s', response.text)
            return data

    def get_spot_price(self):
        """Get the spot price data from the Greenely API."""
        today = datetime.today()
        yesterday = today - timedelta(days = 1)
        tomorrow = today + timedelta(days = 2)
        start = "?from=" + str(yesterday.year) + "-" + yesterday.strftime("%m") + "-" + yesterday.strftime("%d")
        end = "&to=" + str(tomorrow.year) + "-" + tomorrow.strftime("%m") + "-" + tomorrow.strftime("%d")
        url = self._url_spot_price + self._facility_id + "/spot-price" + start + end + "&resolution=hourly"
        response = requests.get(url, headers = self._headers)
        data = {}
        if response.status_code == requests.codes.ok:
            data = response.json()
            return data
        else:
            _LOGGER.error('Failed to get price data, %s', response.text)
            return data
            
    def get_usage(self, year, month, day):
        """Get usage data from the Greenely API."""
        url = self._url_data + year + "/" + month + "/" + day + "/usage"
        response = requests.get(url, headers = self._headers)
        data = {}
        if response.status_code == requests.codes.ok:
            data = response.json()
            return data['data']
        else:
            _LOGGER.error('Failed to fetch usage data for %s/%s/%s, %s', year, month, day, response.text)
            return data

    def get_sold(self, sold_measure, sold_daily):
        """Get sold data from the Greenely API."""
        today = datetime.today()
        if sold_daily == False:
            resolution = "&resolution=monthly"
            first_month = today
            if today.month == 1:
                first_month = today.replace(year=today.year - 1, month=12)
            else:
                extra_days = 0
            while True:
                try:
                    first_month = today.replace(month=today.month - (sold_measure -1), day=today.day - extra_days)
                    break
                except ValueError:
                    extra_days += 1
            start = "from=" + str(first_month.year) + "-" + first_month.strftime("%m") + "-" + first_month.strftime("%d")
        else:
            resolution = "&resolution=daily"
            first_date = today - timedelta(days = sold_measure)
            start = "from=" + str(first_date.year) + "-" + first_date.strftime("%m") + "-" + first_date.strftime("%d")
        end = "&to=" + str(today.year) + "-" + today.strftime("%m") + "-" + today.strftime("%d")
        url = self._url_sold + self._facility_id + "/sold-electricity?" + start + end + resolution
        response = requests.get(url, headers = self._headers)
        data = {}
        if response.status_code == requests.codes.ok:
            data = response.json()
            return data['data']
        else:
            _LOGGER.error('Failed to fetch sold data from %s, %s', first_month.strftime("%d/%m/%Y"), response.text)
            return data

    def get_facility_id(self):
        """Get the facility id."""
        result = requests.get(self._url_facilities, headers = self._headers)
        if result.status_code == requests.codes.ok:
            _LOGGER.debug('jwt is valid!')
            data = result.json()
            self._facility_id = str(data['data']['parameters']['facility_id'])
        else:
            _LOGGER.error('Failed to fetch facility id %s', result.text)

    def check_auth(self):
        """Check to see if our jwt is valid."""
        result = requests.get(self._url_check_auth, headers = self._headers)
        if result.status_code == requests.codes.ok:
            _LOGGER.debug('jwt is valid!')
            return True
        else: 
            if self.login() == False:
                _LOGGER.debug(result.text)
                return False
        return True
        
    def login(self):
        """Login to the Greenely API."""
        result = False
        loginInfo = {'email':self._email, 
            'password':self._password} 
        loginResult = requests.post(self._url_login, headers = self._headers, data = json.dumps(loginInfo))
        if loginResult.status_code == requests.codes.ok:
            jsonResult = loginResult.json()
            self._jwt = "JWT " + jsonResult['jwt']
            self._headers['Authorization'] = self._jwt
            _LOGGER.debug('Successfully logged in and updated jwt')
            self.get_facility_id()
            result = True           
        else:
            _LOGGER.error(loginResult.text)
        return result
