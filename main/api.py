from ninja import NinjaAPI

from users.api import router as auth_router
from artists.api import router as artists_router

api = NinjaAPI()
api.add_router('/users/', auth_router)
api.add_router('/artists/', artists_router)
