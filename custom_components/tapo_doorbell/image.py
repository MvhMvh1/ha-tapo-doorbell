"""Image entity: photo taken from the camera at the moment of each press."""

from __future__ import annotations

import logging

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_STREAM, DEFAULT_STREAM, EVENT_SNAPSHOT, SIGNAL_RING
from .entity import device_info
from .snapshot import async_snapshot

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    # Only when a camera account is set; otherwise there's nothing to grab.
    if entry.options.get(CONF_USERNAME) and entry.options.get(CONF_PASSWORD):
        async_add_entities([TapoDoorbellVisitor(hass, entry)])


class TapoDoorbellVisitor(ImageEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "visitor"
    _attr_content_type = "image/jpeg"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_visitor"
        self._attr_device_info = device_info(entry)
        self._image: bytes | None = None
        self._busy = False

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RING.format(self._entry.entry_id), self._ring
            )
        )

    @callback
    def _ring(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.hass.async_create_background_task(self._capture(), "tapo_doorbell_snapshot")

    async def _capture(self) -> None:
        try:
            opts = self._entry.options
            image = await async_snapshot(
                self.hass,
                self._entry.data[CONF_HOST],
                opts[CONF_USERNAME],
                opts[CONF_PASSWORD],
                opts.get(CONF_STREAM, DEFAULT_STREAM),
            )
            if not image:
                _LOGGER.warning("Could not get a photo from the doorbell camera")
                return
            self._image = image
            self._attr_image_last_updated = dt_util.utcnow()
            self.async_write_ha_state()
            self.hass.bus.async_fire(
                EVENT_SNAPSHOT,
                {
                    "entry_id": self._entry.entry_id,
                    "entity_id": self.entity_id,
                    "url": f"/api/image_proxy/{self.entity_id}",
                },
            )
        finally:
            self._busy = False

    async def async_image(self) -> bytes | None:
        return self._image
