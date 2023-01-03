"""
Support for Mapbox Geocode sensors.
For more details about this platform, please refer to the documentation at
https://github.com/rangiri/MapboxGeocode-HASS
"""
from datetime import datetime
from datetime import timedelta 
import logging
import json
import requests
from requests import get

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_API_KEY, CONF_NAME, CONF_SCAN_INTERVAL, ATTR_ATTRIBUTION, ATTR_LATITUDE, ATTR_LONGITUDE)
import homeassistant.helpers.location as location
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_ORIGIN = 'origin'
CONF_OPTIONS = 'options'
CONF_DISPLAY_ZONE = 'display_zone'
CONF_ATTRIBUTION = "Data provided by www.mapbox.com"
CONF_GRAVATAR = 'gravatar'
CONF_IMAGE = 'image'

ATTR_STREET_NUMBER = 'Street Number'
ATTR_STREET = 'Street'
ATTR_CITY = 'City'
ATTR_POSTAL_TOWN = 'Postal Town'
ATTR_POSTAL_CODE = 'Postal Code'
ATTR_REGION = 'State'
ATTR_COUNTRY = 'Country'
ATTR_COUNTY = 'County'
ATTR_FORMATTED_ADDRESS = 'Formatted Address'

DEFAULT_NAME = 'Mapbox Geocode'
DEFAULT_OPTION = 'street, city'
DEFAULT_DISPLAY_ZONE = 'display'
DEFAULT_KEY = 'no key'
current = '0,0'
zone_check = 'a'
SCAN_INTERVAL = timedelta(seconds=60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ORIGIN): cv.string,
    vol.Optional(CONF_API_KEY, default=DEFAULT_KEY): cv.string,
    vol.Optional(CONF_OPTIONS, default=DEFAULT_OPTION): cv.string,
    vol.Optional(CONF_DISPLAY_ZONE, default=DEFAULT_DISPLAY_ZONE): cv.string,
    vol.Optional(CONF_GRAVATAR, default=None): vol.Any(None, cv.string),
    vol.Optional(CONF_IMAGE, default=None): vol.Any(None, cv.string),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
})

TRACKABLE_DOMAINS = ['device_tracker', 'sensor', 'person']

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    name = config.get(CONF_NAME)
    api_key = config.get(CONF_API_KEY)
    origin = config.get(CONF_ORIGIN)
    options = config.get(CONF_OPTIONS)
    display_zone = config.get(CONF_DISPLAY_ZONE)
    gravatar = config.get(CONF_GRAVATAR) 
    image = config.get(CONF_IMAGE) 

    add_devices([MapboxGeocode(hass, origin, name, api_key, options, display_zone, gravatar, image)])

