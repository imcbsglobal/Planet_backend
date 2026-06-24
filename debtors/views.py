import requests
import traceback
from django.http import JsonResponse
from django.views.decorators.http import require_GET

# ── Constants ─────────────────────────────────────────────────────────────────
ACC_MASTER_URL  = "https://accmaster.imcbs.com/api/sync/acc-master/"
ACC_DEPT_URL    = "https://accmaster.imcbs.com/api/sync/acc-departments/"
ACC_LEDGER_URL  = "https://accmaster.imcbs.com/api/sync/acc-ledger/"
ACC_BILLS_URL   = "https://accmaster.imcbs.com/api/sync/acc-bills/"

# Debtors module
DEBTORS_CLIENT_ID  = "GW9Q6NQQ5ONRU"
DEBTORS_SUPER_CODE = "DEBTO"

# Sysmac Info module
SYSMAC_CLIENT_ID   = "69ZHSXOIMFA6T"
SYSMAC_SUPER_CODE  = "DEBTO"

# IMC1 module
IMC1_CLIENT_ID   = "G9SYCSM54HR3Ev"
IMC1_SUPER_CODE  = "DEBTO"


# ── Shared helpers ─────────────────────────────────────────────────────────────
def _fetch_dept_map(client_id):
    """Returns {department_id: department_name} filtered by client_id."""
    dept_map = {}
    try:
        resp = requests.get(ACC_DEPT_URL, timeout=30)
        resp.raise_for_status()
        raw = resp.json()
        dept_list = raw if isinstance(raw, list) else raw.get("data", [])
        for dept in dept_list:
            if str(dept.get("client_id", "")) != client_id:
                continue
            dept_id = str(dept.get("department_id", "")).strip()
            name    = str(dept.get("department", "")).strip()
            if dept_id and name:
                dept_map[dept_id] = name
    except Exception:
        pass
    return dept_map


def _fetch_debtors_for_client(client_id, super_code, dept_map):
    """Fetches all debtor records for a given client_id/super_code, adds balance + dept name."""
    data = []
    resp = requests.get(ACC_MASTER_URL, timeout=30)
    resp.raise_for_status()
    raw = resp.json()
    records = raw if isinstance(raw, list) else raw.get("data", [])

    for item in records:
        if str(item.get("client_id", "")) != client_id:
            continue
        if str(item.get("super_code", "")) != super_code:
            continue

        item["name"]    = item.get("name", "").strip()
        debit           = float(item.get("debit")  or 0)
        credit          = float(item.get("credit") or 0)
        item["balance"] = debit - credit

        dept_id                 = str(item.get("openingdepartment", "") or "").strip()
        item["department_name"] = dept_map.get(dept_id, dept_id)
        data.append(item)

    return data


def _apply_filters_and_paginate(request, data, dept_map):
    """
    Shared filter + pagination logic.
    Returns a JsonResponse dict (without wrapping in JsonResponse yet).
    """
    query               = request.GET.get("q", "").strip()
    min_balance         = request.GET.get("min_balance", "1")
    selected_department = request.GET.get("department", "")
    selected_rows       = request.GET.get("rows", "15")
    page                = request.GET.get("page", "1")

    # Search filter
    if query:
        terms = query.lower().split()
        filtered = []
        for item in data:
            text = " ".join([
                str(item.get("code", "")),
                str(item.get("name", "")),
                str(item.get("place", "")),
                str(item.get("phone2", "")),
                str(item.get("department_name", "")),
                str(item.get("openingdepartment", "")),
            ]).lower()
            if all(t in text for t in terms):
                filtered.append(item)
        data = filtered

    # Department filter
    if selected_department:
        data = [i for i in data if i.get("openingdepartment", "") == selected_department]

    # Min balance filter
    if min_balance:
        try:
            min_val = float(min_balance)
            data = [i for i in data if float(i.get("balance") or 0) >= min_val]
        except ValueError:
            pass

    # Sort by name
    data.sort(key=lambda x: x.get("name", "").lower())

    # Totals (before pagination)
    total_balance = sum(float(i.get("balance") or 0) for i in data)
    total_debit   = sum(float(i.get("debit")   or 0) for i in data)
    total_credit  = sum(float(i.get("credit")  or 0) for i in data)

    # Pagination
    try:
        rows = int(selected_rows)
        if rows not in [10, 15, 20, 25, 50, 100, 200]:
            rows = 15
    except ValueError:
        rows = 15

    try:
        page_num = int(page)
        if page_num < 1:
            page_num = 1
    except ValueError:
        page_num = 1

    total_count = len(data)
    start = (page_num - 1) * rows
    end   = start + rows
    page_data = data[start:end]

    # Department list for dropdown
    department_list = sorted(
        [[dept_id, name] for dept_id, name in dept_map.items()],
        key=lambda x: x[1]
    )

    # Serialise only needed fields
    results = []
    for item in page_data:
        results.append({
            "code":              item.get("code", ""),
            "name":              item.get("name", ""),
            "place":             item.get("place", ""),
            "phone2":            item.get("phone2", ""),
            "opening_balance":   item.get("opening_balance", 0),
            "debit":             item.get("debit", 0),
            "credit":            item.get("credit", 0),
            "balance":           item.get("balance", 0),
            "department_name":   item.get("department_name", ""),
            "openingdepartment": item.get("openingdepartment", ""),
        })

    return {
        "results":       results,
        "departments":   department_list,
        "total_balance": round(total_balance, 2),
        "total_debit":   round(total_debit,   2),
        "total_credit":  round(total_credit,  2),
        "total_count":   total_count,
        "page":          page_num,
        "rows":          rows,
        "total_pages":   -(-total_count // rows),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Debtors module  (/debtors/…)
# ══════════════════════════════════════════════════════════════════════════════

@require_GET
def debtors1_list(request):
    """
    GET /debtors/debtors1-list/
    Query params: q, min_balance, department, rows, page
    """
    try:
        dept_map = _fetch_dept_map(DEBTORS_CLIENT_ID)
        data     = _fetch_debtors_for_client(DEBTORS_CLIENT_ID, DEBTORS_SUPER_CODE, dept_map)
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "API request timed out"}, status=504)
    except requests.exceptions.ConnectionError:
        return JsonResponse({"error": "Could not connect to API"}, status=502)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse(_apply_filters_and_paginate(request, data, dept_map))





