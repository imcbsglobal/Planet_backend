from django.urls import path
from . import views

app_name = 'collection_new'

urlpatterns = [

    # ── REST API ──────────────────────────────────────────────────────────────
    # NOTE: specific paths must come before parameterised ones
    path('collections/',
         views.api_collection_list,
         name='api_collection_list'),

    path('collections/add/',
         views.api_collection_add,
         name='api_collection_add'),

    path('collections/toggle-status/<int:pk>/',
         views.api_collection_toggle_status,
         name='api_collection_toggle_status'),

    path('collections/<int:pk>/',
         views.api_collection_detail,
         name='api_collection_detail'),

    # ── Proxy endpoints ───────────────────────────────────────────────────────
    path('proxy/clients/',
         views.acc_master_proxy,
         name='acc_master_proxy'),

    path('proxy/departments/',
         views.acc_departments_proxy,
         name='acc_departments_proxy'),
]
