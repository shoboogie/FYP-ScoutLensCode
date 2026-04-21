"""Pipeline orchestrator: runs Steps 1–7 in sequence.

Usage:
    python -m pipeline.run_pipeline               # Full run
    python -m pipeline.run_pipeline --skip-ingest  # Skip download (use cached raw data)
    python -m pipeline.run_pipeline --force        # Re-run all steps even if cached
"""

from __future__ import annotations

import argparse
import logging
import time

from pipeline.ingest import ingest_events, ingest_lineups, ingest_matches
from pipeline.normalise_schema import normalise
from pipeline.compute_minutes import compute_minutes
from pipeline.quality_filter import quality_filter
from pipeline.engineer_features import engineer_features
from pipeline.classify_roles import classify_roles
from pipeline.build_index import build_index

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="ScoutLens data pipeline")
    parser.add_argument(
        "--skip-ingest", action="store_true",
        help="Skip StatsBomb download (use cached raw data)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-run all steps even if cached outputs exist",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    pipeline_t0 = time.perf_counter()
    logger.info("=" * 60)
    logger.info("ScoutLens Data Pipeline (Steps 1–7)")
    logger.info("=" * 60)

    # Step 1: Ingestion
    if args.skip_ingest:
        logger.info("Step 1: SKIPPED (--skip-ingest)")
    else:
        t0 = time.perf_counter()
        logger.info("Step 1: StatsBomb data ingestion")
        ingest_events(force=args.force)
        ingest_matches(force=args.force)
        ingest_lineups(force=args.force)
        logger.info("Step 1 complete in %.1fs", time.perf_counter() - t0)

    # Step 2: Schema normalisation
    t0 = time.perf_counter()
    logger.info("Step 2: Schema normalisation")
    normalise(force=args.force)
    logger.info("Step 2 complete in %.1fs", time.perf_counter() - t0)

    # Step 3: Minutes computation
    t0 = time.perf_counter()
    logger.info("Step 3: Minutes computation")
    compute_minutes(force=args.force)
    logger.info("Step 3 complete in %.1fs", time.perf_counter() - t0)

    # Step 4: Quality filtering
    t0 = time.perf_counter()
    logger.info("Step 4: Quality filtering")
    quality_filter(force=args.force)
    logger.info("Step 4 complete in %.1fs", time.perf_counter() - t0)

    # Step 5: Feature engineering
    t0 = time.perf_counter()
    logger.info("Step 5: Feature engineering")
    engineer_features(force=args.force)
    logger.info("Step 5 complete in %.1fs", time.perf_counter() - t0)

    # Step 6: Role classification
    t0 = time.perf_counter()
    logger.info("Step 6: Role classification")
    classify_roles(force=args.force)
    logger.info("Step 6 complete in %.1fs", time.perf_counter() - t0)

    # Step 7: FAISS index building
    t0 = time.perf_counter()
    logger.info("Step 7: FAISS index building")
    build_index(force=args.force)
    logger.info("Step 7 complete in %.1fs", time.perf_counter() - t0)

    total = time.perf_counter() - pipeline_t0
    logger.info("=" * 60)
    logger.info("Pipeline complete in %.1fs (%.1f min)", total, total / 60)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
