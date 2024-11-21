from ninja import Schema, ModelSchema

from .models import Artist


class ArtistSchema(ModelSchema):
    class Meta:
        model = Artist
        fields = ['id', 'name', 'image']
