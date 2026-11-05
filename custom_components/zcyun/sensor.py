"""传感器：水温、供暖温度、故障、燃烧状态

按 gy_gas 已验证模式（SensorEntityDescription）编写，兼容 HA 2026.10 的
类属性缓存坑：所有 _attr_* 一律实例内赋值。
"""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ZcyunEntity
from .const import (
    AID_FAULT,
    AID_HEAT_TEMP,
    AID_PREHEAT,
    AID_RADIATOR,
    AID_STATUS_BITS,
    AID_WATER_TEMP,
    DOMAIN,
    PREHEAT_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

FAULT_MAP = {0: "无故障", 1: "火焰故障"}
# 散热末端类型：0=散热器(暖气片) / 1=地暖。极性为推断，若实测相反改此处即可。
RADIATOR_MAP = {0: "散热器", 1: "地暖"}
# 零冷水模式：设备端不认云端写入(只读)，仅作状态展示。0/1/2 见 PREHEAT_OPTIONS。
PREHEAT_MAP = {i: v for i, v in enumerate(PREHEAT_OPTIONS)}


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ZcyunAidSensor(
                data,
                SensorEntityDescription(
                    key="water_temp",
                    name="卫浴实际水温",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    icon="mdi:thermometer-water",
                ),
                AID_WATER_TEMP,
                numeric=True,
            ),
            ZcyunAidSensor(
                data,
                SensorEntityDescription(
                    key="heat_temp",
                    name="供暖实际温度",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    icon="mdi:thermometer",
                ),
                AID_HEAT_TEMP,
                numeric=True,
            ),
            ZcyunAidSensor(
                data,
                SensorEntityDescription(
                    key="fault",
                    name="故障代码",
                    icon="mdi:alert-circle",
                ),
                AID_FAULT,
                value_map=FAULT_MAP,
            ),
            ZcyunAidSensor(
                data,
                SensorEntityDescription(
                    key="burning",
                    name="燃烧状态",
                    icon="mdi:fire",
                ),
                AID_STATUS_BITS,
                bitmask=0b10,
            ),
            ZcyunAidSensor(
                data,
                SensorEntityDescription(
                    key="radiator",
                    name="散热方式",
                    icon="mdi:home",
                ),
                AID_RADIATOR,
                value_map=RADIATOR_MAP,
                icon_map={"地暖": "mdi:home", "散热器": "mdi:radiator"},
            ),
            ZcyunAidSensor(
                data,
                SensorEntityDescription(
                    key="preheat_mode",
                    name="零冷水模式",
                    icon="mdi:water-pump",
                ),
                AID_PREHEAT,
                value_map=PREHEAT_MAP,
            ),
        ]
    )


class ZcyunAidSensor(ZcyunEntity, SensorEntity):
    """按 aid 读值的通用传感器"""

    def __init__(self, entry_data, description: SensorEntityDescription, aid,
                 numeric=False, value_map=None, bitmask=None, icon_map=None):
        super().__init__(entry_data["coordinator"], entry_data)
        self.entity_description = description
        self._aid = aid
        self._numeric = numeric
        self._value_map = value_map
        self._bitmask = bitmask
        self._icon_map = icon_map
        self._attr_unique_id = f"{self._did}_{description.key}"

    @property
    def name(self):
        return f"{self._name} {self.entity_description.name}"

    @property
    def icon(self):
        # 图标随状态切换（如散热方式：地暖=房子 / 散热器=暖气片）
        if self._icon_map is not None and self.native_value in self._icon_map:
            return self._icon_map[self.native_value]
        return self.entity_description.icon

    @property
    def native_value(self):
        # 值映射型传感器（故障代码等）设备无值时按 0 兜底（无故障）
        v = self._as(self._aid, 0 if self._value_map is not None else None)
        if v is None:
            return None
        if self._bitmask is not None:
            return "燃烧中" if int(v) & self._bitmask else "待机"
        if self._value_map is not None:
            return self._value_map.get(int(v), f"故障{int(v)}")
        return float(v) if self._numeric else v
