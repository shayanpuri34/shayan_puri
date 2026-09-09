"""Configuration management module.
Loads YAML settings, parses environment variables, and creates directory trees.
"""

from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class PathConfig:
    project_root: Path
    raw_data_dir: Path
    processed_data_dir: Path
    reports_dir: Path
    figures_dir: Path
    logs_dir: Path


@dataclass
class UniverseConfig:
    primary_name: str
    benchmark: str
    fallback: List[str]
    sector_map: Dict[str, str]


@dataclass
class AppConfig:
    random_state: int
    paths: PathConfig
    universe: UniverseConfig
    start_date: str
    end_date: str
    data_priority: List[str]
    rate_limiting: Dict[str, Any]
    event_study: Dict[str, Any]
    features: Dict[str, Any]
    machine_learning: Dict[str, Any]
    signals: Dict[str, Any]
    portfolio: Dict[str, Any]
    transaction_costs: Dict[str, Any]
    api_keys: Dict[str, Optional[str]] = field(default_factory=dict)


def setup_logger(name: str = "earnings_engine", log_dir: Optional[Path] = None) -> logging.Logger:
    """Configures and returns a centralized logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        if log_dir is not None:
            log_dir.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_dir / "engine.log")
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Loads configuration from YAML file and environment variables."""
    if config_path is None:
        # Default to root/config/config.yaml
        current_dir = Path(__file__).resolve().parent
        config_path = str(current_dir.parent / "config" / "config.yaml")

    p = Path(config_path).resolve()
    project_root = p.parent.parent

    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        data = {}

    # Paths resolution
    paths_data = data.get("paths", {})
    paths = PathConfig(
        project_root=project_root,
        raw_data_dir=project_root / paths_data.get("raw_data_dir", "data/raw"),
        processed_data_dir=project_root / paths_data.get("processed_data_dir", "data/processed"),
        reports_dir=project_root / paths_data.get("reports_dir", "reports"),
        figures_dir=project_root / paths_data.get("figures_dir", "reports/figures"),
        logs_dir=project_root / paths_data.get("logs_dir", "logs"),
    )

    # Ensure directories exist
    for d in [paths.raw_data_dir, paths.processed_data_dir, paths.reports_dir, paths.figures_dir, paths.logs_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Read API keys from env (NEVER print or log secrets)
    api_keys = {
        "ALPHA_VANTAGE_API_KEY": os.getenv("ALPHA_VANTAGE_API_KEY"),
        "FMP_API_KEY": os.getenv("FMP_API_KEY"),
        "POLYGON_API_KEY": os.getenv("POLYGON_API_KEY"),
        "FRED_API_KEY": os.getenv("FRED_API_KEY"),
    }

    universe_data = data.get("universe", {})
    universe = UniverseConfig(
        primary_name=universe_data.get("primary_name", "SP500"),
        benchmark=universe_data.get("benchmark", "SPY"),
        fallback=universe_data.get("fallback", [
            "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA",
            "JPM", "BAC", "XOM", "CVX", "WMT", "COST"
        ]),
        sector_map=universe_data.get("sector_map", {})
    )

    dates_data = data.get("dates", {})
    start_date = str(dates_data.get("start_date", "2016-01-01"))
    end_date = str(dates_data.get("end_date", "2024-12-31"))

    return AppConfig(
        random_state=data.get("project", {}).get("random_state", 42),
        paths=paths,
        universe=universe,
        start_date=start_date,
        end_date=end_date,
        data_priority=data.get("data_priority", ["alpha_vantage", "fmp", "yfinance", "sec"]),
        rate_limiting=data.get("rate_limiting", {
            "initial_delay_sec": 1.0,
            "max_delay_sec": 16.0,
            "max_retries": 4,
            "timeout_sec": 15
        }),
        event_study=data.get("event_study", {}),
        features=data.get("features", {}),
        machine_learning=data.get("machine_learning", {}),
        signals=data.get("signals", {}),
        portfolio=data.get("portfolio", {}),
        transaction_costs=data.get("transaction_costs", {}),
        api_keys=api_keys
    )
