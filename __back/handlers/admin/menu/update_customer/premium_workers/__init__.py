from . import open_premium_workers_menu
from . import add_premium_worker
from . import delete_premium_worker


routers = [
    open_premium_workers_menu.router,
    add_premium_worker.router,
    delete_premium_worker.router,
]
