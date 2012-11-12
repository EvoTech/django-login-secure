from __future__ import absolute_import, unicode_literals
from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from .models import BlockedUser


def unlock_user(request, activation_code):
    try:
        BlockedUser.objects.get(key=activation_code).delete()
        return HttpResponseRedirect(settings.LOGIN_URL)
    except:
        raise Http404
