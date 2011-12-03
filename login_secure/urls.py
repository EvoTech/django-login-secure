from django.conf.urls.defaults import *

urlpatterns = patterns("login_secure.views",
    url(r'^(?P<activation_code>[^/]+)/$', 'unlock_user', name="login_secure_unlock_user"),                   
)
