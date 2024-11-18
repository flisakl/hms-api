from django.db import models
from django.db import IntegrityError
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import jwt


class Manager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """

        if not email:
            raise ValueError("Email address must be provided")

        try:
            user = super()._create_user(
                username, email, password, **extra_fields
            )
            return user
        except IntegrityError:
            raise ValueError("Email address must be unique")


class User(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)
    avatar = models.ImageField(upload_to='avatars', blank=True, null=True)
    token = models.TextField(unique=True)

    objects = Manager()

    def __str__(self):
        return self.username

    def _generate_token(self):
        self.token = jwt.encode(
            {"username": self.username, "email": self.email,
             "iat": timezone.now()},
            settings.SECRET_KEY,
            algorithm="HS256"
        )

    def save(self, *args, **kwargs):
        if not self.token:
            self._generate_token()
        super().save(*args, **kwargs)
