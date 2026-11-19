"""Entry point: run the MCP server, or call a single tool headlessly and exit."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from base import bootstrap

from mcp_lighter import __version__
from mcp_lighter.config import Config, default_config_path
from mcp_lighter.server import TOOLS


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mcp-server-lighter",
                                description="MCP server exposing Lighter data to LLM agents.")
    p.add_argument("--version", "-V", action="version", version=f"mcp-server-lighter {__version__}")
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--demo", action="store_true", help="use the bundled demo dataset")
    p.add_argument("--tool", default=None,
                   help=f"call one tool headlessly and exit: {', '.join(TOOLS)}")
    p.add_argument("--wallet", default=None, help="wallet address (default: demo wallet)")
    p.add_argument("--transport", default="stdio", choices=["stdio"],
                   help="MCP transport (only stdio supported today)")
    return p


@bootstrap
def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    demo = args.demo or os.environ.get("LIGHTER_MCP_DEMO", "") == "1"
    config = Config.load(args.config or Path(os.environ.get("LIGHTER_MCP_CONFIG",
                                                            str(default_config_path()))), demo=demo)

    # Headless single-tool mode: call the function and print JSON.
    if args.tool:
        fn = TOOLS.get(args.tool)
        if fn is None:
            print(f"error: unknown tool '{args.tool}'. available: {', '.join(TOOLS)}",
                  file=sys.stderr)
            return 2
        # Apply the chosen config so tool functions read it.
        from mcp_lighter import server
        server._state["config"] = config
        result = fn(args.wallet) if "wallet" in fn.__code__.co_varnames else fn()
        print(json.dumps(result, indent=2, default=str))
        return 0

    # Server mode: register tools on FastMCP and run the stdio transport.
    try:
        from mcp_lighter.server import build_server
        build_server(config).run(transport=args.transport)
    except ImportError as exc:  # pragma: no cover
        print(f"error: MCP SDK not installed ({exc}). Run `pip install -r requirements.txt`.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
