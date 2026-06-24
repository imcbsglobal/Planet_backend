from rest_framework.routers import DefaultRouter
from .views import (
    BranchViewSet, SoftwareViewSet, BusinessNatureViewSet,
    DistrictViewSet, StateViewSet, CountryViewSet, SPViewSet, CorporateViewSet,
)

router = DefaultRouter()
router.register(r"branch",          BranchViewSet,          basename="branch")
router.register(r"software",        SoftwareViewSet,        basename="software")
router.register(r"business-nature", BusinessNatureViewSet,  basename="business-nature")
router.register(r"district",        DistrictViewSet,        basename="district")
router.register(r"state",           StateViewSet,           basename="state")
router.register(r"country",         CountryViewSet,         basename="country")
router.register(r"sp",              SPViewSet,              basename="sp")
router.register(r"corporate",       CorporateViewSet,       basename="corporate")

urlpatterns = router.urls