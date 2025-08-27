from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from contas.forms import LoginForm

class RememberLoginView(LoginView):
    form_class = LoginForm
    redirect_authenticated_user = True  # opcional, evita re-login se já estiver logado

    def form_valid(self, form):
        response = super().form_valid(form)
        remember = form.cleaned_data.get("remember_me")
        if remember:
            # exemplo: 30 dias
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            # expira ao fechar o navegador
            self.request.session.set_expiry(0)
        return response
