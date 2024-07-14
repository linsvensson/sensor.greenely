"""Greenely API"""

from datetime import datetime, timedelta
import json
import logging

import httpx

_LOGGER = logging.getLogger(__name__)


class GreenelyApi:
    def __init__(self, email, password):
        self._jwt = ""
        self._url_check_auth = "https://api2.greenely.com/v1/checkauth"
        self._url_login = "https://api2.greenely.com/v1/login"
        self._url_data = "https://api2.greenely.com/v3/data/"
        self._url_facilities_base = "https://api2.greenely.com/v1/facilities/"
        self._headers = {
            "Accept-Language": "sv-SE",
            "User-Agent": "Android 2 111",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": self._jwt,
        }
        self._email = email
        self._password = password
        self._facility_id = "primary"

    def get_price_data(self):
        today = datetime.today()
        nextMonth = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        start = "?from=" + str(today.year) + "-" + today.strftime("%m") + "-01"
        end = "&to=" + str(nextMonth.year) + "-" + nextMonth.strftime("%m") + "-01"
        url = (
            self._url_facilities_base
            + self._facility_id
            + "/consumption"
            + start
            + end
            + "&resolution=daily&unit=currency&operation=sum"
        )
        response = httpx.get(url, headers=self._headers)
        data = {}
        if response.status_code == httpx.codes.ok:
            data = response.json()
            return data["data"]
        else:
            _LOGGER.error("Failed to get price data, %s", response.text)
            return data

    def get_spot_price(self):
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=2)
        start = (
            "?from="
            + str(yesterday.year)
            + "-"
            + yesterday.strftime("%m")
            + "-"
            + yesterday.strftime("%d")
        )
        end = (
            "&to="
            + str(tomorrow.year)
            + "-"
            + tomorrow.strftime("%m")
            + "-"
            + tomorrow.strftime("%d")
        )
        url = (
            self._url_facilities_base
            + self._facility_id
            + "/spot-price"
            + start
            + end
            + "&resolution=hourly"
        )
        response = httpx.get(url, headers=self._headers)
        data = {}
        if response.status_code == httpx.codes.ok:
            data = response.json()
            return data
        else:
            _LOGGER.error("Failed to get spot price data, %s", response.text)
            return data

    def get_usage(self, startDate, endDate, showHourly):
        start = (
            "?from="
            + str(startDate.year)
            + "-"
            + startDate.strftime("%m")
            + "-"
            + str(startDate.day)
        )
        end = (
            "&to="
            + str(endDate.year)
            + "-"
            + endDate.strftime("%m")
            + "-"
            + str(endDate.day)
        )
        resolution = "hourly" if showHourly else "daily"
        url = (
            self._url_facilities_base
            + self._facility_id
            + "/consumption"
            + start
            + end
            + "&resolution="
            + resolution
        )
        response = httpx.get(url, headers=self._headers)
        data = {}
        if response.status_code == httpx.codes.ok:
            data = response.json()
            return data["data"]
        else:
            _LOGGER.error("Failed to fetch usage data, %s", response.text)
            return data

    def get_facility_id(self):
        result = httpx.get(self._url_facilities_base, headers=self._headers)
        if result.status_code == httpx.codes.ok:
            data = result.json()["data"]
            facility = next((f for f in data if f["is_primary"] == True), None)
            if facility == None:
                _LOGGER.debug(
                    "Found no primary facility, using the first one in the list!"
                )
                facility = data[0]
            self._facility_id = str(data[0]["id"])
            _LOGGER.debug("Fetched facility id %s", self._facility_id)
            return self._facility_id
        else:
            _LOGGER.error("Failed to fetch facility id %s", result.reason)

    def get_produced_electricity(self, startDate, endDate, showHourly):
        start = (
            "?from="
            + str(startDate.year)
            + "-"
            + startDate.strftime("%m")
            + "-"
            + startDate.strftime("%d")
        )
        end = (
            "&to="
            + str(endDate.year)
            + "-"
            + endDate.strftime("%m")
            + "-"
            + endDate.strftime("%d")
        )
        resolution = "hourly" if showHourly else "daily"
        url = (
            self._url_facilities_base
            + self._facility_id
            + "/produced-electricity"
            + start
            + end
            + "&resolution="
            + resolution
        )
        _LOGGER.debug("Fetching produced electicity from url, %s", url)
        response = httpx.get(url, headers=self._headers)
        data = {}
        if response.status_code == httpx.codes.ok:
            data = response.json()
            _LOGGER.debug(
                "Fetched data for produced electricity endpoint, %s", data["data"]
            )
            return data["data"]
        else:
            _LOGGER.error(
                "Failed to fetch produced electricity data, %s", response.text
            )
            return data

    def check_auth(self):
        """Check to see if our jwt is valid."""
        result = httpx.get(self._url_check_auth, headers=self._headers)
        if result.status_code == httpx.codes.ok:
            _LOGGER.debug("jwt is valid!")
            return True
        elif self.login() == False:
            _LOGGER.debug(result.text)
            return False
        return True

    def login(self):
        """Login to the Greenely API."""
        result = False
        loginInfo = {"email": self._email, "password": self._password}
        loginResult = httpx.post(
            self._url_login, headers=self._headers, data=json.dumps(loginInfo)
        )
        if loginResult.status_code == httpx.codes.ok:
            jsonResult = loginResult.json()
            self._jwt = "JWT " + jsonResult["jwt"]
            self._headers["Authorization"] = self._jwt
            _LOGGER.debug("Successfully logged in and updated jwt")
            if self._facility_id == "primary":
                self.get_facility_id()
            else:
                _LOGGER.debug("Facility id is %s", self._facility_id)
            result = True
        else:
            _LOGGER.error(loginResult.text)
        return result
