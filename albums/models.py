from django.db import models
from django.core.validators import MinValueValidator
from artists.models import Artist


year_validators = [MinValueValidator(limit_value=0)]

class Album(models.Model):
    name = models.CharField(max_length=200)
    cover = models.ImageField(upload_to='albums', null=True, blank=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    genre = models.CharField(max_length=50, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True, validators=year_validators)

    class Meta:
        constraints = [
            models.constraints.UniqueConstraint(
                fields=['artist_id', 'name'], name='unique_artist_album'
            )
        ]
