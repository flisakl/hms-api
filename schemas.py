from ninja import Schema, ModelSchema, FilterSchema, Field
from typing import Optional, Any, Annotated, List
from pydantic.functional_validators import AfterValidator

from artists.models import Artist
from albums.models import Album


def invert_bool(v: Any) -> bool:
    return not bool(v)


InvertedBool = Annotated[bool, AfterValidator(invert_bool)]


# BASIC SCHEMAS (they do not contain any fields from other related models)
class ArtistSchema(ModelSchema):
    class Meta:
        model = Artist
        fields = ['id', 'name', 'image']


class AlbumSchema(ModelSchema):
    class Meta:
        model = Album
        fields = ['id', 'name', 'cover', 'genre', 'year']


# COLLECTION SCHEMAS
class ArtistAlbumCount(ArtistSchema):
    album_count: Optional[int] = Field(0)


class AlbumArtist(AlbumSchema):
    artist: ArtistSchema


class AlbumTrackCount(AlbumSchema):
    # TODO add tracks number, once Track model is defined
    pass



# SINGLE RESOURCE SCHEMAS
class ArtistFull(ArtistSchema):
    albums: List[AlbumSchema] = Field([], alias='album_set')

# FILTERING SCHEMAS
class ArtistFilter(FilterSchema):
    name: Optional[str] = Field(None, q='name__icontains')
    has_image: Optional[InvertedBool] = Field(None, q="image__isnull")


class AlbumSchemaIn(Schema):
    name: str
    genre: Optional[str] = Field(None)
    year: Optional[int] = Field(None)
    artist_id: int
