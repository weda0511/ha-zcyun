"""二进制传感器：锅炉子系统实时状态（来自 aid 107 状态位图）

位定义（按设备点位命名顺序；bit1=燃烧 已由本集成实测确认）：
  bit0 水流信号 / bit1 燃烧状态 / bit2 风机状态 / bit3 水泵 / bit4 温控器

各图标亮 = 对应子系统此刻正在工作，灭 = 未工作。
（燃烧状态 bit1 已在 sensor.py 中以文本传感器呈现；此处补齐其余 4 位。）
"""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ZcyunEntity
from .const import AID_STATUS_BITS, DOMAIN

_LOGGER = logging.getLogger(__name__)

# (key, 中文名称, 位索引, 图标)
# 位索引按设备点位命名顺序（水流/燃烧/风机/水泵/温控器 = bit0..bit4）；
# 若实测某图标点亮与预期不符，仅改此处位索引即可。
STATUS_DEFS = [
    ("water_flow", "水流信号", 0, "mdi:waves"),
    ("fan",        "风机状态", 2, "mdi:fan"),
    ("pump",       "水泵",     3, "mdi:pump"),
    ("thermostat", "温控器",   4, "mdi:thermostat"),
]


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ZcyunStatusBinary(data, key, name, bit, icon)
        for (key, name, bit, icon) in STATUS_DEFS
    )


class ZcyunStatusBinary(ZcyunEntity, BinarySensorEntity):
    """读 aid 107 某一位：开/关表示该子系统是否在工作。"""

    def __init__(self, entry_data, key, name, bit, icon):
        super().__init__(entry_data["coordinator"], entry_data)
        self._key = key
        self._status_name = name
        self._bit = bit
        self._icon = icon
        self._attr_unique_id = f"{self._did}_{key}"

    @property
    def name(self):
        return f"{self._name} {self._status_name}"

    @property
    def is_on(self):
        bits = int(self._as(AID_STATUS_BITS, 0) or 0)
        return bool(bits & (1 << self._bit))

    @property
    def icon(self):
        return self._icon
