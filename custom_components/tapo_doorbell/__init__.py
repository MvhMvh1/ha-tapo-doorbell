"""Tapo Doorbell: local doorbell-press detection for Tapo D130 (and similar)."""

from __future__ import annotations

import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from .const import (
    CONF_COOLDOWN,
    DATA_LISTENER,
    DEFAULT_COOLDOWN,
    DOMAIN,
    EVENT_RING,
    SIGNAL_PACKET,
    SIGNAL_RING,
)
from .listener import DoorbellListener

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.EVENT, Platform.BINARY_SENSOR, Platform.IMAGE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    domain_data = hass.data.setdefault(DOMAIN, {})

    listener: DoorbellListener | None = domain_data.get(DATA_LISTENER)
    if listener is None:
        listener = DoorbellListener(hass)
        try:
            await listener.async_start()
        except OSError as err:
            raise ConfigEntryNotReady(f"Cannot open UDP port 20005: {err}") from err
        domain_data[DATA_LISTENER] = listener
    listener.users += 1

    host = entry.data[CONF_HOST]
    last_ring = 0.0

    @callback
    def _on_packet(data: bytes) -> None:
        nonlocal last_ring
        cooldown = entry.options.get(CONF_COOLDOWN, DEFAULT_COOLDOWN)
        now = time.monotonic()
        if now - last_ring < cooldown:
            return  # same press, repeated packet
        last_ring = now
        _LOGGER.debug("Doorbell %s pressed", host)
        async_dispatcher_send(hass, SIGNAL_RING.format(entry.entry_id))
        hass.bus.async_fire(
            EVENT_RING,
            {"entry_id": entry.entry_id, "host": host, "name": entry.data.get(CONF_NAME)},
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_PACKET.format(host), _on_packet)
    )
    entry.async_on_unload(entry.add_update_listener(_async_reload))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    domain_data = hass.data.get(DOMAIN, {})
    listener: DoorbellListener | None = domain_data.get(DATA_LISTENER)
    if ok and listener is not None:
        listener.users -= 1
        if listener.users <= 0:
            await listener.async_stop()
            domain_data.pop(DATA_LISTENER, None)
    return ok
