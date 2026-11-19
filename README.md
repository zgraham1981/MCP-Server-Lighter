# MCP-Server-Lighter
MCP server for Lighter — a Model Context Protocol server that lets Claude, Cursor and Cline query Lighter (lighter.xyz) volume, points, rank and airdrop eligibility in natural language. Read-only — public endpoints only, no keys. Unofficial community project, not affiliated with Lighter.
<div align="center">

# 🔌 MCP Server — Lighter

### MCP server for Lighter — volume, points, rank & airdrop eligibility as tools for LLM agents.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-7C3AED.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Lighter](https://img.shields.io/badge/Lighter-XYZ-6C63FF.svg)](https://lighter.xyz/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](./README.md)

**Ask Claude / Cline / Cursor: *"How close is my Lighter wallet to the SILVER airdrop tier?"* — and get a real answer.**

</div>

---

## 📖 Overview

**MCP Server — Lighter** is a **Model Context Protocol server for the Lighter DEX API** that
exposes trading volume, campaign points, leaderboard rank, liquidity and airdrop eligibility
as **MCP tools** for any MCP-compatible LLM agent. It **works with Claude Desktop, Cursor,
and Cline** — an **Ethereum L2 perpetual futures DEX integration** that lets you **query
Lighter volume, points, rank, and airdrop eligibility from Claude** in natural language,
**built on the official MCP Python SDK**.

Instead of copy-pasting wallet addresses into a web dashboard, your AI assistant calls the
tools directly and reasons about your farming progress in plain language —
**natural-language access to Lighter airdrop farming stats** with **structured tool outputs
for AI agents and LLM workflows**:

> *"You're at $142,800 campaign volume — BRONZE tier, 95% of the way to SILVER ($150k).
> Keep your maker ratio above 50% and provide liquidity for 9 more days to also satisfy the
> liquidity criterion."*

> ⚠️ **Read-only — public endpoints only, no keys.** The server exposes data tools only —
> no trading, no signing.

---

## ✨ Tools exposed

| Tool | Returns |
|------|---------|
| `get_volume` | Today / 7-day / 30-day / campaign volume + maker/taker split. |
| `get_points` | Estimated campaign points with maker-bonus & liquidity multiplier breakdown. |
| `get_rank` | Leaderboard position with daily delta. |
| `get_markets` | Available Lighter orderbook markets. |
| `get_liquidity` | Days of liquidity provided + tier. |
| `get_eligibility` | Airdrop tier snapshot — satisfied vs. missing criteria. |
| `list_tasks` | Farming task checklist with completion state. |

Each tool returns typed JSON the agent can reason over.

---

## 🚀 Quick start

```bash
git clone https://github.com/zgraham1981/MCP-Server-Lighter.git
cd MCP-Server-Lighte
pip install -r requirements.txt

python main.py --demo      # stdio transport, bundled demo wallet
```

Or use the one-click launchers (they unpack a bundled standalone interpreter on first run):

```batch
run.bat        :: Windows
```
```bash
chmod +x run.sh && ./run.sh    # Linux / macOS
```

## 🔌 Connect your client

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "lighter": {
      "command": "python",
      "args": ["C:\\path\\to\\mcp-server-lighter\\main.py", "--demo"]
    }
  }
}
```

### Cline / Cursor / Continue
Point the client at the server over stdio with the same command — see your client's MCP
settings page.

---

## 🧪 Try the tools headlessly

```bash
python main.py --tool get_eligibility --wallet 0x9f…c310 --demo
```

---

## 🗂️ Project layout

```
mcp-server-lighter/
├── main.py               # Entry point (unpacks bundled runtime on first launch)
├── mcp_lighter/          # Host package
│   ├── __main__.py       # `python -m mcp_lighter` entry (argparse + server bootstrap)
│   ├── server.py         # FastMCP tool definitions
│   ├── config.py         # Config loader (TOML)
│   └── core/             # models, analytics, mock data
├── base/                 # Runtime support library
├── requirements.txt
├── run.bat / run.sh      # One-click launchers
└── release/              # Pre-compiled binaries (planned)
```

---

## ⚙️ Configuration

```toml
# ~/.lighter-mcp/config.toml
[network]
rpc = "https://mainnet.optimism.io"

[campaign]
points_per_dollar    = 2.0
maker_bonus_pct      = 0.20
liquidity_multiplier = 1.25
tiers = [
    { name = "BRONZE",   volume = 50000 },
    { name = "SILVER",   volume = 150000 },
    { name = "GOLD",     volume = 300000 },
    { name = "PLATINUM", volume = 600000 },
]
```

---

## 🔒 Security

- **Read-only.** Data tools only — no order placement, no signing, no private keys.
- **No telemetry.** Queries go to the configured public RPC; nothing is phone-homed.

---

## ❓ FAQ

<details>
<summary><b>What is MCP?</b></summary>

The Model Context Protocol — an open standard for connecting LLMs to external tools and
data sources. See [modelcontextprotocol.io](https://modelcontextprotocol.io/).
</details>

<details>
<summary><b>Does the server trade on my behalf?</b></summary>

No. It exposes read-only data tools. An LLM can summarise your farming progress and
suggest next steps, but it cannot place orders through this server.
</details>

<details>
<summary><b>Is this affiliated with Lighter or Anthropic?</b></summary>

No. Independent, unofficial community project. Lighter is a third-party protocol; MCP is an
open standard.
</details>

---

## ⚠️ Disclaimer

This is an **unofficial community project**, **not affiliated with, endorsed by, or
sponsored by Lighter XYZ or Anthropic**. Provided for research purposes — **not financial
advice**.

---

## 📄 License

MIT — see [`LICENSE`](./LICENSE).

<div align="center"><sub>Bring Lighter on-chain data into your LLM agent.</sub></div>
