# 云盒壁挂炉探针（诊断/调试工具）

命令行工具，直接调用智城云 OpenAPI，用于登录保活、状态查询、控制下发验证。
**不含任何硬编码凭证**，首次运行读取同目录 `zcyun_config.json`（参考 `zcyun_config.example.json`）。

## 用法

```bash
python zcyun_probe.py auth          # 鉴权（写入/续期 openKey）
python zcyun_probe.py status        # 人类可读状态翻译
python zcyun_probe.py raw           # 原始数据点 JSON
python zcyun_probe.py set <aid> <value>   # 控制下发，如 set 106 43 设供暖目标43℃
python zcyun_probe.py keepalive      # 循环保活（openKey 到期前自动续）
```

## 说明

- 签名算法见 `custom_components/zcyun/api.py` 头部注释（来自智城云官方 OpenAPI 文档）。
- `openKey` 72 小时有效，`auth` 会写入 `zcyun_config.json` 并在到期前 24h 自动续期。
- 该工具仅用于调试；日常使用请走 HA 集成。
