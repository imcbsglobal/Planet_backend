import requests
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse

# ── Constants ─────────────────────────────────────────────────────────────────
ACC_MASTER_URL = "https://accmaster.imcbs.com/api/sync/acc-master/"
ACC_DEPT_URL   = "https://accmaster.imcbs.com/api/sync/acc-departments/"

# Map branch name → client_id used by accmaster
BRANCH_CLIENT_IDS = {
    'Sysmac Computers': 'GW9Q6NQQ5ONRU',
    'Sysmac Info':      '69ZHSXOIMFA6T',
    'IMCB LLP':         'G9SYCSM54HR3Ev',
}


def acc_client_search(request):
    """
    Unified endpoint for the Account-Link client search UI.

    GET /debtors/acc-client-search/
        → { branches: ["Sysmac Computers", "Sysmac Info", "IMCB LLP"] }

    GET /debtors/acc-client-search/?branch=<name>
        → { departments: [{ id, name }, ...] }

    GET /debtors/acc-client-search/?branch=<name>&department=<id>&q=<search>
        → { clients: [{ code, name, place, phone2, balance, department_name }, ...] }
    """
    branch     = request.GET.get('branch',     '').strip()
    department = request.GET.get('department', '').strip()
    q          = request.GET.get('q',          '').strip().lower()

    # ── 1. No branch → return branch list ────────────────────────────────────
    if not branch:
        return JsonResponse({'branches': list(BRANCH_CLIENT_IDS.keys())})

    client_id = BRANCH_CLIENT_IDS.get(branch)
    if not client_id:
        return JsonResponse({'error': f'Unknown branch: {branch}'}, status=400)

    # ── 2. Branch only → return department list ───────────────────────────────
    if not department:
        try:
            resp = requests.get(ACC_DEPT_URL, timeout=15)
            resp.raise_for_status()
            all_depts = resp.json() if isinstance(resp.json(), list) else []
            depts = sorted(
                [
                    {'id': d['department_id'], 'name': d['department']}
                    for d in all_depts
                    if str(d.get('client_id', '')).strip().upper() == client_id.strip().upper()
                       and d.get('department_id') and d.get('department')
                ],
                key=lambda x: x['name'],
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=502)
        return JsonResponse({'departments': depts})

    # ── 3. Branch + department → return filtered client list ──────────────────
    # Build dept_map for name resolution
    dept_map = {}
    try:
        resp = requests.get(ACC_DEPT_URL, timeout=15)
        resp.raise_for_status()
        for d in (resp.json() if isinstance(resp.json(), list) else []):
            if str(d.get('client_id', '')).strip().upper() == client_id.strip().upper():
                dept_map[str(d.get('department_id', '')).strip()] = str(d.get('department', '')).strip()
    except Exception:
        pass

    try:
        resp = requests.get(ACC_MASTER_URL, timeout=30)
        resp.raise_for_status()
        raw = resp.json() if isinstance(resp.json(), list) else []
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=502)

    clients = []
    for item in raw:
        if str(item.get('client_id', '')).strip().upper() != client_id.strip().upper():
            continue
        if str(item.get('super_code', '')) != 'DEBTO':
            continue
        dept_id = str(item.get('openingdepartment', '') or '').strip()
        if dept_id != department:
            continue

        debit  = float(item.get('debit')  or 0)
        credit = float(item.get('credit') or 0)
        balance = debit - credit

        row = {
            'code':            item.get('code', ''),
            'name':            item.get('name', '').strip(),
            'place':           item.get('place', ''),
            'phone2':          item.get('phone2', ''),
            'balance':         balance,
            'department_name': dept_map.get(dept_id, dept_id),
        }

        if q:
            searchable = ' '.join([
                row['code'], row['name'], row['place'], row['phone2'],
            ]).lower()
            if q not in searchable:
                continue

        clients.append(row)

    clients.sort(key=lambda x: x['name'].lower())
    return JsonResponse({'clients': clients})


