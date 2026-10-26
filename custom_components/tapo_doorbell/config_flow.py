"""Config flow: find the doorbell by pressing it, or enter the IP by hand."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_COOLDOWN,
    CONF_PULSE,
    CONF_STREAM,
    DEFAULT_COOLDOWN,
    DEFAULT_NAME,
    DEFAULT_PULSE,
    DEFAULT_STREAM,
    DISCOVERY_TIMEOUT,
    DOMAIN,
    STREAMS,
)
from .listener import async_wait_for_doorbell
from .snapshot import async_snapshot

_LOGGER = logging.getLogger(__name__)

PASSWORD = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
STREAM = SelectSelector(SelectSelectorConfig(options=STREAMS, translation_key="stream"))


async def _validate_camera(hass, host: str, data: dict[str, Any]) -> str | None:
    """Return an error key, or None if credentials are empty or work."""
    user = data.get(CONF_USERNAME, "").strip()
    pwd = data.get(CONF_PASSWORD, "")
    if not user and not pwd:
        return None
    if not user or not pwd:
        return "incomplete_credentials"
    image = await async_snapshot(
        hass, host, user, pwd, data.get(CONF_STREAM, DEFAULT_STREAM)
    )
    return None if image else "cannot_snapshot"


def _camera_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(
                CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")
            ): str,
            vol.Optional(
                CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")
            ): PASSWORD,
            vol.Required(
                CONF_STREAM, default=defaults.get(CONF_STREAM, DEFAULT_STREAM)
            ): STREAM,
        }
    )


class TapoDoorbellConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._name: str = DEFAULT_NAME
        self._discover_task: asyncio.Task[str] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(step_id="user", menu_options=["discover", "manual"])

    # --- Find by pressing the doorbell -------------------------------------

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._discover_task is None:
            known = {e.data[CONF_HOST] for e in self._async_current_entries()}
            self._discover_task = self.hass.async_create_task(
                async_wait_for_doorbell(known, DISCOVERY_TIMEOUT)
            )
        if not self._discover_task.done():
            return self.async_show_progress(
                step_id="discover",
                progress_action="wait_press",
                progress_task=self._discover_task,
                description_placeholders={"timeout": str(DISCOVERY_TIMEOUT)},
            )
        try:
            self._host = self._discover_task.result()
        except TimeoutError:
            self._discover_task = None
            return self.async_show_progress_done(next_step_id="not_found")
        except OSError as err:
            _LOGGER.error("Could not listen on UDP 20005: %s", err)
            self._discover_task = None
            return self.async_show_progress_done(next_step_id="not_found")
        self._discover_task = None
        return self.async_show_progress_done(next_step_id="found")

    async def async_step_not_found(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="not_found", menu_options=["discover", "manual"]
        )

    async def async_step_found(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._name = user_input[CONF_NAME]
            return await self.async_step_camera()
        await self.async_set_unique_id(self._host)
        self._abort_if_unique_id_configured()
        return self.async_show_form(
            step_id="found",
            data_schema=vol.Schema({vol.Required(CONF_NAME, default=DEFAULT_NAME): str}),
            description_placeholders={"host": self._host},
        )

    # --- Enter the IP by hand ----------------------------------------------

    async def async_step_manual(
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
                self._host = host
                self._name = user_input[CONF_NAME]
                return await self.async_step_camera()

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )
        return self.async_show_form(step_id="manual", data_schema=schema, errors=errors)

    # --- Optional camera account for photos --------------------------------

    async def async_step_camera(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if err := await _validate_camera(self.hass, self._host, user_input):
                errors["base"] = err
            else:
                return self.async_create_entry(
                    title=self._name,
                    data={CONF_HOST: self._host, CONF_NAME: self._name},
                    options={
                        CONF_USERNAME: user_input.get(CONF_USERNAME, "").strip(),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
                        CONF_STREAM: user_input.get(CONF_STREAM, DEFAULT_STREAM),
                        CONF_COOLDOWN: DEFAULT_COOLDOWN,
                        CONF_PULSE: DEFAULT_PULSE,
                    },
                )
        return self.async_show_form(
            step_id="camera",
            data_schema=_camera_schema(user_input or {}),
            errors=errors,
            description_placeholders={"host": self._host},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return TapoDoorbellOptionsFlow()


class TapoDoorbellOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        opts = dict(self.config_entry.options)
        if user_input is not None:
            host = self.config_entry.data[CONF_HOST]
            if err := await _validate_camera(self.hass, host, user_input):
                errors["base"] = err
            else:
                user_input[CONF_USERNAME] = user_input.get(CONF_USERNAME, "").strip()
                return self.async_create_entry(data=user_input)
            opts.update(user_input)

        schema = _camera_schema(opts).extend(
            {
                vol.Required(
                    CONF_COOLDOWN, default=opts.get(CONF_COOLDOWN, DEFAULT_COOLDOWN)
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Required(
                    CONF_PULSE, default=opts.get(CONF_PULSE, DEFAULT_PULSE)
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
