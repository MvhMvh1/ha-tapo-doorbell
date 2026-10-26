"""Config flow: only the doorbell's IP address is needed."""

from __future__ import annotations

import ipaddress
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_COOLDOWN,
    CONF_PULSE,
    DEFAULT_COOLDOWN,
    DEFAULT_NAME,
    DEFAULT_PULSE,
    DOMAIN,
)


class TapoDoorbellConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            try:
                ipaddress.ip_address(host)
            except ValueError:
                errors[CONF_HOST] = "invalid_ip"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={CONF_HOST: host, CONF_NAME: user_input[CONF_NAME]},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return TapoDoorbellOptionsFlow()


class TapoDoorbellOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_COOLDOWN, default=opts.get(CONF_COOLDOWN, DEFAULT_COOLDOWN)
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Required(
                    CONF_PULSE, default=opts.get(CONF_PULSE, DEFAULT_PULSE)
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
