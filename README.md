# sensor.greenely
_Custom component to get usage data and prices from [Greenely](https://www.greenely.se/) for [Home Assistant](https://www.home-assistant.io/)._

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
**password (Required)** | string | Your Greenely password. Custom name for the sensor. Default `avanza_stock_{stock}`.
**name (Optional)** | string | Custom name for the sensor. Default `greenely`.
**show_usage (Optional)** | boolean | . Default `false`.
**show_daily_prices (Optional)** | boolean | . Default `false`.
**usage_days (Optional)** | number | How many days of usage data you want. Default `10`.

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
    name: My Greenely Data
    email: test@gmail.com
    password: 1234
    show_usage: true
    show_daily_prices: true
    usage_days: 4
```
