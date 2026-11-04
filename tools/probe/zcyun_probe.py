#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智城云（新云合）博威壁挂炉 probe CLI

用法:
  python zcyun_probe.py auth          # 登录拿 openKey（自动写入缓存）
  python zcyun_probe.py devices       # 设备列表
  python zcyun_probe.py status        # 实时状态（翻译属性名）
  python zcyun_probe.py raw           # 实时状态（原始 JSON）
  python zcyun_probe.py set 106 45   # 控制下发 aid=106(设置供暖温度) 值=45
  python zcyun_probe.py keepalive    # 保活：刷新 openKey（提前 24h 续）
"""
import json
import hashlib
import sys
import time
import os
import urllib.request
import urllib.error

BASE = "https://papi.zcyun.cn"
HERE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(HERE, "zcyun_config.json")


def load_cfg():
    with open(CFG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_cfg(cfg):
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def auth(cfg, force=False):
    """登录鉴权，返回 openKey；72h 内且非强制则复用缓存"""
    exp = cfg.get("openKeyExpiredAt", 0)
    now = int(time.time() * 1000)
    if not force and cfg.get("openKey") and exp - now > 24 * 3600 * 1000:
        return cfg["openKey"]
    pwd_md5 = hashlib.md5(cfg["password"].encode()).hexdigest()
    ts = now
    sign = hashlib.md5((pwd_md5 + str(ts)).encode()).hexdigest()
    body = json.dumps({"account": cfg["account"], "ts": ts, "sign": sign,
                       "platformId": cfg["platformId"]})
    req = urllib.request.Request(
        BASE + "/v1/auth", data=body.encode(),
        headers={"Content-Type": "application/json;charset=utf-8",
                 "User-Agent": "MachtalkDemo/0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read().decode())
    if resp.get("code") != 0:
        raise RuntimeError("auth failed: %s" % resp)
    cfg["openId"] = resp["openId"]
    cfg["openKey"] = resp["openKey"]
    cfg["openKeyExpiredAt"] = resp["expiredAt"]
    save_cfg(cfg)
    print("[auth] openKey 已更新，有效期至 %s" % time.strftime(
        "%Y-%m-%d %H:%M", time.localtime(resp["expiredAt"] / 1000)))
    return resp["openKey"]


def call(cfg, method, uri, body_str=""):
    """带签名调用。uri 为路径（不含 query string，签名不含 query）"""
    ts = int(time.time() * 1000)
    sign = hashlib.sha1((method + uri + body_str + str(ts) + cfg["openKey"]).encode()).hexdigest()
    headers = {"openId": cfg["openId"], "ts": str(ts), "sign": sign,
               "Content-Type": "application/json;charset=utf-8",
               "User-Agent": "MachtalkDemo/0"}
    req = urllib.request.Request(BASE + uri,
                                 data=(body_str.encode() if body_str else None),
                                 headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode()
    except urllib.error.HTTPError as e:
        return e.read().decode()


def first_did(cfg):
    resp = json.loads(call(cfg, "GET", "/v1/user/devices"))
    devs = resp["data"]["devs"]
    return devs[0]["did"], devs[0]["name"]


def cmd_status(translate=True):
    cfg = load_cfg()
    auth(cfg)
    did, name = first_did(cfg)
    st = json.loads(call(cfg, "GET", "/v1/device/status/%s" % did))
    if not translate:
        print(json.dumps(st, ensure_ascii=False, indent=1))
        return
    if st.get("code") != 0:
        print("错误:", st)
        return
    desc_path = os.path.join(HERE, "device_desc.json")
    if os.path.exists(desc_path):
        with open(desc_path, encoding="utf-8") as f:
            desc = json.load(f)
        attrs = {a["aid"]: a for a in desc["data"]["attrs"]}
    else:
        attrs = {}
    print("设备: %s (did=%s)" % (name, did))
    for k, v in sorted(st["data"]["as"].items(), key=lambda x: int(x[0])):
        a = attrs.get(int(k))
        label = a["name"] if a else "[未知]"
        sym = a.get("symbol", "") if a else ""
        extra = ""
        if a and a.get("vs") and str(int(v) if isinstance(v, float) else v) in a["vs"]:
            vv = int(v) if isinstance(v, float) else v
            extra = " (%s)" % a["vs"].get(str(vv), a["vs"].get(vv, ""))
        elif a and a.get("type") == 5 and a.get("vs"):
            extra = " (%s)" % a["vs"].get(str(v), "?")
        print("  %-14s aid=%-6s = %-10s %s%s" % (label, k, v, sym, extra))
    fids = st["data"].get("fids", [])
    print("故障 fids:", fids if fids else "无")


def cmd_set(aid, value):
    cfg = load_cfg()
    auth(cfg)
    did, name = first_did(cfg)
    body = json.dumps({"as": {str(aid): int(value)}})
    print("下发: %s  aid=%s -> %s" % (name, aid, value))
    resp = call(cfg, "POST", "/v1/device/opt/%s" % did, body)
    print("平台回执:", resp)
    if json.loads(resp).get("code") == 0:
        time.sleep(3)
        print("\n3秒后回读状态:")
        cmd_status()


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cfg = load_cfg()
    if args[0] == "auth":
        auth(cfg, force=True)
    elif args[0] == "devices":
        auth(cfg)
        print(call(cfg, "GET", "/v1/user/devices"))
    elif args[0] == "status":
        cmd_status()
    elif args[0] == "raw":
        cmd_status(translate=False)
    elif args[0] == "set":
        if len(args) < 3:
            print("用法: set <aid> <value>")
            return
        cmd_set(int(args[1]), int(args[2]))
    elif args[0] == "keepalive":
        auth(cfg)  # 不足24h余期时静默跳过
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
