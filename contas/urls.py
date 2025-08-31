from django.urls import path, reverse_lazy
from contas.views.editar_perfil import EditarPerfil
from contas.views.criar_conta import CriarConta
from contas.views.login import RememberLoginView
from django.contrib.auth import views as auth_view
app_name = "contas"

urlpatterns = [
    path("login/", RememberLoginView.as_view(template_name="login.html"), name="login"),
    path('logout/',auth_view.LogoutView.as_view(next_page=reverse_lazy('contas:login')), name="logout"),
    path('editar_perfil/<int:pk>', EditarPerfil.as_view(), name="editar_perfil"),
    path('criar_conta/', CriarConta.as_view(), name="criar_conta"),
    path('redefinir_senha/', auth_view.PasswordChangeView.as_view(template_name='editarperfil.html', success_url=reverse_lazy('livros:index')), name="redefinir_senha"),
]