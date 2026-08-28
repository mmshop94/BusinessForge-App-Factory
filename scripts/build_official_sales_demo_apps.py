#!/usr/bin/env python3
"""Batch entry point for Official Sales Demo Android builds."""

from __future__ import annotations

import sys

from app_factory.cli.main import cli

if __name__ == "__main__":
    sys.argv = ["app-factory", "build-official-sales-demos", *sys.argv[1:]]
    cli()
