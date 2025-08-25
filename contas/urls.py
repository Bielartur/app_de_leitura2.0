from contas.views.signin import Signin
from contas.views.signup import Signup
from contas.views.user import GetUser

from django.urls import path

urlpatterns = [
    path('login', Signin.as_view()),
    path('criar_conta', Signup.as_view()),
    path('user', GetUser.as_view())
]