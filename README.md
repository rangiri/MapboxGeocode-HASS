# Mapbox Geocode

This component has been created to be used with Home Assistant.

Mapbox geocode is the process of converting device tracker location into a human-readable address.

The sensor will update the address each time the device tracker location changes. If the device tracker is in a zone it will display the zone.

### Credit

Full credit for this component lies with [michaelmcarthur](https://github.com/michaelmcarthur).

### Installation:

Copy the manifest.json file and place it in <config_dir>/custom_components/mapbox_geocode/manifest.json

Copy the sensor.py file and place it in <config_dir>/custom_components/mapbox_geocode/sensor.py

### Example Screenshot:
![alt text](https://github.com/rangiri/MapboxGeocode-HASS/blob/master/Mapbox_Geocode_Screenshot.png "Screenshot")

### Example entry for configuration.yaml
```
sensor:

  - platform: mapbox_geocode
    origin: device_tracker.mobile_phone
```
### Configuration variables:

origin (Required): Tracking can be setup to track entity type device_tracker. The component updates it will use the latest location of that entity and update the sensor.

name (Optional): A name to display on the sensor. The default is “Mapbox Geocode"

options (Optional): Select what level of address information you want. Choices are 'street_number', 'street', 'city', 'county', 'state', 'postal_code', 'country' or 'formatted_address'. You can use any combination of these options, separate each option with a comma. The default is “street, city"

display_zone (Optional): Choose to display a zone when in a zone. Choices are 'show' or 'hide'. The default is 'show'

gravatar (Optional): An email address for the device’s owner. You can set up a Gravatar [here.](https://gravatar.com) If provided, it will override `picture` The default is 'none'

api_key (Optional): Your application’s API key (get one by following the instructions below). This key identifies your application for purposes of quota management. 

You need to register for an API key to use Mapbox Geocode. This can be done by following these instructions
*** WIP


### Example with optional entry for configuration.yaml
```
- platform: mapbox_geocode
  name: johnny
  origin: device_tracker.mobile_phone
  options: street_number, street, city
  display_zone: hide
  gravatar: youremail@address.com
  api_key: XXXX_XXXXX_XXXXX
```
