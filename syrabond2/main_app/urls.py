from django.urls import path
from syrabond2.main_app.views import SwitchesListView, switch, PremisesListView

urlpatterns = [
    path('', SwitchesListView.as_view()),
    path('switches/', SwitchesListView.as_view()),
    path('premises/', PremisesListView.as_view()),
    path('switch/<str:uid>', switch)
]