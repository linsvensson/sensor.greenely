import json
import logging
from datetime import datetime, timedelta

import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.entity import Entity

__version__ = '1.0.0'

_LOGGER = logging.getLogger(__name__)

SENSOR_USAGE_NAME = 'Greenely Usage'
SENSOR_PRICES_NAME = 'Greenely Prices'

CONF_EMAIL = 'email'
CONF_PASSWORD = 'password'
CONF_JWT = 'jwt'

CONF_USAGE_DAYS = 'usage_days'
CONF_USAGE = 'usage'
CONF_PRICES = 'prices'

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

MONITORED_CONDITIONS_USAGE_POINTS = [
    'usage',
    'timestamp',
]

MONITORED_POINTS = [
    'points',
]

MONITORED_CONDITIONS_POINTS = [
    'price',
    'timestamp',
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_USAGE): cv.boolean,
    vol.Optional(CONF_PRICES): cv.boolean,
    vol.Optional(CONF_USAGE_DAYS): cv.positive_int,
})

SCAN_INTERVAL = timedelta(minutes=60)

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the Greenely sensor."""
    jwt = config.get(CONF_JWT)
    email = config.get(CONF_EMAIL)
    password = config.get(CONF_PASSWORD)
    
    show_usage = config.get(CONF_USAGE)
    if show_usage is None:
        show_usage = True
    show_prices = config.get(CONF_PRICES)
    if show_prices is None:
        show_prices = True
    usage_days = config.get(CONF_USAGE_DAYS)
    if usage_days is None:
        usage_days = 10
        
    api = GreenelyAPI(email, password, jwt)
    entities = []
    if show_usage:
        entities.append(GreenelyUsageSensor(SENSOR_USAGE_NAME, api, usage_days))
    if show_prices:
        entities.append(GreenelyPricesSensor(SENSOR_PRICES_NAME, api))
    async_add_entities(entities, True)

class GreenelyPricesSensor(Entity):
    """Representation of a Greenely sensor."""

    def __init__(self, name, api):
        """Initialize a Greenely sensor."""
        self._name = name
        self._icon = "mdi:account-cash"
        self._state = 0
        self._state_attributes = {}
        self._unit_of_measurement = 'kr'
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
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    def update(self):
        """Update state and attributes."""
        _LOGGER.debug('Checking jwt validity...')
        self._api.check_auth()
        
        data = self._api.get_data()
        if data:
            _LOGGER.debug('Fetching daily prices...')
            self._state =  data['current_month']['value'] / 100
            for condition in MONITORED_CONDITIONS_DEFAULT:
                self._state_attributes[condition] = data.get(condition, None)         
     
class GreenelyUsageSensor(Entity):
    """Representation of a Greenely usage sensor."""

    def __init__(self, name, api, usage_days):
        """Initialize a Greenely usage sensor."""
        self._name = name
        self._icon = "mdi:power-socket-eu"
        self._state = 0
        self._state_attributes = {}
        self._unit_of_measurement = 'kWh'
        self._usage_days = usage_days
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
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    def update(self):
        _LOGGER.debug('Checking jwt validity...')
        self._api.check_auth()

        # Get todays date
        today = datetime.now()
        _LOGGER.debug('Fetching usage data...')
        for i in range(self._usage_days):
            previous_day = today - timedelta(days=i)
            response = self._api.get_usage(str(previous_day.year), str(previous_day.month), str(previous_day.day))
            if response:
                self.make_attribute(previous_day, response, i)

    def make_attribute(self, date, response, index):
        points = response.get('points', None)
        day = []
        for point in points:
            usage = point['usage']
            if usage != None and usage != 0:
                newPoint = {}
                newPoint['date'] = date.strftime("%d/%m/%Y")
                dt_object = datetime.fromtimestamp(point['timestamp'])
                newPoint['time'] = dt_object.strftime("%H:%M")
                newPoint['value'] = str(usage / 1000)
                day.append(newPoint)
        self._state_attributes['day{}'.format(index)] = json.dumps(day)

class GreenelyAPI():
    """Greenely API."""

    def __init__(self, email, password, jwt):
        """Initialize Greenely API."""
        self._url_check_auth = 'https://api2.greenely.com/v1/checkauth'
        self._url_login = 'https://api2.greenely.com/v1/login'
        self._url_retail = 'https://api2.greenely.com/v2/retail/overview'
        self._url_data = 'https://api2.greenely.com/v3/data/'
        self._headers = {'Accept-Language':'sv-SE', 
            'User-Agent':'Android 2 111',
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization':jwt}    
        self._jwt = jwt
        self._email = email
        self._password = password

    def get_data(self):
        """Get the price data from the Greenely API."""
        response = requests.get(self._url_retail, headers = self._headers)
        data = {}
        if response.status_code == requests.codes.ok:
            data = response.json()
            return data['data']
        else:
            _LOGGER.debug('Failed to get price data, %s', response.text)
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
            _LOGGER.debug('Failed to fetch usage data for %s/%s/%s, %s', year, month, day, response.text)
            return data

    def check_auth(self):
        """Check to see if our jwt is valid."""
        result = requests.post(self._url_check_auth, headers = self._headers)
        if result.status_code == requests.codes.ok:
            _LOGGER.debug('jwt is valid!')    
        else: 
            if self.login() == False:
                _LOGGER.debug(result.text)  
        
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
            _LOGGER.debug('Sucessfully logged in and updated jwt')
            result = True           
        else:
            _LOGGER.debug(loginResult.text)
        return result