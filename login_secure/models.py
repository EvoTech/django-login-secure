from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


class LoginAttempt(models.Model):
    user = models.ForeignKey(User, related_name="has_login_attempt")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.BooleanField(db_index=True)


class BlockedUser(models.Model):
    user = models.ForeignKey(User, related_name="failed_attempt")
    date_blocked = models.DateTimeField(auto_now_add=True, db_index=True)
    key = models.CharField(_('Activation key'), max_length=255, unique=True)


from .utils import patch_authenticate
patch_authenticate()