def sysmac_info_list(request):
    CLIENT_ID = '69ZHSXOIMFA6T'
    api_url = "https://accmaster.imcbs.com/api/sync/acc-master/"
    dept_url = "https://accmaster.imcbs.com/api/sync/acc-departments/"
    data = []
    error_message = None

    # ✅ Fetch department lookup: department_id → department name
    dept_map = {}
    try:
        dept_response = requests.get(dept_url, timeout=30)
        dept_response.raise_for_status()
        for dept in dept_response.json():
            if str(dept.get('client_id', '')) == CLIENT_ID:
                dept_map[str(dept['department_id'])] = dept['department']
    except Exception:
        pass

    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        raw_data = response.json()

        for item in raw_data:
            if str(item.get('client_id', '')) != CLIENT_ID:
                continue
            if str(item.get('super_code', '')) != 'DEBTO':
                continue

            item['name'] = item.get('name', '').strip()

            debit = float(item.get('debit') or 0)
            credit = float(item.get('credit') or 0)
            item['balance'] = debit - credit

            # ✅ Resolve department name from ID
            dept_id = str(item.get('openingdepartment', '') or '')
            item['openingdepartment'] = dept_id
            item['department_name'] = dept_map.get(dept_id, dept_id)

            data.append(item)

    except requests.exceptions.Timeout:
        error_message = "API request timed out"
    except requests.exceptions.ConnectionError:
        error_message = "Could not connect to API"
    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP Error: {e}"
    except Exception as e:
        error_message = f"Error fetching data: {str(e)}"

    if error_message:
        return JsonResponse({'error': error_message, 'results': [], 'departments': []}, status=502)

    # Filters
    query = request.GET.get('q', '').strip()
    min_balance = request.GET.get('min_balance', '1')
    selected_department = request.GET.get('department', '')
    selected_rows = request.GET.get('rows', '15')

    original_count = len(data)

    # ✅ Department dropdown built from dept API, as [id, name] pairs
    department_list = sorted(
        [[dept_id, name] for dept_id, name in dept_map.items()],
        key=lambda x: x[1]
    )

    # Search filter
    if query:
        search_terms = query.lower().split()
        filtered_data = []
        for item in data:
            searchable_fields = [
                str(item.get('code', '')),
                str(item.get('name', '')),
                str(item.get('place', '')),
                str(item.get('phone2', '')),
                str(item.get('opening_balance', '')),
                str(item.get('debit', '')),
                str(item.get('credit', '')),
                str(item.get('balance', '')),
                str(item.get('department_name', '')),
            ]
            combined_text = ' '.join(searchable_fields).lower()
            if all(term in combined_text for term in search_terms):
                filtered_data.append(item)
        data = filtered_data

    # Department filter (by id)
    if selected_department:
        data = [item for item in data if item.get('openingdepartment', '') == selected_department]

    # Minimum balance filter
    if min_balance:
        try:
            min_balance_value = float(min_balance)
            data = [item for item in data if float(item.get('balance') or 0) >= min_balance_value]
        except ValueError:
            pass

    # Sort and Totals
    data.sort(key=lambda x: x.get('name', '').lower())
    total_balance = sum(float(item.get('balance') or 0) for item in data)
    total_debit = sum(float(item.get('debit') or 0) for item in data)
    total_credit = sum(float(item.get('credit') or 0) for item in data)

    # Handle row count
    try:
        selected_rows_int = int(selected_rows)
        if selected_rows_int not in [10, 15, 20, 25, 50, 100, 200]:
            selected_rows_int = 15
    except ValueError:
        selected_rows_int = 15

    paginator = Paginator(data, selected_rows_int)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return JsonResponse({
        'results': list(page_obj.object_list),
        'departments': department_list,
        'total_records': original_count,
        'filtered_count': len(data),
        'total_balance': total_balance,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'current_page': page_obj.number,
        'num_pages': paginator.num_pages,
        'selected_rows': selected_rows_int,
    })


