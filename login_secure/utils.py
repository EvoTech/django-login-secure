import copy
import datetime
import uuid

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail, mail_admins
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from .models import LoginAttempt, BlockedUser

authenticate_orig = None

INTERVAL = getattr(settings, 'LOGIN_SECURE_INTERVAL', 3600)
LIMIT = getattr(settings, 'LOGIN_SECURE_LIMIT', 5)


def authenticate_secure(**credentials):
    """
    If the given credentials are valid, return a User object.
    """
    user = authenticate_orig(**credentials)
    user_is_blocked = False
    try:
        logging_expr = copy.copy(credentials)
        logging_expr.pop("password")
        logging_user = User.objects.get(**logging_expr)
        logging_status = bool(user)

        if BlockedUser.objects.filter(user=logging_user).count():
            user_is_blocked = True

        login = LoginAttempt()
        login.user = logging_user
        login.status = logging_status
        login.save()

        start_time = datetime.datetime.now()\
            - datetime.timedelta(seconds=INTERVAL)
        failed_attempts = LoginAttempt.objects.filter(
            user=logging_user,
            status=0,
            timestamp__range=(start_time, datetime.datetime.now())
        )
        if not user_is_blocked and not logging_status\
                and failed_attempts.count() >= LIMIT:
            blocked = BlockedUser()
            blocked.user = logging_user
            blocked.key = unicode(uuid.uuid4())
            blocked.save()

            user_is_blocked = True
            site = Site.objects.get_current().domain

            if logging_user.email:
                user_message = render_to_string(
                    'login_secure/user_message.html', {
                        'site': site,
                        'activation_code': blocked.key,
                        'user': logging_user,
                    }
                )
                send_mail(
                    _("%(site)s security system message") % {'site': site, },
                    user_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [logging_user.email, ],
                    fail_silently=True
                )

            admin_message = render_to_string(
                'login_secure/admin_message.html', {
                    'site': site,
                    'activation_code': blocked.key,
                    'user': logging_user,
                }
            )
            mail_admins(
                _("%(site)s security system message") % {'site': site, },
                admin_message,
                fail_silently=True
            )
    except:
        pass

    if user_is_blocked:
        user = None
        raise PermissionDenied(
            _("This account is currently blocked by security login system. Check your email for details.")
        )

    return user


def patch_authenticate():
    """
    Monkey-patches the urlresolvers.reverse function. Will not patch twice.
    """
    global authenticate_orig
    if auth.authenticate is not authenticate_secure:
        authenticate_orig = auth.authenticate
        auth.authenticate = authenticate_secure
