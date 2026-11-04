"""配置流"""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .api import ZcyunClient, ZcyunAuthError
from .const import CONF_ACCOUNT, CONF_PASSWORD, CONF_PLATFORM_ID, DEFAULT_PLATFORM_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ZcyunFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            client = ZcyunClient(
                user_input[CONF_ACCOUNT],
                user_input[CONF_PASSWORD],
                user_input.get(CONF_PLATFORM_ID, DEFAULT_PLATFORM_ID),
            )
            try:
                await self.hass.async_add_executor_job(client.auth, True)
                devs = await self.hass.async_add_executor_job(client.list_devices)
            except ZcyunAuthError:
                errors["base"] = "auth_failed"
            except Exception as e:
                _LOGGER.exception("zcyun 连接失败")
                errors["base"] = "cannot_connect"
            else:
                if not devs:
                    errors["base"] = "no_devices"
                else:
                    dev = devs[0]
                    return self.async_create_entry(
                        title=dev.get("name", "智城云设备"),
                        data={
                            **user_input,
                            "did": dev["did"],
                            "name": dev.get("name", dev["did"]),
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCOUNT): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_PLATFORM_ID, default=DEFAULT_PLATFORM_ID): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        from .options import ZcyunOptionsFlow

        return ZcyunOptionsFlow(config_entry)