def imc1_list(request):
    CLIENT_ID = 'G9SYCSM54HR3Ev'
    api_url = "https://accmaster.imcbs.com/api/sync/acc-master/"
    dept_url = "https://accmaster.imcbs.com/api/sync/acc-departments/"
    data = []
    error_message = None

    # ✅ Fetch department lookup: department_id → department name
    dept_map = {}
    try:
        dept_response = requests.get(dept_url, timeout=30)
        dept_response.raise_for_status()
        for dept in dept_response.json():
            if str(dept.get('client_id', '')) == CLIENT_ID:
                dept_map[str(dept['department_id'])] = dept['department']
    except Exception:
        pass

    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        raw_data = response.json()

        for item in raw_data:
            if str(item.get('client_id', '')) != CLIENT_ID:
                continue
            if str(item.get('super_code', '')) != 'DEBTO':
                continue

            item['name'] = item.get('name', '').strip()

            debit = float(item.get('debit') or 0)
            credit = float(item.get('credit') or 0)
            item['balance'] = debit - credit

            # ✅ Resolve department name from ID
            dept_id = str(item.get('openingdepartment', '') or '')
            item['openingdepartment'] = dept_id
            item['department_name'] = dept_map.get(dept_id, dept_id)

            data.append(item)

    except requests.exceptions.Timeout:
        error_message = "API request timed out"
    except requests.exceptions.ConnectionError:
        error_message = "Could not connect to API"
    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP Error: {e}"
    except Exception as e:
        error_message = f"Error fetching data: {str(e)}"

    if error_message:
        return JsonResponse({'error': error_message, 'results': [], 'departments': []}, status=502)

    # Query params
    query = request.GET.get('q', '').strip()
    min_balance = request.GET.get('min_balance', '1')
    selected_department = request.GET.get('department', '').strip()
    selected_rows = request.GET.get('rows', '15')

    original_count = len(data)

    # ✅ Department dropdown built from dept API, as [id, name] pairs
    department_list = sorted(
        [[dept_id, name] for dept_id, name in dept_map.items()],
        key=lambda x: x[1]
    )

    # Filter by search
    if query:
        search_terms = query.lower().split()
        filtered_data = []
        for item in data:
            searchable_fields = [
                str(item.get('code', '')),
                str(item.get('name', '')),
                str(item.get('place', '')),
                str(item.get('phone2', '')),
                str(item.get('opening_balance', '')),
                str(item.get('debit', '')),
                str(item.get('credit', '')),
                str(item.get('balance', '')),
                str(item.get('department_name', '')),
            ]
            combined_text = ' '.join(searchable_fields).lower()
            if all(term in combined_text for term in search_terms):
                filtered_data.append(item)
        data = filtered_data

    # Filter by min balance
    if min_balance:
        try:
            min_balance_value = float(min_balance)
            data = [item for item in data if float(item.get('balance') or 0) >= min_balance_value]
        except ValueError:
            pass

    # Filter by department id
    if selected_department:
        data = [item for item in data if item.get('openingdepartment', '') == selected_department]

    data.sort(key=lambda x: x.get('name', '').lower())

    total_balance = sum(float(item.get('balance') or 0) for item in data)
    total_debit = sum(float(item.get('debit') or 0) for item in data)
    total_credit = sum(float(item.get('credit') or 0) for item in data)

    try:
        selected_rows_int = int(selected_rows)
        if selected_rows_int not in [10, 15, 20, 25, 50, 100, 200]:
            selected_rows_int = 15
    except ValueError:
        selected_rows_int = 15

    paginator = Paginator(data, selected_rows_int)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return JsonResponse({
        'results': list(page_obj.object_list),
        'departments': department_list,
        'total_records': original_count,
        'filtered_count': len(data),
        'total_balance': total_balance,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'current_page': page_obj.number,
        'num_pages': paginator.num_pages,
        'selected_rows': selected_rows_int,
    })


