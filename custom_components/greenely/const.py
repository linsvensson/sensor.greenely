"""Constants for the greenely sensors"""

SENSOR_USAGE_NAME = 'Greenely Usage'
SENSOR_SOLD_NAME = 'Greenely Sold'
SENSOR_PRICES_NAME = 'Greenely Prices'

DOMAIN = 'greenely'

CONF_PRICES = 'prices'
CONF_USAGE = 'usage'
CONF_SOLD = 'sold'
CONF_SOLD_MEASURE = 'sold_measure'
CONF_SOLD_DAILY = 'sold_daily'
CONF_USAGE_DAYS = 'usage_days'
CONF_SHOW_HOURLY = 'show_hourly'
CONF_DATE_FORMAT = 'date_format'
CONF_TIME_FORMAT = 'time_format'
CONF_HOURLY_OFFSET_DAYS = 'hourly_offset_days'

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