# ══════════════════════════════════════════════════════════════════════════════
# Sysmac Info module  (/sysmac-info/…)
# ══════════════════════════════════════════════════════════════════════════════

@require_GET
def sysmac_info_list(request):
    """
    GET /sysmac-info/sysmac-info-list/
    Query params: q, min_balance, department, rows, page
    """
    try:
        dept_map = _fetch_dept_map(SYSMAC_CLIENT_ID)
        data     = _fetch_debtors_for_client(SYSMAC_CLIENT_ID, SYSMAC_SUPER_CODE, dept_map)
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "API request timed out"}, status=504)
    except requests.exceptions.ConnectionError:
        return JsonResponse({"error": "Could not connect to API"}, status=502)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse(_apply_filters_and_paginate(request, data, dept_map))



# ══════════════════════════════════════════════════════════════════════════════
# IMC1 module  (/imc1/…)
# ══════════════════════════════════════════════════════════════════════════════

@require_GET
def imc1_list(request):
    """
    GET /imc1/imc1-list/
    Query params: q, min_balance, department, rows, page
    """
    try:
        dept_map = _fetch_dept_map(IMC1_CLIENT_ID)
        data     = _fetch_debtors_for_client(IMC1_CLIENT_ID, IMC1_SUPER_CODE, dept_map)
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "API request timed out"}, status=504)
    except requests.exceptions.ConnectionError:
        return JsonResponse({"error": "Could not connect to API"}, status=502)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse(_apply_filters_and_paginate(request, data, dept_map))


# ══════════════════════════════════════════════════════════════════════════════
# Account Link Client Search  (/debtors/acc-client-search/)
# ══════════════════════════════════════════════════════════════════════════════

# All known client_ids mapped to their branch name
ACC_CLIENTS = {
    "GW9Q6NQQ5ONRU": "Sysmac Computers",
    "69ZHSXOIMFA6T": "Sysmac Info",
    "G9SYCSM54HR3Ev": "IMCB LLB",
}


@require_GET
def acc_client_search(request):
    """
    GET /debtors/acc-client-search/
    Query params:
      branch      – client_id key (e.g. GW9Q6NQQ5ONRU)
      department  – department_id to filter by (optional)
      q           – search term for client name / code (optional)
    Returns: { branches, departments, clients }
    """
    branch_id  = request.GET.get("branch", "").strip()
    dept_id    = request.GET.get("department", "").strip()
    q          = request.GET.get("q", "").strip().lower()

    # ── Branch list (static, from known clients) ──────────────────────────────
    branch_list = [{"id": k, "name": v} for k, v in ACC_CLIENTS.items()]

    if not branch_id:
        return JsonResponse({"branches": branch_list, "departments": [], "clients": []})

    # ── Department list for selected branch ───────────────────────────────────
    dept_map = {}
    try:
        resp = requests.get(ACC_DEPT_URL, timeout=30)
        resp.raise_for_status()
        raw = resp.json()
        dept_list = raw if isinstance(raw, list) else raw.get("data", [])
        for dept in dept_list:
            if str(dept.get("client_id", "")) != branch_id:
                continue
            did  = str(dept.get("department_id", "")).strip()
            name = str(dept.get("department", "")).strip()
            if did and name:
                dept_map[did] = name
    except Exception:
        pass

    departments = sorted(
        [{"id": k, "name": v} for k, v in dept_map.items()],
        key=lambda x: x["name"]
    )

    if not dept_id:
        return JsonResponse({"branches": branch_list, "departments": departments, "clients": []})

    # ── Client list for selected branch + department ──────────────────────────
    clients = []
    try:
        resp = requests.get(ACC_MASTER_URL, timeout=30)
        resp.raise_for_status()
        raw = resp.json()
        records = raw if isinstance(raw, list) else raw.get("data", [])
        for item in records:
            if str(item.get("client_id", "")) != branch_id:
                continue
            if str(item.get("openingdepartment", "")).strip() != dept_id:
                continue
            name = str(item.get("name", "")).strip()
            code = str(item.get("code", "")).strip()
            if q and q not in name.lower() and q not in code.lower():
                continue
            clients.append({"code": code, "name": name})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    clients.sort(key=lambda x: x["name"])
    return JsonResponse({"branches": branch_list, "departments": departments, "clients": clients})
