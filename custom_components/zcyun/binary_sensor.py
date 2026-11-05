"""二进制传感器：锅炉子系统实时状态（图标的亮/灭）

两类来源：
  1) aid 107 状态位图位：水流(bit0)/风机(bit2)/水泵(bit3)/温控器(bit4)
     —— 与 App 那排图标一致，亮=该部件正在工作。
  2) 单一 aid 开关量：
     - 夏季模式  (aid 102，反向：冬季=1故灭，夏季=0故亮)  → 对应 App 雪花图标
     - 定时功能  (aid 108)                                   → 对应 App 时钟图标
     - 零冷水    (aid 29，值≠0=有预热模式)                   → 对应 App 循环/水滴图标
     - 故障报警  (aid 17，值≠0=有故障)                       → 对应 App 叹号图标

燃烧状态 (aid 107 bit1) 已在 sensor.py 中以文本传感器呈现，此处不再重复。
"""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ZcyunEntity
from .const import (
    AID_STATUS_BITS,
    AID_MODE,
    AID_TIMER_ON,
    AID_PREHEAT,
    AID_FAULT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# (key, 中文名, 图标, 位图位[None表示非位图], 单aid[None表示位图], 反向)
# 反向=True：aid 值为 0 时亮（如夏季模式：冬季=1故灭，夏季=0故亮）
STATUS_DEFS = [
    ("water_flow",  "水流信号", "mdi:waves",      0,    None,        False),
    ("fan",         "风机状态", "mdi:fan",        2,    None,        False),
    ("pump",        "水泵",     "mdi:pump",       3,    None,        False),
    ("thermostat",  "温控器",   "mdi:thermostat", 4,    None,        False),
    ("summer_mode", "夏季模式", "mdi:snowflake",  None, AID_MODE,     True),
    ("timer",       "定时功能", "mdi:clock",      None, AID_TIMER_ON, False),
    ("preheat",     "零冷水",   "mdi:repeat",     None, AID_PREHEAT,  False),
    ("fault",       "故障报警", "mdi:alert",      None, AID_FAULT,    False),
]


async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ZcyunStatusBinary(data, key, name, bit, aid, icon, invert)
        for (key, name, icon, bit, aid, invert) in STATUS_DEFS
    )


class ZcyunStatusBinary(ZcyunEntity, BinarySensorEntity):
    """读 aid 107 某一位，或读单一 aid 的开关量，开/关表示该状态是否激活。"""

    def __init__(self, entry_data, key, name, bit, aid, icon, invert):
        super().__init__(entry_data["coordinator"], entry_data)
        self._key = key
        self._status_name = name
        self._bit = bit
        self._aid = aid
        self._icon = icon
        self._invert = invert
        self._attr_unique_id = f"{self._did}_{key}"

    @property
    def name(self):
        return f"{self._name} {self._status_name}"

    @property
    def is_on(self):
        if self._bit is not None:
            bits = int(self._as(AID_STATUS_BITS, 0) or 0)
            return bool(bits & (1 << self._bit))
        raw = self._as(self._aid, 0)
        try:
            on = bool(int(raw))
        except (TypeError, ValueError):
            on = bool(raw)
        return (not on) if self._invert else on

    @property
    def icon(self):
        return self._icon
