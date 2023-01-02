---
layout: page
title: "Mapbox Geocode"
description: "Convert device tracker location into a human-readable address."
date: 2023-01-02 11:00
sidebar: true
comments: false
sharing: true
footer: true
logo: mapbox_maps.png
ha_category: Sensor
ha_iot_class: "Cloud Polling"
ha_release: 0.6
---



The `mapbox_geocode` sensor converts device tracker location into a human-readable address.

The sensor will update the address each time the device tracker location changes. If the device tracker is in a zone it will display the zone.

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

display_zone (Optional): Choose to display a zone when in a zone. Choices are 'show' or 'hide'. The default is “show"

### Example with optional entry for configuration.yaml
```
- platform: mapbox_geocode
  name: michael
  origin: device_tracker.mobile_phone
  options: street_number, street, city
  display_zone: hide
```

Powered by [Mapbox](http://www.mapbox.com/)
