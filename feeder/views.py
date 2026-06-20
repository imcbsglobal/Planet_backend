from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Feeder
from .serializers import FeederSerializer


class FeederListCreateView(APIView):
    """
    GET  /api/feeder/feeders/   → list all feeders (with optional search)
    POST /api/feeder/feeders/   → create a new feeder
    """

    def get(self, request):
        qs = Feeder.objects.all()

        # Optional search across name, software, branch, created_by
        q = request.query_params.get("search", "").strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=q)          |
                Q(software__icontains=q)      |
                Q(branch__icontains=q)        |
                Q(created_by__icontains=q)
            )

        # Optional filters
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        adm_status_filter = request.query_params.get("admStatus")
        if adm_status_filter:
            qs = qs.filter(adm_status=adm_status_filter)

        serializer = FeederSerializer(qs, many=True)
        return Response({"results": serializer.data, "count": qs.count()})

    def post(self, request):
        data = request.data.copy()
        # Set created_by safely (works with or without auth)
        if "createdBy" not in data or not data["createdBy"]:
            user = getattr(request, "user", None)
            data["createdBy"] = getattr(user, "username", "") or "Admin"

        serializer = FeederSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeederDetailView(APIView):
    """
    GET    /api/feeder/feeders/<id>/  → retrieve
    PUT    /api/feeder/feeders/<id>/  → full update
    PATCH  /api/feeder/feeders/<id>/  → partial update
    DELETE /api/feeder/feeders/<id>/  → delete
    """

    def _get_object(self, pk):
        return get_object_or_404(Feeder, pk=pk)

    def get(self, request, pk):
        feeder = self._get_object(pk)
        return Response(FeederSerializer(feeder).data)

    def put(self, request, pk):
        feeder = self._get_object(pk)
        serializer = FeederSerializer(feeder, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        feeder = self._get_object(pk)
        serializer = FeederSerializer(feeder, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        feeder = self._get_object(pk)
        feeder.delete()
        return Response({"detail": "Feeder deleted."}, status=status.HTTP_204_NO_CONTENT)