"""Grab a single JPEG frame from the doorbell's RTSP stream."""

from __future__ import annotations

import shlex
from urllib.parse import quote

from homeassistant.components.ffmpeg import async_get_image
from homeassistant.core import HomeAssistant

from .const import RTSP_PORT


def rtsp_input(host: str, username: str, password: str, stream: str) -> str:
    """ffmpeg input arguments; TCP avoids grey/smeared frames over Wi-Fi."""
    url = (
        f"rtsp://{quote(username, safe='')}:{quote(password, safe='')}"
        f"@{host}:{RTSP_PORT}/{stream}"
    )
    return f"-rtsp_transport tcp -i {shlex.quote(url)}"


async def async_snapshot(
    hass: HomeAssistant, host: str, username: str, password: str, stream: str
) -> bytes | None:
    image = await async_get_image(hass, rtsp_input(host, username, password, stream))
    return image or None
