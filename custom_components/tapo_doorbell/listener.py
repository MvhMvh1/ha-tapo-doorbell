"""Shared UDP listener for Tapo doorbell press broadcasts (port 20005)."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import SIGNAL_PACKET, UDP_PORT

_LOGGER = logging.getLogger(__name__)


class _Protocol(asyncio.DatagramProtocol):
    def __init__(self, listener: "DoorbellListener") -> None:
        self._listener = listener

    def datagram_received(self, data: bytes, addr) -> None:
        self._listener.packet_received(data, addr[0])

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("UDP error: %s", exc)


class DoorbellListener:
    """One socket for all doorbells; packets are routed by sender IP."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._transport: asyncio.DatagramTransport | None = None
        self.users = 0

    async def async_start(self) -> None:
        if self._transport is not None:
            return
        loop = asyncio.get_running_loop()
        # reuse_port so this can run next to Tapo: Cameras Control,
        # which listens on the same port. Broadcasts reach both sockets.
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: _Protocol(self),
            local_addr=("0.0.0.0", UDP_PORT),
            allow_broadcast=True,
            reuse_port=True,
        )
        _LOGGER.info("Listening for Tapo doorbell presses on UDP %s", UDP_PORT)

    @callback
    def packet_received(self, data: bytes, ip: str) -> None:
        _LOGGER.debug("Packet from %s (%d bytes): %s", ip, len(data), data[:64].hex())
        # Datagram callbacks already run in HA's event loop.
        async_dispatcher_send(self.hass, SIGNAL_PACKET.format(ip), data)

    async def async_stop(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None


class _DiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self, future: asyncio.Future, exclude: set[str]) -> None:
        self._future = future
        self._exclude = exclude

    def datagram_received(self, data: bytes, addr) -> None:
        ip = addr[0]
        if ip not in self._exclude and not self._future.done():
            self._future.set_result(ip)


async def async_wait_for_doorbell(exclude: set[str], timeout: float) -> str:
    """Return the IP of the first doorbell that broadcasts a press.

    Uses its own socket (reuse_port), so it works whether or not the
    integration is already running for another doorbell.
    Raises TimeoutError if nothing arrives in time.
    """
    loop = asyncio.get_running_loop()
    future: asyncio.Future[str] = loop.create_future()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _DiscoveryProtocol(future, exclude),
        local_addr=("0.0.0.0", UDP_PORT),
        allow_broadcast=True,
        reuse_port=True,
    )
    try:
        async with asyncio.timeout(timeout):
            return await future
    finally:
        transport.close()
