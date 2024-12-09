from typing import List, Optional, Any
from typing_extensions import Annotated
from ninja import Schema, FilterSchema, ModelSchema, Field

from artists.schemas import ArtistSchema
from albums.models import Album


class AlbumSchema(ModelSchema):
    artist: ArtistSchema
    # TODO add tracks number, once Track model is defined

    class Meta:
        model = Album
        fields = ['id', 'name', 'cover', 'genre', 'year']


class AlbumSchemaIn(Schema):
    name: str
    genre: Optional[str] = Field(None)
    year: Optional[int] = Field(None)
    artist_id: int
