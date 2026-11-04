"""智城云（新云合）集成入口"""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ZcyunClient, ZcyunAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = ZcyunClient(
        entry.data["account"],
        entry.data["password"],
        entry.data.get("platformId", 2),
    )

    try:
        await hass.async_add_executor_job(client.auth, True)
    except ZcyunAuthError as e:
        _LOGGER.error("zcyun 鉴权失败: %s", e)
        return False

    async def async_update():
        try:
            return await hass.async_add_executor_job(client.get_status, entry.data["did"])
        except ZcyunAuthError as e:
            raise UpdateFailed(f"鉴权失败: {e}") from e
        except Exception as e:
            raise UpdateFailed(f"状态更新失败: {e}") from e

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.data['did']}",
        update_method=async_update,
        update_interval=SCAN_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "did": entry.data["did"],
        "name": entry.data.get("name") or entry.title,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry, ["climate", "water_heater", "sensor", "binary_sensor"]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["climate", "water_heater", "sensor", "binary_sensor"]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


class ZcyunEntity(CoordinatorEntity):
    """公共基类：设备信息"""

    def __init__(self, coordinator, entry_data):
        super().__init__(coordinator)
        self._did = entry_data["did"]
        self._name = entry_data["name"]

    @property
    def device_info(self):
        return {
            "identifiers": {("zcyun", self._did)},
            "name": self._name,
            "manufacturer": "博威/智城云",
            "model": "云盒壁挂炉 (vkrniw)",
        }

    @property
    def available(self):
        return self.coordinator.last_update_success and self.coordinator.data is not None

    def _as(self, aid, default=None):
        data = self.coordinator.data or {}
        return (data.get("as") or {}).get(str(aid), default)
