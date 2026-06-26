import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import ClientMaster
from .serializers import ClientMasterSerializer
from master.models import Branch, Corporate, District, State, Country, Software, BusinessNature, SP

# ── Field sets used for sanitization ──────────────────────────────────────────
DATE_FIELDS   = {"installation_date", "renewal_date", "suc_end_date"}
NUMBER_FIELDS = {"no_of_seats", "software_amount", "suc_amount"}
FK_FIELDS     = {"branch", "corporate", "district", "state", "country",
                 "software", "business_nature", "service_pack"}


def _sanitize_row(row):
    """
    Convert empty strings → None for date, number, and FK fields so the
    serializer doesn't reject them with 'wrong format' / 'valid number required'.
    Also clears SUC-specific fields when type is Free or blank.
    """
    for f in DATE_FIELDS | NUMBER_FIELDS | FK_FIELDS:
        if row.get(f) == "" or row.get(f) is None:
            row[f] = None

    # Clear SUC fields when type is not SUC / Service Charge
    type_val = str(row.get("type", "")).strip()
    if type_val not in ("SUC", "Service Charge"):
        row["suc_amount"]    = None
        row["suc_end_date"]  = None
        row["payment_class"] = ""

    return row


def _build_name_map(model):
    """Return {lower_name: id} for a master model."""
    return {obj.name.strip().lower(): obj.id for obj in model.objects.all()}


def _resolve_fk_fields(row):
    """
    Convert text names → integer PKs for all FK fields.
    Returns (row, field_warnings) where field_warnings is a dict of
    {field: message} for names that couldn't be resolved (non-blocking).
    """
    FK_CONFIG = {
        "branch":          Branch,
        "corporate":       Corporate,
        "district":        District,
        "state":           State,
        "country":         Country,
        "software":        Software,
        "business_nature": BusinessNature,
        "service_pack":    SP,
    }

    field_warnings = {}

    for field, model in FK_CONFIG.items():
        raw = row.get(field)
        if raw is None:
            continue  # already null — leave as-is

        # Already an integer PK — nothing to do
        if isinstance(raw, int) or (isinstance(raw, str) and raw.isdigit()):
            row[field] = int(raw)
            continue

        if not raw:
            row[field] = None
            continue

        # Text name — resolve to PK via case-insensitive lookup
        name_map = _build_name_map(model)
        pk = name_map.get(str(raw).strip().lower())
        if pk is not None:
            row[field] = pk
        else:
            row.pop(field, None)
            field_warnings[field] = f'"{raw}" not found in {model.__name__} — field left blank.'

    return row, field_warnings


class ClientMasterViewSet(viewsets.ModelViewSet):
    queryset = ClientMaster.objects.select_related(
        "branch", "corporate", "district", "state", "country",
        "software", "business_nature", "service_pack",
    ).all()
    serializer_class   = ClientMasterSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], url_path="bulk-import",
            permission_classes=[AllowAny])
    def bulk_import(self, request):
        """
        POST /api/clientmaster/clientmaster/bulk-import/
        Accepts a JSON array of client objects and creates them in bulk.
        FK fields accept either an integer PK or a text name (resolved by lookup).
        Returns { created: N, errors: [...] }
        """
        rows = request.data
        if not isinstance(rows, list):
            return Response(
                {"detail": "Expected a JSON array of client objects."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_count = 0
        errors = []

        for idx, raw_row in enumerate(rows):
            row = dict(raw_row)           # shallow copy — don't mutate input

            # Auto-generate code if missing
            if not row.get("code"):
                row["code"] = "IMP-" + uuid.uuid4().hex[:8].upper()

            row = _sanitize_row(row)      # empty strings → None
            row, fk_warnings = _resolve_fk_fields(row)  # names → PKs

            serializer = ClientMasterSerializer(data=row)
            if serializer.is_valid():
                serializer.save()
                created_count += 1
                if fk_warnings:
                    errors.append({
                        "row":    idx + 1,
                        "code":   row.get("code", ""),
                        "name":   row.get("name", ""),
                        "errors": fk_warnings,
                        "saved":  True,
                    })
            else:
                errors.append({
                    "row":    idx + 1,
                    "code":   row.get("code", ""),
                    "name":   row.get("name", ""),
                    "errors": serializer.errors,
                    "saved":  False,
                })

        return Response(
            {"created": created_count, "errors": errors},
            status=status.HTTP_200_OK,
        )
