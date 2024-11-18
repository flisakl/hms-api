from ninja import NinjaAPI

from users import router as auth_router

api = NinjaAPI()
api.add_router('/users/', auth_router)
