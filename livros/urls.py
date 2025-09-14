from django.urls import path
from livros.views.dashboard import DashboardView
from livros.views.livros_concluidos import LivroDoneListView

app_name = "livros"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("livros_concluidos", LivroDoneListView.as_view(), name="concluidos"),
]
