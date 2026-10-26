"""Binary sensor that is 'on' for a few seconds after each press."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .const import CONF_PULSE, DEFAULT_PULSE, SIGNAL_RING
from .entity import device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([TapoDoorbellPressed(entry)])


class TapoDoorbellPressed(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "pressed"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_icon = "mdi:doorbell"
    _attr_is_on = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_pressed"
        self._attr_device_info = device_info(entry)
        self._cancel_off: CALLBACK_TYPE | None = None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RING.format(self._entry.entry_id), self._ring
            )
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._cancel_off:
            self._cancel_off()

    @callback
    def _ring(self) -> None:
        if self._cancel_off:
            self._cancel_off()
        self._attr_is_on = True
        self.async_write_ha_state()
        pulse = self._entry.options.get(CONF_PULSE, DEFAULT_PULSE)
        self._cancel_off = async_call_later(self.hass, pulse, self._off)

    @callback
    def _off(self, _now) -> None:
        self._cancel_off = None
        self._attr_is_on = False
        self.async_write_ha_state()
