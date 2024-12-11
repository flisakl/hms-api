from ninja import Schema, ModelSchema, FilterSchema, Field
from typing import Optional, Any, Annotated, List
from pydantic.functional_validators import AfterValidator

from artists.models import Artist
from albums.models import Album
from tracks.models import Track


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


class TrackSchema(ModelSchema):
    class Meta:
        model = Track
        fields = [
            'id', 'title', 'duration', 'genre',
            'number', 'year', 'cover', 'file'
        ]


# COLLECTION SCHEMAS
class ArtistAlbumCount(ArtistSchema):
    album_count: Optional[int] = Field(0)


class AlbumArtist(AlbumSchema):
    artist: ArtistSchema


class AlbumArtistTrackCount(AlbumArtist):
    track_count: Optional[int] = Field(0)


class TrackArtists(TrackSchema):
    artists: List[ArtistSchema] = Field([])


class TrackFull(TrackArtists):
    album: AlbumSchema = Field(None)

# SINGLE RESOURCE SCHEMAS


class ArtistFull(ArtistSchema):
    albums: List[AlbumSchema] = Field([], alias='album_set')


class AlbumFull(AlbumArtist):
    tracks: List[TrackArtists] = Field([], alias='track_set')


# FILTER SCHEMAS
class ArtistFilter(FilterSchema):
    name: Optional[str] = Field(None, q='name__icontains')
    has_image: Optional[InvertedBool] = Field(None, q="image__isnull")


class AlbumFilter(FilterSchema):
    name: Optional[str] = Field(None, q='name__icontains')
    artist_name: Optional[str] = Field(None, q='artist__name__icontains')
    artist_id: Optional[int] = Field(None, q='artist__id')
    genre: Optional[str] = Field(None, q='genre__icontains')
    year: Optional[int] = Field(None)
    has_image: Optional[InvertedBool] = Field(None, q="cover__isnull")


class TrackFilter(FilterSchema):
    title: Optional[str] = Field(None, q='title__icontains')
    genre: Optional[str] = Field(None, q='genre__icontains')
    artist: Optional[str] = Field(None, q='artists__name__icontains')
    artist_id: Optional[int] = Field(None, q='artists__id')
    year: Optional[int] = Field(None, q='year')
    year_start: Optional[int] = Field(None, q='year__gte')
    year_end: Optional[int] = Field(None, q='year__lte')
    album: Optional[str] = Field(None, q='album__name__icontains')
    album_id: Optional[int] = Field(None, q='album__id')
    has_image: Optional[InvertedBool] = Field(None, q="cover__isnull")


# INPUT SCHEMAS
class AlbumSchemaIn(Schema):
    name: str
    genre: Optional[str] = Field(None)
    year: Optional[int] = Field(None)
    artist_id: int


class TrackSchemaIn(Schema):
    # This will be comma separated list of integers
    artist_ids: Optional[str] = Field("")
    album_id: Optional[int] = Field(None)
    title: Optional[str] = Field("Unknown")
    genre: Optional[str] = Field(None)
    number: Optional[int] = Field(None)
    year: Optional[int] = Field(None)
