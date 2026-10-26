"""Event entity: one event per doorbell press."""

from __future__ import annotations

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SIGNAL_RING
from .entity import device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([TapoDoorbellEvent(entry)])


class TapoDoorbellEvent(EventEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "doorbell"
    _attr_device_class = EventDeviceClass.DOORBELL
    _attr_event_types = ["ring"]

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ring_event"
        self._attr_device_info = device_info(entry)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RING.format(self._entry.entry_id), self._ring
            )
        )

    @callback
    def _ring(self) -> None:
        self._trigger_event("ring")
        self.async_write_ha_state()
