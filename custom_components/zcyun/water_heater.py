"""WaterHeater：卫浴热水"""
import logging

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_OFF, STATE_ON, UnitOfTemperature

from . import ZcyunEntity
from .const import AID_POWER, AID_WATER_SET, AID_WATER_TEMP, DOMAIN

_LOGGER = logging.getLogger(__name__)

STATE_HEAT_PUMP = "heat_pump"


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZcyunWaterHeater(data)])


class ZcyunWaterHeater(ZcyunEntity, WaterHeaterEntity):
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = [STATE_OFF, STATE_ON]
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )

    def __init__(self, entry_data):
        super().__init__(entry_data["coordinator"], entry_data)
        self._attr_unique_id = f"{self._did}_water_heater"

    @property
    def name(self):
        return f"{self._name} 卫浴热水"

    @property
    def current_temperature(self):
        v = self._as(AID_WATER_TEMP)
        return float(v) if v is not None else None

    @property
    def target_temperature(self):
        v = self._as(AID_WATER_SET)
        return float(v) if v is not None else None

    @property
    def min_temp(self):
        return 30

    @property
    def max_temp(self):
        return 60

    @property
    def current_operation(self):
        return STATE_ON if int(self._as(AID_POWER, 0) or 0) == 1 else STATE_OFF

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        client = self.coordinator.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["client"]
        await self.hass.async_add_executor_job(client.opt, self._did, AID_WATER_SET, int(temp))
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode):
        client = self.coordinator.hass.data[DOMAIN][self.coordinator.config_entry.entry_id]["client"]
        await self.hass.async_add_executor_job(
            client.opt, self._did, AID_POWER, 1 if operation_mode == STATE_ON else 0
        )
        await self.coordinator.async_request_refresh()
