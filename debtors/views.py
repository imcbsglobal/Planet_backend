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
    'IMCB LLP':         'G9SYCSM54HR3E',
}


def _clean(value):
    """
    Normalize client_id / code values before comparing them.

    The accmaster feeds are known to carry backtick artifacts and
    inconsistent casing (same issue seen on department codes/names).
    Comparing raw strings can either drop valid ledger rows or, worse,
    let a differently-formatted-but-coincidentally-equal code slip
    through as a match for the wrong debtor. Always compare cleaned
    values on both sides.
    """
    return str(value or '').replace('`', '').strip().upper()


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


def get_sysmac_info_ledger(request):
    """
    GET /debtors/get-sysmac-info-ledger/?code=<code>

    Returns a raw list of ledger entries for a Sysmac Info debtor, filtered
    by client_id + code from the shared acc-ledgers feed. Field names match
    what LedgerContent (sysmacinfo_list.jsx) already expects: entry_date,
    voucher_no, particulars, narration, debit, credit.
    """
    CLIENT_ID = '69ZHSXOIMFA6T'   # Sysmac Info
    ledger_api_url = "https://accmaster.imcbs.com/api/sync/acc-ledgers/"

    code = _clean(request.GET.get('code', ''))
    if not code:
        return JsonResponse({'error': 'code parameter is required'}, status=400)

    try:
        response = requests.get(ledger_api_url, timeout=30)
        response.raise_for_status()
        json_data = response.json()
        raw_data = json_data if isinstance(json_data, list) else json_data.get('data', [])
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'API request timed out'}, status=502)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'Could not connect to API'}, status=502)
    except requests.exceptions.HTTPError as e:
        return JsonResponse({'error': f'HTTP Error: {e}'}, status=502)
    except Exception as e:
        return JsonResponse({'error': f'Error fetching ledger: {str(e)}'}, status=502)

    entries = []
    for item in raw_data:
        if _clean(item.get('client_id', '')) != _clean(CLIENT_ID):
            continue
        if _clean(item.get('code', '')) != code:
            continue

        entries.append({
            'entry_date':  item.get('date', '') or '',
            'voucher_no':  item.get('voucher_no', '') or '',
            'particulars': (item.get('particulars', '') or '').strip(),
            'narration':   (item.get('narration', '') or '').strip(),
            'debit':       float(item.get('debit') or 0),
            'credit':      float(item.get('credit') or 0),
        })

    entries.sort(key=lambda x: (x['entry_date'], x['voucher_no']))
    return JsonResponse(entries, safe=False)


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


def get_imc1_ledger(request):
    """
    GET /debtors/get-imc1-ledger/?code=<code>

    Returns a raw list of ledger entries for an IMCB LLP debtor, filtered
    by client_id + code from the shared acc-ledgers feed. Same entry shape
    as get_sysmac_info_ledger: entry_date, voucher_no, particulars,
    narration, debit, credit.

    NOTE: BRANCH_CLIENT_IDS['IMCB LLP'] is 'G9SYCSM54HR3E' (trailing 'v'),
    but a sample of the live ledger feed showed entries tagged
    'G9SYCSM54HR3E' (no trailing 'v'). If IMCB ledger rows come back empty,
    check the real client_id value in the ledger feed and adjust CLIENT_ID
    below to match — don't assume it's identical to imc1_list's constant.
    """
    CLIENT_ID = 'G9SYCSM54HR3E'   # IMCB LLP — verify against live ledger feed if empty
    ledger_api_url = "https://accmaster.imcbs.com/api/sync/acc-ledgers/"

    code = _clean(request.GET.get('code', ''))
    if not code:
        return JsonResponse({'error': 'code parameter is required'}, status=400)

    try:
        response = requests.get(ledger_api_url, timeout=30)
        response.raise_for_status()
        json_data = response.json()
        raw_data = json_data if isinstance(json_data, list) else json_data.get('data', [])
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'API request timed out'}, status=502)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'Could not connect to API'}, status=502)
    except requests.exceptions.HTTPError as e:
        return JsonResponse({'error': f'HTTP Error: {e}'}, status=502)
    except Exception as e:
        return JsonResponse({'error': f'Error fetching ledger: {str(e)}'}, status=502)

    entries = []
    for item in raw_data:
        if _clean(item.get('client_id', '')) != _clean(CLIENT_ID):
            continue
        if _clean(item.get('code', '')) != code:
            continue

        entries.append({
            'entry_date':  item.get('date', '') or '',
            'voucher_no':  item.get('voucher_no', '') or '',
            'particulars': (item.get('particulars', '') or '').strip(),
            'narration':   (item.get('narration', '') or '').strip(),
            'debit':       float(item.get('debit') or 0),
            'credit':      float(item.get('credit') or 0),
        })

    entries.sort(key=lambda x: (x['entry_date'], x['voucher_no']))
    return JsonResponse(entries, safe=False)


def imc1_list(request):
    CLIENT_ID = 'G9SYCSM54HR3E'
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


def get_ledger(request):
    """
    GET /debtors/get-ledger/?code=<code>

    Returns full ledger entries (raw transaction lines) for a single
    Sysmac Computers debtor, identified by their debtor `code`, pulled
    from the shared acc-ledgers feed and filtered to this client_id + code.

    Response:
        {
            code, ledger: [ { date, particulars, entry_mode, voucher_no,
                               narration, debit, credit, running_balance }, ... ],
            total_debit, total_credit, closing_balance
        }
    """
    CLIENT_ID = 'GW9Q6NQQ5ONRU'   # Sysmac Computers
    ledger_api_url = "https://accmaster.imcbs.com/api/sync/acc-ledgers/"

    code = _clean(request.GET.get('code', ''))
    if not code:
        return JsonResponse({'error': 'code parameter is required', 'ledger': []}, status=400)

    try:
        response = requests.get(ledger_api_url, timeout=30)
        response.raise_for_status()
        json_data = response.json()
        raw_data = json_data if isinstance(json_data, list) else json_data.get('data', [])
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'API request timed out', 'ledger': []}, status=502)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'Could not connect to API', 'ledger': []}, status=502)
    except requests.exceptions.HTTPError as e:
        return JsonResponse({'error': f'HTTP Error: {e}', 'ledger': []}, status=502)
    except Exception as e:
        return JsonResponse({'error': f'Error fetching ledger: {str(e)}', 'ledger': []}, status=502)

    entries = []
    for item in raw_data:
        if _clean(item.get('client_id', '')) != _clean(CLIENT_ID):
            continue
        if _clean(item.get('code', '')) != code:
            continue

        debit = float(item.get('debit') or 0)
        credit = float(item.get('credit') or 0)

        entries.append({
            'date':        item.get('date', '') or '',
            'particulars': (item.get('particulars', '') or '').strip(),
            'entry_mode':  item.get('entry_mode', '') or '',
            'voucher_no':  item.get('voucher_no', '') or '',
            'narration':   (item.get('narration', '') or '').strip(),
            'debit':       debit,
            'credit':      credit,
        })

    # Chronological order, then compute a running balance
    entries.sort(key=lambda x: (x['date'], x['voucher_no']))

    running = 0.0
    for e in entries:
        running += e['debit'] - e['credit']
        e['running_balance'] = running

    total_debit = sum(e['debit'] for e in entries)
    total_credit = sum(e['credit'] for e in entries)

    return JsonResponse({
        'code': code,
        'ledger': entries,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'closing_balance': running,
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