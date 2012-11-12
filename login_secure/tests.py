from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.core import mail, urlresolvers
from django.test import TestCase

from . import utils
from .models import LoginAttempt, BlockedUser


class LoginSecureTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            email="test@mailinator.com",
            password="testpwd"
        )

    def test_login(self):
        mail_count = len(mail.outbox)

        for i in range(utils.LIMIT - 1):
            response = self.client.login(
                username='test',
                password='not_testpwd'
            )
            self.assertFalse(response)
            self.assertEqual(len(LoginAttempt.objects.all()), i + 1)
            self.assertEqual(len(BlockedUser.objects.all()), 0)
            self.assertEqual(len(mail.outbox), mail_count)

        self.assertRaises(
            utils.PermissionDenied,
            self.client.login,
            **dict(username='test', password='not_testpwd')
        )
        self.assertEqual(len(LoginAttempt.objects.all()), utils.LIMIT)
        self.assertEqual(len(BlockedUser.objects.all()), 1)
        self.assertEqual(len(mail.outbox), mail_count + 2)

        blocked = BlockedUser.objects.all()[0]
        self.assertEqual(blocked.user, self.user)
        unlock_url = urlresolvers.reverse(
            'login_secure_unlock_user',
            kwargs={
                'activation_code': blocked.key
            }
        )
        self.assertTrue(unlock_url in mail.outbox[0].body)

        self.assertRaises(
            utils.PermissionDenied,
            self.client.login,
            **dict(username='test', password='testpwd')
        )

        response = self.client.get(unlock_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(BlockedUser.objects.all()), 0)

        response = self.client.login(username='test', password='testpwd')
        self.assertTrue(response)
