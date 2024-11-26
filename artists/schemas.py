from ninja import Schema, ModelSchema, FilterSchema, Field
from typing import Optional, Any, Annotated
from pydantic.functional_validators import AfterValidator

from .models import Artist


def invert_bool(v: Any) -> bool:
    return not bool(v)


InvertedBool = Annotated[bool, AfterValidator(invert_bool)]


class ArtistSchema(ModelSchema):
    class Meta:
        model = Artist
        fields = ['id', 'name', 'image']


class ArtistFilter(FilterSchema):
    name: Optional[str] = Field(None, q='name__icontains')
    has_image: Optional[InvertedBool] = Field(None, q="image__isnull")


class ArtistAndAlbumsSchema(ArtistSchema):
    # TODO: add albums field, once Album model is added
    # albums: List[AlbumSchema] = Field([], alias='album_set')
    pass
