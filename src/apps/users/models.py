import hashlib

from django.contrib.auth.models import AbstractUser
from django.db import models

from pda import settings


class CustomUser(AbstractUser):
    """
    Add additional fields to the user model here.
    """

    avatar = models.FileField(upload_to="profile-pictures/", blank=True)
    language = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.email or self.username}"

    def get_display_name(self) -> str:
        if self.get_full_name().strip():
            return self.get_full_name()
        return self.email or self.username

    @property
    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar.url
        else:
            return settings.STATIC_URL + "images/user.svg"
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "avatar_url": self.avatar_url
        }
