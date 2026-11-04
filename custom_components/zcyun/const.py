"""智城云（新云合）常量"""
DOMAIN = "zcyun"

CONF_ACCOUNT = "account"
CONF_PASSWORD = "password"
CONF_PLATFORM_ID = "platformId"

DEFAULT_PLATFORM_ID = 2
BASE_URL = "https://papi.zcyun.cn"

# 数据点 aid 表（博威壁挂炉 / vkrniw）
AID_POWER = 101          # 开关键 0/1
AID_MODE = 102           # 模式 0夏季/1冬季
AID_WATER_TEMP = 103     # 卫浴实际水温 ℃
AID_HEAT_TEMP = 104      # 供暖实际温度 ℃
AID_WATER_SET = 105      # 设置卫浴水温 30-60
AID_HEAT_SET = 106       # 设置供暖温度 30-80
AID_STATUS_BITS = 107    # 水流/燃烧/风机/水泵/温控器位图
AID_TIMER_ON = 108       # 定时开关
AID_FAULT = 17           # 故障代码 0无
AID_RADIATOR = 116       # 散热器/地暖 0/1
AID_PREHEAT = 29         # 零冷水模式 0无预热/1单次预热/2全开候预热

# 零冷水模式选项（aid 29）
PREHEAT_OPTIONS = ["无预热", "单次预热", "全开候预热"]

OPENKEY_REFRESH_MS = 24 * 3600 * 1000  # 到期前24h续期
