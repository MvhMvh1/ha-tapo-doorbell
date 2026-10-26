"""Shared device info."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DEFAULT_NAME, DOMAIN


def device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_NAME, DEFAULT_NAME),
        manufacturer="TP-Link",
        model="Tapo D130",
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )
