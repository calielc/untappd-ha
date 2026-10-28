"""Config flow for Untappd."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TimeSelector

from .const import (
    CONF_COOKIE,
    CONF_HAPPY_END,
    CONF_HAPPY_INTERVAL,
    CONF_HAPPY_START,
    CONF_SCAN_INTERVAL,
    CONF_USER_AGENT,
    CONF_USERNAME,
    DEFAULT_HAPPY_END,
    DEFAULT_HAPPY_INTERVAL,
    DEFAULT_HAPPY_START,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)
from .coordinator import async_fetch_beer_page, async_fetch_profile

_MULTILINE = TextSelector(TextSelectorConfig(multiline=True))


def _clean_cookie(value: str | None) -> str | None:
    """Accept 'Cookie: a=b; c=d' as copied from DevTools as well as the bare value."""
    if not value:
        return None
    value = " ".join(value.split())
    if value.lower().startswith("cookie:"):
        value = value[len("cookie:") :].strip()
    return value or None


async def _validate(hass, username: str, cookie: str | None, user_agent: str | None) -> str | None:
    """Return an error key, or None when the input works."""
    try:
        await async_fetch_profile(hass, username)
        if cookie:
            await async_fetch_beer_page(hass, username, cookie, user_agent)
    except ConfigEntryAuthFailed:
        return "invalid_auth"
    except ValueError as err:
        if str(err) == "user_not_found":
            return "user_not_found"
        return "beer_history_unreadable" if cookie and "beer_history" in str(err) else "profile_unreadable"
    except (ClientError, TimeoutError):
        return "cannot_connect"
    return None


class UntappdConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        user_input = user_input or {}
        if CONF_USERNAME in user_input:
            username = user_input[CONF_USERNAME].strip().lstrip("@")
            cookie = _clean_cookie(user_input.get(CONF_COOKIE))
            user_agent = (user_input.get(CONF_USER_AGENT) or "").strip() or None
            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_configured()
            if error := await _validate(self.hass, username, cookie, user_agent):
                errors["base"] = error
            else:
                data = {CONF_USERNAME: username}
                if cookie:
                    data[CONF_COOKIE] = cookie
                if user_agent:
                    data[CONF_USER_AGENT] = user_agent
                return self.async_create_entry(title=f"Untappd ({username})", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME, vol.UNDEFINED)): str,
                    vol.Optional(CONF_COOKIE): _MULTILINE,
                    vol.Optional(CONF_USER_AGENT): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            cookie = _clean_cookie(user_input.get(CONF_COOKIE))
            user_agent = (user_input.get(CONF_USER_AGENT) or "").strip() or entry.data.get(CONF_USER_AGENT)
            if not cookie:
                errors["base"] = "invalid_auth"
            elif error := await _validate(self.hass, entry.data[CONF_USERNAME], cookie, user_agent):
                errors["base"] = error
            else:
                updates = {CONF_COOKIE: cookie}
                if user_agent:
                    updates[CONF_USER_AGENT] = user_agent
                return self.async_update_reload_and_abort(entry, data_updates=updates)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_COOKIE): _MULTILINE, vol.Optional(CONF_USER_AGENT): str}),
            description_placeholders={"username": entry.data[CONF_USERNAME]},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return UntappdOptionsFlow()


class UntappdOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        o = self.config_entry.options
        minutes = vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=1440))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=o.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): minutes,
                    vol.Required(
                        CONF_HAPPY_INTERVAL, default=o.get(CONF_HAPPY_INTERVAL, DEFAULT_HAPPY_INTERVAL)
                    ): minutes,
                    vol.Required(
                        CONF_HAPPY_START, default=o.get(CONF_HAPPY_START, DEFAULT_HAPPY_START)
                    ): TimeSelector(),
                    vol.Required(CONF_HAPPY_END, default=o.get(CONF_HAPPY_END, DEFAULT_HAPPY_END)): TimeSelector(),
                }
            ),
        )