def debtors1_list(request):
    api_url = "https://accmaster.imcbs.com/api/sync/acc-master/"
    dept_api_url = "https://accmaster.imcbs.com/api/sync/acc-departments/"
    data = []
    error_message = None

    # Fetch department name map {department_id: department_name} filtered by client
    dept_map = {}
    try:
        dept_response = requests.get(dept_api_url, timeout=30)
        dept_response.raise_for_status()
        dept_json = dept_response.json()
        if isinstance(dept_json, list):
            dept_list = dept_json
        elif isinstance(dept_json, dict):
            dept_list = dept_json.get('data', [])
        else:
            dept_list = []
        for dept in dept_list:
            if str(dept.get('client_id', '')) != 'GW9Q6NQQ5ONRU':
                continue
            dept_id = str(dept.get('department_id', '')).strip()
            name = str(dept.get('department', '')).strip()
            if dept_id and name:
                dept_map[dept_id] = name
    except Exception:
        pass  # dept_map stays empty; codes will show as-is

    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        json_data = response.json()

        if isinstance(json_data, list):
            raw_data = json_data
        elif isinstance(json_data, dict):
            raw_data = json_data.get('data', [])
        else:
            raw_data = []
            error_message = "Unexpected JSON structure."

        for item in raw_data:
            if str(item.get('client_id', '')) != 'GW9Q6NQQ5ONRU':
                continue
            if str(item.get('super_code', '')) != 'DEBTO':
                continue
            item['name'] = item.get('name', '').strip()
            debit = float(item.get('debit') or 0)
            credit = float(item.get('credit') or 0)
            item['balance'] = debit - credit

            # Resolve department name using openingdepartment as department_id
            dept_id = str(item.get('openingdepartment', '') or '').strip()
            item['openingdepartment'] = dept_id
            item['department_name'] = dept_map.get(dept_id, dept_id)

            data.append(item)

    except requests.exceptions.Timeout:
        error_message = "API request timed out"
    except requests.exceptions.ConnectionError:
        error_message = "Could not connect to API"
    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP Error: {e}"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"

    if error_message:
        return JsonResponse({'error': error_message, 'results': [], 'departments': []}, status=502)

    query = request.GET.get('q', '').strip()
    min_balance = request.GET.get('min_balance', '1')
    selected_department = request.GET.get('department', '')
    selected_rows = request.GET.get('rows', '15')

    original_count = len(data)

    # Department dropdown: all departments for this client from dept API, sorted by name
    department_list = sorted(
        [[dept_id, name] for dept_id, name in dept_map.items()],
        key=lambda x: x[1]
    )

    # Search filter
    if query:
        search_terms = query.lower().split()
        filtered_data = []
        for item in data:
            searchable_fields = [
                str(item.get('code', '')),
                str(item.get('name', '')),
                str(item.get('super_code', '')),
                str(item.get('opening_balance', '')),
                str(item.get('debit', '')),
                str(item.get('credit', '')),
                str(item.get('balance', '')),
                str(item.get('place', '')),
                str(item.get('phone2', '')),
                str(item.get('openingdepartment', '')),
                str(item.get('department_name', '')),
            ]
            combined_text = ' '.join(searchable_fields).lower()
            if all(term in combined_text for term in search_terms):
                filtered_data.append(item)
        data = filtered_data

    # Department filter
    if selected_department:
        data = [item for item in data if item.get('openingdepartment', '') == selected_department]

    # Minimum balance filter
    if min_balance:
        try:
            min_balance_value = float(min_balance)
            data = [item for item in data if float(item.get('balance') or 0) >= min_balance_value]
        except ValueError:
            pass

    # Totals
    total_balance = sum(float(item.get('balance') or 0) for item in data)
    total_debit = sum(float(item.get('debit') or 0) for item in data)
    total_credit = sum(float(item.get('credit') or 0) for item in data)

    data.sort(key=lambda x: x.get('name', '').lower())

    # Rows per page
    try:
        selected_rows_int = int(selected_rows)
        if selected_rows_int not in [10, 15, 20, 25, 50, 100, 200]:
            selected_rows_int = 15
    except ValueError:
        selected_rows_int = 15

    paginator = Paginator(data, selected_rows_int)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return JsonResponse({
        'results': list(page_obj.object_list),
        'departments': department_list,
        'total_records': original_count,
        'filtered_count': len(data),
        'total_balance': total_balance,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'current_page': page_obj.number,
        'num_pages': paginator.num_pages,
        'selected_rows': selected_rows_int,
    })