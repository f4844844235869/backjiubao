from fastapi import APIRouter

from app.api.routes import users
from app.modules.auth.router import router as auth_router
from app.modules.employee.router import router as employee_router
from app.modules.iam.router import router as iam_router
from app.modules.inventory.router import router as inventory_router
from app.modules.notification.router import router as notification_router
from app.modules.org.router import router as org_router
from app.modules.pos.router import router as pos_router
from app.modules.product.router import router as product_router
from app.modules.store.router import router as store_router
from app.modules.wallet.router import router as wallet_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users.router)
api_router.include_router(employee_router)
api_router.include_router(store_router)
api_router.include_router(org_router)
api_router.include_router(iam_router)
api_router.include_router(notification_router)
api_router.include_router(product_router)
api_router.include_router(wallet_router)
api_router.include_router(pos_router)
api_router.include_router(inventory_router)
