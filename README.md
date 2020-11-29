# sensor.greenely
[![GitHub last commit](https://img.shields.io/github/last-commit/linsvensson/sensor.greenely)](https://github.com/linsvensson/sensor.greenely)

_Custom component to get usage data and prices from [Greenely](https://www.greenely.se/) for [Home Assistant](https://www.home-assistant.io/)._

Because Greenely doesn't have an open api yet, we are using the Android user-agent to access data.
Data is fetched every hour.

## Installation
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `greenely`.
4. Download _all_ the files from the `custom_components/greenely/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Add a sensor `- platform: greenely` to your HA configuration.

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/greenely/__init__.py
custom_components/greenely/sensor.py
custom_components/greenely/manifest.json
```

## Configuration
key | type | description
:--- | :--- | :---
**platform (Required)** | string | `greenely`
**email (Required)** | string | Your Greenely username.
**password (Required)** | string | Your Greenely password.
**usage (Optional)** | boolean | Creates a sensor showing usage data. Default `true`.
**prices (Optional)** | boolean | Creates a sensor showing price data. Default `true`.
**usage_days (Optional)** | number | How many days of usage data you want. Default `10`.
**date_format (Optional)** | string | Default `%b %d %Y`, shows up as `Jan 18 2020`. [References](https://strftime.org/)

## Example
**Configuration with default settings:**
```yaml
sensor:
  - platform: greenely
    email: test@gmail.com
    password: 1234
```

**Configuration with custom settings:**
```yaml
sensor:
  - platform: greenely
    email: test@gmail.com
    password: 1234
    usage: true
    prices: false
    usage_days: 4
    date_format: '%d/%m/%Y'
```

## Lovelace
**Example usage with [flex-table-card](https://github.com/custom-cards/flex-table-card):**
```yaml
- type: 'custom:flex-table-card'
  title: Greenely Usage
  sort_by: date
  entities:
    include: sensor.greenely_usage
  columns:
    - name: date
      attr_as_list: days
      modify: x.date
      icon: mdi:calendar
    - name: kWh
      attr_as_list: days
      modify: x.usage
      icon: mdi:flash
```

![image](https://user-images.githubusercontent.com/5594088/72650563-2b67aa80-3981-11ea-8101-d54dfb337ee8.PNG)

**Example prices with [flex-table-card](https://github.com/custom-cards/flex-table-card):**
```yaml
- type: custom:vertical-stack-in-card
  cards:
    - type: horizontal-stack
      cards:
        - type: 'custom:flex-table-card'
          title: Today
          sort_by: date
          entities:
            include: sensor.greenely_prices
          columns:
            - name: time
              attr_as_list: current_day
              modify: x.time
              icon: mdi:clock
            - name: price(öre/kWh)
              attr_as_list: current_day
              modify: Math.round(x.price * 10) / 10
              icon: mdi:cash
        - type: 'custom:flex-table-card'
          title: Tomorrow
          sort_by: date
          entities:
            include: sensor.greenely_prices
          columns:
            - name: time
              attr_as_list: next_day
              modify: x.time
              icon: mdi:clock
            - name: price(öre/kWh)
              attr_as_list: next_day
              modify: Math.round(x.price * 10) / 10
              icon: mdi:cash
```

![image](https://user-images.githubusercontent.com/5594088/72912188-8e6b8f80-3d3b-11ea-8072-096571fecd41.PNG)

## Data object structures
**current_day, next_day & current_month**
```json
[{ "date": "Jan 18 2020", "time": "13:00", "price": "24.75" }]
```
**days**
```json
[{ "date": "Jan 12 2020", "usage": "1.0" }]
```
