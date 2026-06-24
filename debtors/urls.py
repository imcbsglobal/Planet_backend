from django.urls import path
from . import views

urlpatterns = [
    # ── Debtors module ────────────────────────────────────────────────────────
    path("debtors1-list/",    views.debtors1_list,   name="debtors1_list"),

    # ── Sysmac Info module ────────────────────────────────────────────────────
    path("sysmac-info-list/", views.sysmac_info_list, name="sysmac_info_list"),

    # ── IMC1 module ───────────────────────────────────────────────────────────
    path("imc1-list/",           views.imc1_list,          name="imc1_list"),

    # ── Account Link Search ───────────────────────────────────────────────────
    path("acc-client-search/",   views.acc_client_search,  name="acc_client_search"),
]