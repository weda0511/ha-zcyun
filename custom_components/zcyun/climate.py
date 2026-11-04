"""Climate：供暖"""
import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from . import ZcyunEntity
from .const import (
    AID_HEAT_SET,
    AID_HEAT_TEMP,
    AID_MODE,
    AID_POWER,
    AID_STATUS_BITS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZcyunClimate(data)])


class ZcyunClimate(ZcyunEntity, ClimateEntity):
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = ["夏季模式", "冬季模式"]
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, entry_data):
        super().__init__(entry_data["coordinator"], entry_data)
        self._attr_unique_id = f"{self._did}_climate"

    @property
    def name(self):
        return f"{self._name} 供暖"

    @property
    def current_temperature(self):
        v = self._as(AID_HEAT_TEMP)
        return float(v) if v is not None else None

    @property
    def target_temperature(self):
        v = self._as(AID_HEAT_SET)
        return float(v) if v is not None else None

    @property
    def target_temperature_step(self):
        return 1

    @property
    def min_temp(self):
        return 30

    @property
    def max_temp(self):
        return 80

    @property
    def hvac_mode(self):
        if int(self._as(AID_POWER, 0) or 0) != 1:
            return HVACMode.OFF
        return HVACMode.HEAT if int(self._as(AID_MODE, 1) or 0) == 1 else HVACMode.COOL

    @property
    def hvac_action(self):
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        bits = int(self._as(AID_STATUS_BITS, 0) or 0)
        # bit1 = 燃烧状态（据面板 DSL 推断，实测校准）
        return HVACAction.HEATING if bits & 0b10 else HVACAction.IDLE

    @property
    def preset_mode(self):
        return "冬季模式" if int(self._as(AID_MODE, 1) or 0) == 1 else "夏季模式"

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        await self.hass.async_add_executor_job(
            self.coordinator.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["client"].opt,
            self._did, AID_HEAT_SET, int(temp),
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        client = self.coordinator.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["client"]
        if hvac_mode == HVACMode.OFF:
            await self.hass.async_add_executor_job(client.opt, self._did, AID_POWER, 0)
        else:
            await self.hass.async_add_executor_job(client.opt, self._did, AID_POWER, 1)
            await self.hass.async_add_executor_job(
                client.opt, self._did, AID_MODE, 1 if hvac_mode == HVACMode.HEAT else 0
            )
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode):
        client = self.coordinator.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["client"]
        await self.hass.async_add_executor_job(
            client.opt, self._did, AID_MODE, 1 if preset_mode == "冬季模式" else 0
        )
        await self.coordinator.async_request_refresh()
