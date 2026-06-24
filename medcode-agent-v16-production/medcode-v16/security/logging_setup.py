"""
MedCode AI — Structured Logging Setup
======================================
Loads config/logging.json in production, uses console format in development.
Creates module-specific loggers with non-blocking handlers.
"""

from __future__ import annotations

import json
import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Dict


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    json_format: bool = True,
) -> Dict[str, logging.Logger]:
    """
    Configure structured logging for MedCode AI.

    In production (json_format=True): loads config/logging.json with JSON formatter.
    In development (json_format=False): uses human-readable console format.

    Returns dict of configured module loggers.
    """
    testing = os.environ.get("TESTING", "0") == "1"
    environment = os.environ.get("MEDCODE_ENV", "development")
    use_json = json_format and environment == "production"

    if use_json:
        _load_json_config(log_dir, log_level)
    else:
        _setup_console_config(log_level)

    loggers = {}
    module_names = [
        "medcode.api",
        "medcode.security",
        "medcode.agents",
        "medcode.database",
        "medcode.audit",
    ]
    for name in module_names:
        loggers[name] = logging.getLogger(name)

    root_logger = logging.getLogger("medcode")
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    return loggers


def _load_json_config(log_dir: str, log_level: str) -> None:
    """Load the JSON logging config from config/logging.json."""
    config_path = Path(__file__).parent.parent / "config" / "logging.json"

    if not config_path.exists():
        _setup_console_config(log_level)
        return

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        log_path = Path(log_dir)
        if not log_path.exists():
            log_path.mkdir(parents=True, exist_ok=True)

        for handler_name, handler_cfg in config.get("handlers", {}).items():
            if "filename" in handler_cfg:
                original = handler_cfg["filename"]
                handler_cfg["filename"] = str(log_path / Path(original).name)

        config["handlers"]["console"]["level"] = log_level
        config["loggers"][""]["level"] = log_level

        logging.config.dictConfig(config)
    except Exception:
        _setup_console_config(log_level)


def _setup_console_config(log_level: str) -> None:
    """Fallback: simple console-based logging."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    for name in ["medcode", "uvicorn", "httpx", "httpcore"]:
        logger = logging.getLogger(name)
        logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)
