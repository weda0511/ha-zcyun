# 智城云（新云合）博威云盒壁挂炉 — Home Assistant 集成

把「新云合」App（智城云平台 `papi.zcyun.cn`，前身 Machtalk）接入 Home Assistant，
支持博威云盒壁挂炉（型号 vkrniw / KDX）的供暖、卫浴热水监控与控制。

> 个人兴趣作品，与智城云（中科智城）及博威无任何关联，仅自用。

---

## 功能与实体

| 实体 | 类型 | 说明 |
|---|---|---|
| 供暖 | `climate` | 开关机（aid 101）、冬季/夏季模式（aid 102）、目标温度 30-80℃（aid 106）、当前供暖温度（aid 104）、燃烧状态 |
| 卫浴热水 | `water_heater` | 开关、目标温度 30-60℃（aid 105）、当前卫浴水温（aid 103） |
| 卫浴实际水温 | `sensor` | ℃，`state_class=measurement`（可长期统计） |
| 供暖实际温度 | `sensor` | ℃，`state_class=measurement`（可长期统计） |
| 故障代码 | `sensor` | 0=无故障 |
| 燃烧状态 | `sensor` | 燃烧中 / 待机（aid 107 bit1） |
| 水流信号 | `binary_sensor` | 供暖回路有水流动（aid 107 bit0，亮=有水流） |
| 风机状态 | `binary_sensor` | 燃烧风机运转（aid 107 bit2） |
| 水泵 | `binary_sensor` | 循环水泵运转（aid 107 bit3） |
| 温控器 | `binary_sensor` | 房间温控器在请求加热（aid 107 bit4） |
| 散热方式 | `sensor` | 散热器 / 地暖（aid 116，只读） |
| 零冷水模式 | `sensor` | 无预热 / 单次预热 / 全开候预热（aid 29，设备端不认云端写入，**只读展示**） |

**关于零冷水**：设备属性表标称 aid 29 可写，实测云端写入回 `code:0` 但设备真值不变，
故做成只读显示，避免「点了没反应」的假控制。如需真控制请在原厂 App 操作。

---

## 安装

### HACS
1. HACS → 集成 → 右上角 ⋮ → 自定义仓库 → 填入 `https://github.com/weda0511/ha-zcyun` → 类别选「集成」
2. 搜索「智城云」安装，重启 HA
### 手动
复制 `custom_components/zcyun/` 到 `config/custom_components/zcyun/`，重启 HA

## 配置
设置 → 设备与服务 → 添加集成 → 搜索「智城云」→ 填新云合 App 的**账号（手机号）**、**密码**，平台 ID 默认 `2`。
登录后自动定时拉取状态（60s），`openKey` 72h 有效、到期前 24h 自动续期。

---

## 温度曲线与能源看板（重要）

**温度 ≠ 能源，请勿把温度塞进 HA 能源看板。**
- 能源看板只认 `device_class: energy/gas/water` + `state_class: total_increasing` 的消耗类实体；
  壁挂炉温度是热舒适度指标，塞进去 HA 不会画、语义也错。
- 壁挂炉**本身不上报用气量**（aid 32/33/34 为只读且 `store=0`，历史查询为空），无设备级能耗数据。
- **真正该进能源看板的是燃气消耗**：贵阳燃气表（`gy_gas` 集成）的 `燃气表读数 / 当期用气量`
  已是 `device_class=gas, state_class=total_increasing, m³`，在 设置→能源→燃气 选它即可。
- **采暖温度上升曲线**走单独的看板：见 `examples/heating-monitor.yaml`（YAML 模式看板），
  含 24h 实时升温曲线、按日长期统计、近 7 天采暖会话，并叠加燃烧动作；
  顶部另含「锅炉实时运行状态」图标卡（glance），用 `mdi:fire / waves / fan / pump / thermostat` 图标
  把 aid 107 的 5 个状态位（火焰/水流/风机/水泵/温控器）以**图标+文字**实时展示——
  冬季烧地暖点火时全部亮起，到温停火后一起熄灭。
  HA 仅在温度**变化**时落库，恒温待机只有 1 个基点，采暖升温时每个变化都会记录，曲线自然出现。

---

## 调试工具
`tools/probe/` 提供命令行探针（登录保活 / 状态 / 控制验证），详见其 README。

## 技术要点
- 鉴权：`POST /v1/auth`，`sign = MD5(md5(password) + ts)`，返回 openKey
- 接口签名：`sign = SHA1(方法大写 + URI路径(不含query) + requestBody + ts + openKey)`（官方 OpenAPI 文档）
- 状态：`GET /v1/device/status/{did}`；控制：`POST /v1/device/opt/{did}` `{"as":{"106":43}}`
- 属性定义：`GET /v1/device/desc/{did}`（49 个数据点）
- HA 2026.10 适配：`async_forward_entry_setups`、传感器用 `SensorEntityDescription` 规避类属性缓存坑
