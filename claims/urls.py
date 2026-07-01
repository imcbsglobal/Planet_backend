from rest_framework.routers import DefaultRouter

from .views import ClaimViewSet

router = DefaultRouter()
router.register(r"claims", ClaimViewSet, basename="claims")

urlpatterns = router.urls

# Resulting endpoints:
# GET    /api/claims/             -> list (filters: ?status=&expense_type=&department=&company=&search=&ordering=)
# POST   /api/claims/             -> create   (multipart/form-data: company, department, expense_type, client, amount, description, receipt)
# GET    /api/claims/<id>/        -> retrieve
# PUT    /api/claims/<id>/        -> update
# PATCH  /api/claims/<id>/        -> partial update
# DELETE /api/claims/<id>/        -> delete
# PATCH  /api/claims/<id>/status/ -> inline status update (used by ClaimsList status dropdown)