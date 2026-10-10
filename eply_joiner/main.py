#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
╔══════════════════════════════════════════════════════════════════╗
║                        E P L Y   J O I N E R                    ║
║                                                                  ║
║        Discord Token Joiner  •  Fully Request-Based              ║
║        Built By Eply          •  CLI / Terminal                  ║
╚══════════════════════════════════════════════════════════════════╝

Joins a Discord server via an invite link using tokens stored in
tokens.txt (format: email:password:token  OR  just token), routing
every request through rotating proxies listed in proxies.txt.

Every token gets its own fresh proxy. If a CAPTCHA (400 + captcha-key)
or a rate limit (429) is returned, the tool instantly switches to a new
unused proxy and retries — up to MAX_RETRIES times per token.

Educational / network-testing tool. Use responsibly.
"""

import os
import re
import sys
import json
import time
import base64
import random
import threading
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("[!] Missing dependency 'requests'. Run:  pip install -r requirements.txt")
    sys.exit(1)

try:
    from colorama import init, Fore, Style
    init(autoreset=False)
except ImportError:
    class _NoColor:
        def __getattr__(self, n): return ""
    Fore = Style = _NoColor()

# ──────────────────────────────── CONFIG ────────────────────────────────
BANNER = r"""
   ███████╗██████╗ ██╗      ██████╗██╗   ██╗     ██╗ ██████╗ ██╗███╗   ██╗███████╗██████╗
   ██╔════╝██╔══██╗██║     ██╔════╝╚██╗ ██╔╝     ██║██╔═══██╗██║████╗  ██║██╔════╝██╔══██╗
   █████╗  ██████╔╝██║     ██║      ╚████╔╝ ███╗ ██║██║   ██║██║██╔██╗ ██║█████╗  ██████╔╝
   ██╔══╝  ██╔══██╗██║     ██║       ╚██╔╝  ╚███╔██║██║   ██║██║██║╚██╗██║██╔══╝  ██╔══██╗
   ███████╗██║  ██║███████╗╚██████╗   ██║    ╚████╔╝╚██████╔╝██║██║ ╚████║███████╗██║  ██║
   ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝     ╚═══╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
"""

SUB_BANNER = f"""{Fore.CYAN}{Style.BRIGHT}
               ⚡  Discord Token Joiner  •  Request-Based  •  Proxy-Rotated  ⚡
                         {Fore.YELLOW}Built By{Fore.WHITE} {Style.BRIGHT}Eply{Style.RESET_ALL}
               {Fore.MAGENTA}══════════════════════════════════════════════════════════════{Style.RESET_ALL}
