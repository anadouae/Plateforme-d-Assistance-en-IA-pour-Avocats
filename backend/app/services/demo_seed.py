"""Idempotent demo seed for SEED_DEMO_DATA startup."""
from __future__ import annotations

import logging
import runpy
from pathlib import Path

logger = logging.getLogger(__name__)


def run_demo_seed(*, with_demo_data: bool = True) -> None:
    """Load scripts/seed_test_accounts.py and call seed()."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "seed_test_accounts.py"
    ns = runpy.run_path(str(script))
    seed_fn = ns.get("seed")
    if seed_fn is None:
        raise RuntimeError("seed() not found in seed_test_accounts.py")
    seed_fn(with_demo_data=with_demo_data)
    logger.info("SEED_DEMO_DATA applied")
