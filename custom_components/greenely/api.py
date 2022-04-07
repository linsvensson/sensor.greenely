import logging
from datetime import datetime, timedelta
import requests
import json

_LOGGER = logging.getLogger(__name__)

class GreenelyApi:
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