"""

VERSION          = "1.0.0"
TOKENS_FILE      = "tokens.txt"
PROXIES_FILE     = "proxies.txt"
MAX_RETRIES      = 10           # max attempts per token (captcha / ratelimit / errors)
API_BASE         = "https://discord.com/api/v9"

# A handful of realistic desktop User-Agents for header rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

# ──────────────────────────────── LOGGING ────────────────────────────────
def _ts():
    return f"{Style.DIM}[{time.strftime('%H:%M:%S')}]{Style.RESET_ALL}"

def log_info(msg):    print(f"{_ts()} {Fore.CYAN}  INFO  {Style.RESET_ALL} │ {msg}", flush=True)
def log_ok(msg):      print(f"{_ts()} {Fore.LIGHTGREEN_EX}   ✔    {Style.RESET_ALL} │ {Fore.GREEN}{msg}{Style.RESET_ALL}", flush=True)
def log_warn(msg):    print(f"{_ts()} {Fore.YELLOW}  WARN  {Style.RESET_ALL} │ {Fore.YELLOW}{msg}{Style.RESET_ALL}", flush=True)
def log_err(msg):     print(f"{_ts()} {Fore.LIGHTRED_EX}  ERR   {Style.RESET_ALL} │ {Fore.RED}{msg}{Style.RESET_ALL}", flush=True)
def log_captcha(msg): print(f"{_ts()} {Fore.MAGENTA} CAPTA {Style.RESET_ALL} │ {Fore.MAGENTA}{msg}{Style.RESET_ALL}", flush=True)
def log_rate(msg):    print(f"{_ts()} {Fore.LIGHTBLUE_EX}  RATE  {Style.RESET_ALL} │ {Fore.LIGHTBLUE_EX}{msg}{Style.RESET_ALL}", flush=True)
def log_swap(msg):    print(f"{_ts()} {Fore.LIGHTMAGENTA_EX} SWAP  {Style.RESET_ALL} │ {Fore.LIGHTMAGENTA_EX}🔄 {msg}{Style.RESET_ALL}", flush=True)

def log_title(msg):
    bar = "═" * 68
    print(f"\n{Fore.CYAN}{Style.BRIGHT}╔{bar}╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}║  {msg.center(66)}{Style.RESET_ALL}{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}╚{bar}╝{Style.RESET_ALL}\n", flush=True)

def short_proxy(p):
    """Mask credentials when printing a proxy."""
    if "@" in p:
        scheme = p.split("://", 1)[0] + "://" if "://" in p else ""
        host = p.split("@", 1)[1]
        return f"{scheme}***@{host}"
    return p

# ─────────────────────────────── PROXY POOL ───────────────────────────────
class ProxyPool:
    """Thread-safe pool that hands out ONE unused proxy per acquire().

    Accepts every common proxy format:
        ip:port | user:pass@ip:port | protocol://ip:port
        protocol://user:pass@ip:port | http / https / socks4 / socks5 ...
    """

    _LINE_RE = re.compile(r"^(?P<scheme>[a-zA-Z][\w+.\-]*://)?(?P<rest>.+)$")

    def __init__(self, raw_lines):
        self.proxies = []
        self.used    = set()
        self._lock   = threading.Lock()
        for line in raw_lines:
            norm = self._normalize(line)
            if norm:
                self.proxies.append(norm)
        random.shuffle(self.proxies)

    @classmethod
    def _normalize(cls, raw):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            return None
        m = cls._LINE_RE.match(raw)
        scheme, rest = (m.group("scheme") or "").rstrip(":/").lower(), m.group("rest")
        if scheme and scheme not in ("http", "https", "socks4", "socks5", "socks5h"):
            scheme = ""                                   # unknown prefix -> treat as plain host blob
        if "@" in rest:
            auth, host = rest.rsplit("@", 1)
            if ":" not in host:
                return None
            scheme = scheme or "http"                     # creds without scheme -> assume http
            return f"{scheme}://{auth}@{host}"
        if ":" in rest:                                   # plain ip:port
            return f"{scheme or 'http'}://{rest}"
        return None

    def size(self):
        return len(self.proxies)

    def acquire(self):
        """Return a fresh (never-used) proxy, or None if all are burned."""
        with self._lock:
            for p in self.proxies:
                if p not in self.used:
                    self.used.add(p)
                    return p
        return None

    def recycle(self):
        """Reset used flags (called when we need more proxies than the pool has)."""
        with self._lock:
            self.used.clear()

    @staticmethod
    def build_requests_dict(proxy):
        """Convert 'scheme://user:pass@host:port' into the dict `requests` wants."""
        try:
            parsed = urlparse(proxy)
            scheme = parsed.scheme or "http"
            host   = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
            auth   = ""
            if parsed.username:
                pw = requests.utils.unquote(parsed.password or "")
                auth = f"{requests.utils.unquote(parsed.username)}:{pw}@"
            base = f"{scheme}://{auth}{host}"
            return {"http": base, "https": base}
        except Exception:
            return {"http": proxy, "https": proxy}

# ─────────────────────────────── TOKEN LOADER ───────────────────────────────
# A Discord token is three dot-separated base64-ish segments:
#     <uid-b64>.<timestamp>.<hmac>          (chars: A-Z a-z 0-9 _ -)
# Lines in tokens.txt may be `email:password:token` or a bare `token`.
# Passwords can contain ':' and '.', so we don't split on ':' blindly. Instead
# we scan the line right-to-left, treating each position as the end of the
# token's LAST segment, and check whether the preceding two segments are valid
# too. The first (right-most) such match wins — which is exactly where the
# real token sits in both supported formats.
_TOKEN_SEG = re.compile(r"[A-Za-z0-9_\-]{4,}")

def _extract_token(line):
    # Iterate over dot positions right-to-left. p3 = last dot of the token,
    # p2 = second-to-last dot. seg1 is whatever precedes p2 after the final
    # ':' (email:password:token) or the whole prefix (bare token line).
    dots = [i for i, c in enumerate(line) if c == "."]
    for idx3 in range(len(dots) - 1, 0, -1):
        p3 = dots[idx3]
        for idx2 in range(idx3 - 1, -1, -1):
            p2 = dots[idx2]
            seg3 = line[p3 + 1:]
            seg2 = line[p2 + 1:p3]
            if not (_TOKEN_SEG.fullmatch(seg3) and _TOKEN_SEG.fullmatch(seg2)):
                continue
            prefix = line[:p2]
            if ":" in prefix:                        # email:password: → cut before final colon
                seg1 = prefix[prefix.rfind(":") + 1:]
            else:                                    # bare token line
                seg1 = prefix
            if _TOKEN_SEG.fullmatch(seg1):
                return f"{seg1}.{seg2}.{seg3}"
    # fallback: classic email:pass:token with a dot-less legacy token
    parts = line.split(":")
    if "@" in (parts[0] if parts else "") and len(parts) >= 3:
        cand = ":".join(parts[2:]).strip()
        if len(cand) >= 24 and not any(c.isspace() for c in cand):
            return cand
    return None

def load_tokens(path):
    """Parse tokens.txt: lines of `email:pass:token` OR bare `token`. Returns list[str]."""
    tokens = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tok = _extract_token(line)
            if tok:
                tokens.append(tok)
    return tokens

# ─────────────────────────────── INVITE CODE ───────────────────────────────
_INVITE_RE = re.compile(r"(?:discord(?:app)?\.com/(?:invite|join)/|discord\.gg/)([A-Za-z0-9\-]{2,32})",
                        re.IGNORECASE)
_BARE_CODE = re.compile(r"^[A-Za-z0-9\-]{2,32}$")

def extract_invite(user_input):
    s = user_input.strip()
    m = _INVITE_RE.search(s)
    if m:
        return m.group(1)
    if _BARE_CODE.match(s):                    # user typed just the code
        return s
    return None

# ─────────────────────────────── JOINER CORE ───────────────────────────────
class EplyJoiner:
    def __init__(self, invite_code, pool):
        self.invite = invite_code
        self.pool   = pool
        self.ok_count      = 0
        self.fail_count    = 0
        self.invalid_count = 0
        self.locked_count  = 0
        self._counter_lock = threading.Lock()

    # ---- helpers -------------------------------------------------------
    @staticmethod
    def _super_properties(ua):
        if "Firefox" in ua:      browser, os_name = "Firefox", "Windows"
        elif "Edg" in ua:        browser, os_name = "Edge", "Windows"
        elif "Mac OS X" in ua:   browser, os_name = "Chrome", "macOS"
        elif "Linux" in ua:      browser, os_name = "Chrome", "Linux"
        else:                    browser, os_name = "Chrome", "Windows"
        props = {
            "os": os_name,
            "browser": browser,
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": ua,
            "browser_version": "".join(re.findall(r"\d+", ua)[:2]),
            "os_version": "10",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": str(random.randint(200000, 300000)),
            "client_event_source": None,
        }
        return base64.b64encode(json.dumps(props, separators=(",", ":")).encode()).decode()

    @classmethod
    def _build_headers(cls, token):
        ua = random.choice(USER_AGENTS)
        locale = random.choice(["en-US", "en-GB", "de", "fr", "es-ES"])
        return {
            "Authorization": token,
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": f"{locale},en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "X-Super-Properties": cls._super_properties(ua),
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    @staticmethod
    def _is_captcha(status, body):
        if status != 400:
            return False
        low = body.lower()
        return ("captcha" in low or '"captcha_key"' in low or "need verification" in low)

    @staticmethod
    def _is_ratelimited(status, body):
        if status == 429:
            return True
        low = body.lower()
        return status in (401, 403) and ("ratelimit" in low or "rate limit" in low)

    def _count(self, attr, n=1):
        with self._counter_lock:
            setattr(self, attr, getattr(self, attr) + n)

    def _account_status(self, session, proxies):
        """Validate token via /users/@me/guilds before joining."""
        try:
            r = session.get(f"{API_BASE}/users/@me/guilds",
                            proxies=proxies, timeout=20, allow_redirects=False)
            if r.status_code == 401:
                return "invalid"
            if r.status_code == 403 and "disabled" in r.text.lower():
                return "locked"
            if r.status_code >= 500:
                return "error"
            return "valid"
        except requests.RequestException:
            return "error"

    # ---- main worker ---------------------------------------------------
    def join_token(self, index, total, token):
        tag = f"#{index}/{total}"
        for attempt in range(1, MAX_RETRIES + 1):

            proxy = self.pool.acquire()
            if proxy is None:                       # pool exhausted → recycle & keep going
                self.pool.recycle()
                proxy = self.pool.acquire()
            if proxy is None:
                log_err(f"{tag} No proxies available at all — check {PROXIES_FILE}.")
                self._count("fail_count")
                return
            proxies = ProxyPool.build_requests_dict(proxy)
            shown   = short_proxy(proxy)

            sess = requests.Session()
            sess.headers.update(self._build_headers(token))

            # 1) validate account (cheap, same proxy)
            state = self._account_status(sess, proxies)
            if state == "invalid":
                log_warn(f"{tag} Token INVALID (bad login) — skipping.")
                self._count("invalid_count")
                return
            if state == "locked":
                log_warn(f"{tag} Token LOCKED / phone-verification required — skipping.")
                self._count("locked_count")
                return

            # 2) resolve invite metadata (guild name / guild id)
            guild_name, guild_id = "?", None
            try:
                inv = sess.get(f"{API_BASE}/invites/{self.invite}?with_counts=true",
                               proxies=proxies, timeout=20)
                if inv.status_code == 200:
                    data = inv.json()
                    guild_name = data.get("guild", {}).get("name", "?")
                    guild_id   = data.get("guild", {}).get("id")
                elif inv.status_code == 404:
                    log_err(f"{tag} Invite code '{self.invite}' not found / expired.")
                    self._count("fail_count")
                    return
                elif self._is_captcha(inv.status_code, inv.text) or \
                     self._is_ratelimited(inv.status_code, inv.text):
                    reason = "CAPTCHA" if self._is_captcha(inv.status_code, inv.text) else "RATE LIMIT"
                    log_warn(f"{tag} {reason} hit on invite lookup ({shown}) — swapping proxy.")
                    log_swap("rotating to a fresh proxy…")
                    continue
            except requests.RequestException:
                pass                                # proceed blindly if lookup fails

            # 3) THE JOIN — POST /api/v9/guilds/{id}/members/@me
            payload = json.dumps({"gift_code_sku_id": None, "captcha_key": None})
            url = (f"{API_BASE}/guilds/{guild_id}/members/@me"
                   if guild_id else f"{API_BASE}/invites/{self.invite}")
            try:
                resp = sess.post(url, data=payload, proxies=proxies, timeout=25,
                                 allow_redirects=False)
            except requests.RequestException as e:
                log_warn(f"{tag} Network error on attempt {attempt} ({shown}): "
                         f"{e.__class__.__name__} — swapping proxy.")
                log_swap("trying next proxy…")
                continue

            status, body = resp.status_code, resp.text or ""

            if status in (201, 204) or (status == 200 and '"joined_at"' in body):
                log_ok(f"{tag} JOINED 「{guild_name}」 via {shown}")
                self._count("ok_count")
                return

            if status == 401:
                log_warn(f"{tag} Token rejected (401) — marking invalid.")
                self._count("invalid_count")
                return

            if status == 403 and "disabled" in body.lower():
                log_warn(f"{tag} Account locked / requires verification — skipping.")
                self._count("locked_count")
                return

            if self._is_ratelimited(status, body):
                wait = 0.0
                try:
                    wait = float(resp.headers.get("Retry-After") or
                                 resp.json().get("retry_after", 0))
                except Exception:
                    pass
                log_rate(f"{tag} RATE LIMITED (429, retry-after≈{wait:.0f}s) on {shown} "
                         f"— switching proxy.")
                log_swap("rotating to a fresh proxy…")
                time.sleep(min(wait, 5))
                continue

            if self._is_captcha(status, body):
                log_captcha(f"{tag} CAPTCHA detected on {shown} "
                            f"— switching to a new unused proxy.")
                log_swap("rotating to a fresh proxy…")
                continue

            if status == 200 and "already" in body.lower():
                log_ok(f"{tag} Already a member of 「{guild_name}」 — counted as success.")
                self._count("ok_count")
                return

            if 500 <= status < 600:
                log_warn(f"{tag} Server error {status} on {shown} — swapping proxy.")
                continue

            log_err(f"{tag} Unexpected response {status}: {body[:140]} "
                    f"— swapping proxy (attempt {attempt}/{MAX_RETRIES}).")

        log_err(f"{tag} Gave up after {MAX_RETRIES} retries.")
        self._count("fail_count")

# ─────────────────────────────── INPUT PROMPTS ───────────────────────────────
def prompt_threads(total):
    default = min(10, total)
    while True:
        raw = input(f"{Fore.CYAN}{Style.BRIGHT} ➜ Threads {Style.RESET_ALL}"
                    f"{Style.DIM}(1-{max(total, 1)}, default {default}): {Style.RESET_ALL}").strip()
        if not raw:
            return max(1, default)
        try:
            n = int(raw)
            if 1 <= n <= max(total, 1):
                return n
            print(f"{Fore.RED}   ✖ Enter a number between 1 and {max(total, 1)}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}   ✖ That isn't a number.{Style.RESET_ALL}")

def prompt_invite():
    while True:
        raw = input(f"{Fore.CYAN}{Style.BRIGHT} ➜ Server Invite Link "
                    f"{Style.RESET_ALL}{Style.DIM}(discord.gg/xxxx, full URL, or code): "
                    f"{Style.RESET_ALL}").strip()
        code = extract_invite(raw)
        if code:
            log_ok(f"Invite code resolved: {Fore.LIGHTYELLOW_EX}{code}{Style.RESET_ALL}")
            return code
        print(f"{Fore.RED}   ✖ Couldn't read an invite code from that. Try again.{Style.RESET_ALL}")

# ─────────────────────────────── MAIN ───────────────────────────────
def main():
    print(f"{Fore.CYAN}{Style.BRIGHT}{BANNER}{Style.RESET_ALL}")
    print(SUB_BANNER)
    print(f"{Style.DIM}{'':>18}version {VERSION}  •  threads → invite → join → exit{Style.RESET_ALL}\n")

    # ── files ──
    if not os.path.isfile(TOKENS_FILE):
        log_err(f"{TOKENS_FILE} not found! Create it with lines of `token` or `email:pass:token`.")
        sys.exit(1)
    if not os.path.isfile(PROXIES_FILE):
        log_err(f"{PROXIES_FILE} not found! Add your proxies (any format, one per line).")
        sys.exit(1)

    with open(PROXIES_FILE, "r", encoding="utf-8", errors="ignore") as fh:
        pool = ProxyPool(fh.readlines())
    if pool.size() == 0:
        log_err(f"No usable proxies parsed from {PROXIES_FILE}.")
        sys.exit(1)
    log_ok(f"Loaded {pool.size()} proxies from {PROXIES_FILE} (all formats accepted).")

    tokens = load_tokens(TOKENS_FILE)
    if not tokens:
        log_err(f"No valid tokens parsed from {TOKENS_FILE}.")
        sys.exit(1)
    log_ok(f"Loaded {len(tokens)} tokens from {TOKENS_FILE}.")

    # ── prompts ──
    threads = prompt_threads(len(tokens))
    invite  = prompt_invite()

    log_title(f"EPLY JOINER ENGAGED  •  invite={invite}  •  threads={threads}  "
              f"•  retries={MAX_RETRIES}")

    joiner = EplyJoiner(invite, pool)
    total  = len(tokens)
    start  = time.time()

    # simple thread pool (no external deps): shared queue + workers
    queue = list(enumerate(tokens, start=1))
    qlock = threading.Lock()

    def worker():
        while True:
            with qlock:
                if not queue:
                    return
                idx, tok = queue.pop(0)
            joiner.join_token(idx, total, tok)

    workers = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
    for w in workers: w.start()
    for w in workers: w.join()

    elapsed = time.time() - start

    # ── summary ──
    bar = "═" * 68
    print(f"\n{Fore.CYAN}{Style.BRIGHT}╔{bar}╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}{Style.BRIGHT}"
          f"{'  E P L Y   J O I N E R   —   F I N I S H E D ':^66}{Style.RESET_ALL}"
          f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}╠{bar}╣{Style.RESET_ALL}")
    rows = [
        (Fore.LIGHTGREEN_EX, "✔ Joined successfully", joiner.ok_count),
        (Fore.RED,           "✘ Failed / gave up",    joiner.fail_count),
        (Fore.YELLOW,        "⚠ Invalid tokens",      joiner.invalid_count),
        (Fore.MAGENTA,       "⛒ Locked accounts",     joiner.locked_count),
        (Fore.CYAN,          "Σ Total processed",     total),
        (Style.BRIGHT,       "⏱ Time elapsed",        f"{elapsed:.1f}s"),
    ]
    for color, label, val in rows:
        text = f"   {color}{label:<22}{Style.RESET_ALL} {Style.BRIGHT}{val:>12}{Style.RESET_ALL}"
        print(f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}{text:<66}{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}╚{bar}╝{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}{Style.BRIGHT}                 Thanks for using Eply Joiner — Built By Eply 💎{Style.RESET_ALL}\n")

    sys.exit(0)   # close the process once every token has been handled

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}   Interrupted by user — exiting.{Style.RESET_ALL}")
        sys.exit(130)
