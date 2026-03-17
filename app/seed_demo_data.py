import logging

from app.initial_data import init

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed() -> None:
    """兼容入口，内部复用统一初始化脚本。"""
    init()


def main() -> None:
    logger.info("Seeding demo data")
    seed()
    logger.info("Demo data seeded")


if __name__ == "__main__":
    main()
