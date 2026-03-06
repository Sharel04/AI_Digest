"""Main entry point - runs digest workflow and sends email."""

import logging
import sys

from config import Config
from agent.workflow import DigestWorkflow
from storage.memory import MemoryStore
from mailer.sender import EmailSender


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)


def main() -> int:
    try:
        config = Config()
        config.validate()
        workflow = DigestWorkflow(config)
        digest_items = workflow.run(target_items=5)
        if not digest_items:
            logger.error("No digest items generated")
            return 1
        MemoryStore(config.storage.memory_file).save_digest(digest_items)
        if EmailSender(config.email).send_digest(digest_items):
            logger.info("Digest sent successfully")
            return 0
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