class MapboxGeocode(Entity):
    """Representation of a Mapbox Geocode Sensor."""

    def __init__(self, hass, origin, name, api_key, options, display_zone, gravatar, image):
        """Initialize the sensor."""
        self._hass = hass
        self._name = name
        self._api_key = api_key
        self._options = options.lower()
        self._display_zone = display_zone.lower()
        self._state = "Awaiting Update"
        self._gravatar = gravatar
        self._image = image

        self._street_number = None
        self._street = None
        self._city = None
        self._postal_town = None
        self._postal_code = None
        self._city = None
        self._region = None
        self._country = None
        self._county = None
        self._formatted_address = None
        self._zone_check_current = None

        # Check if origin is a trackable entity
        if origin.split('.', 1)[0] in TRACKABLE_DOMAINS:
            self._origin_entity_id = origin
        else:
            self._origin = origin

        if gravatar is not None:
            self._picture = self._get_gravatar_for_email(gravatar)
        elif image is not None:
            self._picture = self._get_image_from_url(image)
        else:
            self._picture = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def entity_picture(self):
        """Return the picture of the device."""
        return self._picture

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return{
            ATTR_STREET_NUMBER: self._street_number,
            ATTR_STREET: self._street,
            ATTR_CITY: self._city,
            ATTR_POSTAL_TOWN: self._postal_town,
            ATTR_POSTAL_CODE: self._postal_code,
            ATTR_REGION: self._region,
            ATTR_COUNTRY: self._country,
            ATTR_COUNTY: self._county,
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
            ATTR_FORMATTED_ADDRESS: self._formatted_address,
        }

    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Get the latest data and updates the states."""

        if hasattr(self, '_origin_entity_id'):
            self._origin = self._get_location_from_entity(
                self._origin_entity_id
            )

        """Update if location has changed."""

        global current
        global zone_check
        global user_display

        # Don't update anyting if no origin location
        if self._origin is None:
            return

        # If location is still same then do not update.
        if current == self._origin:
            return

        if self.hass.states.get(self._origin_entity_id) is not None:
            zone_check = self.hass.states.get(self._origin_entity_id).state
        else: 
            zone_check = 'not_home'

        # Do not update location if zone is still the same and defined (not not_home)
        if zone_check == self._zone_check_current and zone_check != 'not_home':    
            return

        self._zone_check_current = zone_check
        lat = self._origin
        current = lat
        self._reset_attributes()
        if self._api_key == 'no key':
            _LOGGER.error("Mapbox needs API Token, please get one and set in config yaml file")
            return
            #url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{longitude},{latitude}.json?limit=1&access_token=YOUR_MAPBOX_ACCESS_TOKEN"
        else:
            url = "https://api.mapbox.com/geocoding/v5/mapbox.places/" + lat + ".json?limit=1&access_token=" + self._api_key
            _LOGGER.debug("Mapbox request sent: " + url)
        try:
            response = get(url, timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to retrieve geocode from Mapbox. Error: %s", err)
            return
        
        if response.status_code > 400:
            self._state = response.reason
            _LOGGER.error("Check your api key and account settings - Mapbox Reason Code: %s", response.reason)
        
        street_number = ''
        street = 'Unnamed Road'
        alt_street = 'Unnamed Road'
        city = ''
        postal_town = ''
        state = ''
        county = ''
        country = ''
        postal_code = ''
        formatted_address = 'Unamed Location Address'
        # New Code #######################################################
        addrs_content = {}
        decoded = json.loads(response.text)
        features = decoded.get('features', [])

        for item in features[0].get('context', []):
            if '.' in item['id']:
                attribute = item['id'].split('.')[0]
                addrs_content[attribute] = item['text']

        addrs_content['street_name'] = features[0].get('text')
        addrs_content['street_number'] = features[0].get('address')
        addrs_content['full_address'] = features[0].get('place_name')
       
        if street_number == '':
            street_number = addrs_content.get('street_name')
            self._street_number = street_number
        if street == 'Unnamed Road':
            street = addrs_content.get('street_name')
            self._street = street
        if alt_street == 'Unnamed Road':
            alt_street = addrs_content.get('neighborhood','Unknown Locality')
        if city == '':
            city = addrs_content.get('place')
            self._city = city
        if postal_town == '':
            postal_town = addrs_content.get('district')
            self._postal_town = postal_town
        if state == '':
            state = addrs_content.get('region')
            self._region = state
        if county == '':
            county = addrs_content.get('locality')
            self._county = county
        if country == '':
            country = addrs_content.get('country')
            self._country = country
        if postal_code == '':
            postal_code = addrs_content.get('postcode')
            self._postal_code = postal_code
        
        formatted_address = addrs_content['full_address']

        if self._display_zone == 'hide' or zone_check == "not_home":
            if street == 'Unnamed Road':
                street = alt_street
                self._street = alt_street
            if city == '':
                city = postal_town
                if city == '':
                    city = county

            display_options = self._options
            user_display = []

            if "street_number" in display_options:
                user_display.append(street_number)
            if "street" in display_options:
                user_display.append(street)
            if "city" in display_options:
                self._append_to_user_display(city)
            if "county" in display_options:
                self._append_to_user_display(county)
            if "state" in display_options:
                self._append_to_user_display(state)
            if "postal_town" in display_options:
                self._append_to_user_display(postal_town)
            if "postal_code" in display_options:
                self._append_to_user_display(postal_code)
            if "country" in display_options:
                self._append_to_user_display(country)
            if "formatted_address" in display_options:
                self._append_to_user_display(formatted_address)

            user_display = ', '.join(  x for x in user_display )

            if user_display == '':
                user_display = street
            self._state = user_display
        else:
            self._state = zone_check[0].upper() + zone_check[1:]

    def _get_location_from_entity(self, entity_id):
        """Get the origin from the entity state or attributes."""
        entity = self._hass.states.get(entity_id)

        if entity is None:
            _LOGGER.error("Unable to find entity %s", entity_id)
            return None

        # Check if the entity has origin attributes
        if location.has_location(entity):
            return self._get_location_from_attributes(entity)

        # When everything fails just return nothing
        return None

    def _reset_attributes(self):
        """Resets attributes."""
        self._street = None
        self._street_number = None
        self._city = None
        self._postal_town = None
        self._postal_code = None
        self._region = None
        self._country = None
        self._county = None
        self._formatted_address = None

    def _append_to_user_display(self, append_check):
        """Appends attribute to state if false."""
        if append_check == "":
            pass
        else:
            user_display.append(append_check)

    @staticmethod
    def _get_location_from_attributes(entity):
        """Get the lat/long string from an entities attributes."""
        # Mapbox needs Long,Lat - in that order
        attr = entity.attributes
        return "%s,%s" % (attr.get(ATTR_LONGITUDE), attr.get(ATTR_LATITUDE))

    def _get_gravatar_for_email(self, email: str):
        """Return an 80px Gravatar for the given email address. Async friendly."""
        import hashlib
        url = 'https://www.gravatar.com/avatar/{}.jpg?s=80&d=wavatar'
        return url.format(hashlib.md5(email.encode('utf-8').lower()).hexdigest())

    def _get_image_from_url(self, url: str):
        """Return an image from a given url. Async friendly."""
        import hashlib
        return url.format(hashlib.md5(url.encode('utf-8').lower()).hexdigest())
    
