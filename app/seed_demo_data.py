import logging

from sqlmodel import Session

from app.core.db import engine, init_db, seed_sample_data
from app.seed_product_data import seed_product_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed() -> None:
    """显式写入演示门店、组织、角色、员工及商品中心数据。"""

    with Session(engine) as session:
        init_db(session)
        seed_sample_data(session)
        seed_product_data(session)


def main() -> None:
    logger.info("Seeding demo data")
    seed()
    logger.info("Demo data seeded")


if __name__ == "__main__":
    main()
