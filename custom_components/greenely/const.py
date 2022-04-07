SENSOR_USAGE_NAME = 'Greenely Usage'
SENSOR_SOLD_NAME = 'Greenely Sold'
SENSOR_PRICES_NAME = 'Greenely Prices'

# Component domain, used to store component data in hass data.
DOMAIN = 'greenely'
CONFIG = 'config'
API = 'api'

CONF_DATA = 'data'
DATA_LIST = ''
CONF_USAGE_DAYS = 'usage_days'
CONF_USAGE = 'usage'
CONF_SOLD = 'sold'
CONF_SOLD_MEASURE = 'sold_measure'
CONF_SOLD_DAILY = 'sold_daily'
CONF_PRICES = 'prices'
CONF_SHOW_HOURLY = 'show_hourly'
CONF_DATE_FORMAT = 'date_format'
CONF_TIME_FORMAT = 'time_format'
CONF_HOURLY_OFFSET_DAYS = 'hourly_offset_days'

DATA_PRICES = 'prices'
DATA_USAGE = 'usage'
DATA_SOLD = 'sold'

DATA_LIST = [
    'prices',
    'usage',
]

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