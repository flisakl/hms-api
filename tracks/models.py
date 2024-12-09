from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.db import models

from artists.models import Artist
from albums.models import Album


class Track(models.Model):
    file = models.FileField(upload_to='tracks')
    title = models.CharField(max_length=200)
    duration = models.DurationField()
    genre = models.CharField(max_length=50, null=True, blank=True)
    artists = models.ManyToManyField(Artist)
    number = models.IntegerField(
        default=1, validators=[MinValueValidator(1)],
        help_text=_('Track number in album')
    )
    year = models.IntegerField(_('release year'), default=1)
    album = models.ForeignKey(Album, null=True, blank=True,
                              on_delete=models.SET_NULL)
    # For singles only
    cover = models.ImageField(upload_to='tracks', null=True, blank=True)

    def __str__(self):
        return self.title
