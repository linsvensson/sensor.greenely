"""Greenely API"""
import logging
from datetime import datetime, timedelta
import requests
import json

_LOGGER = logging.getLogger(__name__)

class GreenelyApi:
    def __init__(self, email, password):
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

    def get_price_data(self):
        response = requests.get(self._url_retail, headers = self._headers)
        data = {}
        if response.status_code == requests.codes.ok:
            data = response.json()
            return data['data']
        else:
            _LOGGER.error('Failed to get price data, %s', response.text)
            return data

    def get_spot_price(self):
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
        url = self._url_data + year + "/" + month + "/" + day + "/usage"
        response = requests.get(url, headers = self._headers)
        data = {}
        if response.status_code == requests.codes.ok:
            data = response.json()
            return data['data']
        else:
            _LOGGER.error('Failed to fetch usage data for %s/%s/%s, %s', year, month, day, response.text)
            return data

    def get_facility_id(self):
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