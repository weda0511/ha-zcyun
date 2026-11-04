"""智城云 API 客户端

签名规则（官方 OpenAPI 个人版文档）：
- 接口签名: sign = SHA1(方法大写 + URI路径(不含query) + requestBody + ts + openKey)
- 鉴权:     POST /v1/auth  sign = MD5(md5(password) + ts)
"""
import hashlib
import json
import time
import logging

import urllib.request
import urllib.error

from .const import BASE_URL, OPENKEY_REFRESH_MS

_LOGGER = logging.getLogger(__name__)

UA = "MachtalkDemo/0"


class ZcyunClient:
    def __init__(self, account, password, platform_id, app_id=5):
        self.account = account
        self.password = password
        self.platform_id = platform_id
        self.app_id = app_id
        self.open_id = None
        self.open_key = None
        self.open_key_expired_at = 0

    # ---------- 鉴权 ----------
    def auth(self, force=False):
        now = int(time.time() * 1000)
        if (
            not force
            and self.open_key
            and self.open_key_expired_at - now > OPENKEY_REFRESH_MS
        ):
            return
        pwd_md5 = hashlib.md5(self.password.encode()).hexdigest()
        ts = now
        sign = hashlib.md5((pwd_md5 + str(ts)).encode()).hexdigest()
        body = json.dumps(
            {"account": self.account, "ts": ts, "sign": sign, "platformId": self.platform_id}
        )
        resp = self._request("POST", "/v1/auth", body, signed=False)
        if resp.get("code") != 0:
            raise ZcyunAuthError(resp.get("msg", "auth failed"))
        self.open_id = resp["openId"]
        self.open_key = resp["openKey"]
        self.open_key_expired_at = resp["expiredAt"]
        _LOGGER.debug("zcyun auth ok, openKey expires at %s", resp["expiredAt"])

    # ---------- 请求 ----------
    def _request(self, method, uri, body_str="", signed=True, retry_auth=True):
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "User-Agent": UA,
        }
        if signed:
            # 签名只含路径，不含 query string
            path = uri.split("?")[0]
            ts = int(time.time() * 1000)
            sign = hashlib.sha1(
                (method + path + body_str + str(ts) + self.open_key).encode()
            ).hexdigest()
            headers.update({"openId": self.open_id, "ts": str(ts), "sign": sign})
        req = urllib.request.Request(
            BASE_URL + uri,
            data=(body_str.encode() if body_str else None),
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode())
            except Exception:
                raise

    def call(self, method, uri, body_str=""):
        resp = self._request(method, uri, body_str)
        if resp.get("code") in (20015, 20017):  # 会话过期 -> 重鉴权一次
            self.auth(force=True)
            resp = self._request(method, uri, body_str)
        if resp.get("code") != 0:
            _LOGGER.warning("zcyun api %s %s -> %s", method, uri, resp)
        return resp

    # ---------- 业务 ----------
    def list_devices(self):
        return self.call("GET", "/v1/user/devices?appId=%d" % self.app_id)["data"]["devs"]

    def get_status(self, did):
        resp = self.call("GET", "/v1/device/status/%s" % did)
        if resp.get("code") != 0:
            return None
        return resp["data"]

    def get_desc(self, did):
        resp = self.call("GET", "/v1/device/desc/%s" % did)
        if resp.get("code") != 0:
            return None
        return resp["data"]

    def opt(self, did, aid, value):
        body = json.dumps({"as": {str(aid): int(value)}})
        return self.call("POST", "/v1/device/opt/%s" % did, body)


class ZcyunAuthError(Exception):
    pass
