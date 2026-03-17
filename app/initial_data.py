import logging

from sqlmodel import Session

from app.core.db import engine, init_db, seed_sample_data
from app.seed_product_data import seed_product_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    """执行统一初始化脚本，补齐基础权限、演示组织门店及商品中心数据。"""

    with Session(engine) as session:
        init_db(session)
        seed_sample_data(session)
        seed_product_data(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
