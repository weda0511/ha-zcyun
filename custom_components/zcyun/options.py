"""选项流：改密码/平台ID"""
from homeassistant import config_entries

from .const import CONF_ACCOUNT, CONF_PASSWORD, CONF_PLATFORM_ID, DEFAULT_PLATFORM_ID
import voluptuous as vol


class ZcyunOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            data = dict(self._entry.data)
            data[CONF_PASSWORD] = user_input[CONF_PASSWORD]
            data[CONF_PLATFORM_ID] = user_input.get(CONF_PLATFORM_ID, DEFAULT_PLATFORM_ID)
            self.hass.config_entries.async_update_entry(self._entry, data=data)
            return self.async_create_entry(title="", data={})
        schema = vol.Schema(
            {
                vol.Required(CONF_ACCOUNT, default=self._entry.data[CONF_ACCOUNT]): str,
                vol.Required(CONF_PASSWORD, default=self._entry.data[CONF_PASSWORD]): str,
                vol.Optional(
                    CONF_PLATFORM_ID,
                    default=self._entry.data.get(CONF_PLATFORM_ID, DEFAULT_PLATFORM_ID),
                ): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
