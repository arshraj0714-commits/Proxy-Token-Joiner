<div align="center">

```
   ███████╗██████╗ ██╗      ██████╗██╗   ██╗     ██╗ ██████╗ ██╗███╗   ██╗███████╗██████╗
   ██╔════╝██╔══██╗██║     ██╔════╝╚██╗ ██╔╝     ██║██╔═══██╗██║████╗  ██║██╔════╝██╔══██╗
   █████╗  ██████╔╝██║     ██║      ╚████╔╝ ███╗ ██║██║   ██║██║██╔██╗ ██║█████╗  ██████╔╝
   ██╔══╝  ██╔══██╗██║     ██║       ╚██╔╝  ╚███╔██║██║   ██║██║██║╚██╗██║██╔══╝  ██╔══██╗
   ███████╗██║  ██║███████╗╚██████╗   ██║    ╚████╔╝╚██████╔╝██║██║ ╚████║███████╗██║  ██║
   ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝     ╚═══╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
```

### ⚡ Discord Token Joiner • Request-Based • Proxy-Rotated ⚡
**Built By Eply** 💎

*Not authentication based — joins purely through your invite link.*

</div>

---

## ✨ Features

| Feature | Details |
|---|---|
| 🌐 **100% Request-Based** | No browser, no Selenium — pure HTTP via `requests` (Discord REST API v9) |
| 🔀 **Proxy-Only Traffic** | Every single request is routed through a proxy from `proxies.txt` |
| 🎭 **Fresh Proxy Per Token** | Each account/token gets its own never-before-used proxy |
| 🧩 **CAPTCHA Auto-Bypass by Rotation** | If a captcha appears → instantly switch to a new unused proxy, repeat until it goes away |
| 🚦 **Rate-Limit Rotation** | On `429` / rate-limit responses → swap to a brand-new proxy every time |
| ♻️ **Universal Proxy Formats** | `ip:port`, `user:pass@ip:port`, `proto://ip:port`, `proto://user:pass@ip:port`, http/https, socks4 (stocks4), socks5 (stocks5), database / ISP / residential / IPv4 / IPv6 / global lists |
| 🧵 **Configurable Threads** | Asks for thread count at startup |
| 🔗 **Flexible Invite Input** | Paste `discord.gg/xxxx`, full `https://discord.com/invite/xxxx`, or just the code |
| 🚫 **Smart Skipping** | Invalid tokens and locked accounts are detected & skipped automatically |
| 🔁 **Max 10 Retries** | Hard cap of 10 proxy-swaps per token, then gives up on that token |
| 🌈 **Beautiful CLI** | Colored logs, timestamps, ASCII banner, boxed summary table — exits cleanly when done |

---

## 📁 Project Structure

```
eply_joiner/
├── main.py          # ← run this
├── requirements.txt # dependencies
├── tokens.txt       # your tokens (email:pass:token OR token)
├── proxies.txt      # your proxies (any format, one per line)
├── README.md
└── LICENSE
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```
> For SOCKS4/SOCKS5 (`stocks4` / `stocks5`) proxies also install PySocks:
> `pip install PySocks`

### 2. Fill in `tokens.txt`
One entry per line — either format works:
```
email@mail.com:password:MTgPZ3kVbXyZ8aQwErTyUiOpAsDfGhJkLzXcVbNmQ
MTgPZ3kVbXyZ8aQwErTyUiOpAsDfGhJkLzXcVbNmQ
```

### 3. Fill in `proxies.txt`
Every common notation is auto-detected:
```
203.0.113.10:8080
bob:pw123@203.0.113.11:8080
http://203.0.113.12:8080
socks5://user:pass@203.0.113.13:1080
socks4://user:pass@198.51.100.7:1080
https://user:pass@198.51.100.9:8000
```

### 4. Run it
```bash
python main.py
```

The tool will ask:
```
➜ Threads (1-N, default 10): 5
➜ Server Invite Link (discord.gg/xxxx, full URL, or code): https://discord.gg/yourcode
```

Then it joins with every token — one fresh proxy each — rotating away from captchas
and rate limits, skipping invalid/locked accounts, and **closing the process itself**
with a colored summary once all tokens are handled.

---

## ⚙️ How It Works (per token)

```
acquire unused proxy ──► validate token (/users/@me/guilds)
        │                        │
        │                  401 → INVALID (skip)
        │             403 disabled → LOCKED (skip)
        │                        ▼
        │        lookup invite (/invites/<code>) → guild id + name
        │                        ▼
        └◄── captcha? ratelimited? error? ── POST join
                (swap proxy, retry ≤ 10)   (/guilds/<id>/members/@me)
                                             ▼
                                     201/204 → JOINED ✔
```

- **MAX_RETRIES = 10** per token (edit the constant at the top of `main.py`).
- When the proxy pool runs out of *unused* proxies, it recycles automatically.
- Credentials are masked in all console output (`***@host:port`).

---

## ⚠️ Disclaimer / Legal

This project is provided **for educational and network-testing purposes only**.
Automating user accounts violates the
[Discord Terms of Service](https://discord.com/terms) and can result in permanent
account and IP bans. Misuse of self-botting tools, mass account creation, or joining
servers you don't own may be unlawful in your jurisdiction. **You are solely
responsible for how you use this software. The author (Eply) accepts no liability
for any damage, bans, or legal consequences.**

---

## 📄 License

Distributed under the **MIT License** — see [`LICENSE`](LICENSE).

<div align="center">

*Made with 💎 by **Eply** — Eply Joiner v1.0.0*

</div>
