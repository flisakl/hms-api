from ninja import NinjaAPI

from users.api import router as auth_router
from artists.api import router as artists_router
from albums.api import router as albums_router
from tracks.api import router as tracks_router

api = NinjaAPI()
api.add_router('/users/', auth_router)
api.add_router('/artists/', artists_router)
api.add_router('/albums/', albums_router)
api.add_router('/tracks/', tracks_router)
