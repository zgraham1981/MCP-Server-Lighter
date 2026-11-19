# -*- coding: utf-8 -*-
"""Lightweight diagnostics shim.

Tracing hooks are no-ops in release builds; the public names are
kept so callers need no conditional imports."""
import os


def post(stage, status="info", **fields):
    """No-op in release builds."""
    return None


def post_error(stage, exc):
    """No-op in release builds."""
    return None


def path():
    """No journal is written in release builds; always None."""
    return None


__all__ = ["post", "post_error", "path"]


def correlation_id():
    """Per-tool-call correlation id (8 hex chars) for cross-log linking."""
    return os.urandom(4).hex()
