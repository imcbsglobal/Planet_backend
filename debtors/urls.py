from django.urls import path
from . import views

urlpatterns = [
    # ── Debtors module ────────────────────────────────────────────────────────
    path("debtors1-list/",    views.debtors1_list,   name="debtors1_list"),
    path("get-ledger/",       views.get_ledger,      name="get_ledger"),

    # ── Sysmac Info module ────────────────────────────────────────────────────
    path("sysmac-info-list/",       views.sysmac_info_list,       name="sysmac_info_list"),
    path("get-sysmac-info-ledger/", views.get_sysmac_info_ledger, name="get_sysmac_info_ledger"),

    # ── IMC1 module ───────────────────────────────────────────────────────────
    path("imc1-list/",           views.imc1_list,          name="imc1_list"),
    path("get-imc1-ledger/",     views.get_imc1_ledger,    name="get_imc1_ledger"),

    # ── Account Link Search ───────────────────────────────────────────────────
    path("acc-client-search/",   views.acc_client_search,  name="acc_client_search"),
]