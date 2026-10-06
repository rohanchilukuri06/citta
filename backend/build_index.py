import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ensure backend folder is in path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from vector_indexer import build_vector_database
from inspect_index import inspect_unified_index

async def main():
    parser = argparse.ArgumentParser(description="CittaAI Unified Vector Database Builder & Diagnostic Tool")
    parser.add_argument("--force", action="store_true", help="Force rebuild of vector database even if hash matches")
    parser.add_argument("--inspect", action="store_true", help="Only run index inspection and print diagnostics")
    args = parser.parse_args()

    if args.inspect:
        inspect_unified_index()
        return

    logger.info("Initializing CittaAI Unified Vector Database Builder...")
    success = await build_vector_database(force=args.force)

    if success:
        logger.info("\n--- Unified Index Build Successful! ---")
        inspect_unified_index()
    else:
        logger.error("Unified Index Build Failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

