#!/usr/bin/env python3
"""Dựng dailysale_v9.json cho dashboard-kinhdoanh/dailysale.html.

Nguồn (project rural-data-analystic):
  - sales.sql   : daily_sale_new_report (asia-southeast1) — doanh thu, bill, target, hủy, shrink, tồn kho
  - Thuộc tính CH: ưu tiên Google Sheet "Storelist Rural" › Storeslist (bản mới nhất) qua --profile;
                  nếu không truyền --profile thì dùng profile.sql (admin_hr.store_profile_20261103, bản chụp 03/11)
Hai dataset khác vùng nên chạy 2 truy vấn rồi ghép ở đây.

Chạy (máy đã đăng nhập gcloud/bq):
    python3 tools/dailysale/build.py                 # chạy bq, ghi ./dailysale_v9.json
    python3 tools/dailysale/build.py --sales s.json --profile p.json   # dùng file có sẵn (bq --format=json)

Quy tắc:
  - Ngày báo cáo = ngày gần nhất có doanh thu (D-1).
  - WTD = Thứ 2 → D-1. LY ngày/tuần lùi 364 ngày (cùng thứ); LY tháng/năm cùng ngày lịch năm trước.
  - SPD kỳ = doanh thu kỳ / số ngày có bán của CH trong kỳ. Bill/ngày tương tự. Basket = DT*1000/bill (nghìn đ).
  - Nhóm CH theo ngày khai trương (Y = năm của D, M = tháng của D):
      LFL < Y-1 · STU = Y-1 · NSO1 = tháng M · NSO2 = tháng M-1 · NSO = các tháng còn lại của năm Y.
      SKT = khai trương sau ngày báo cáo · KHAC = không có ngày khai trương.
  - Tỉnh dùng tên tỉnh cũ (trước 1/7). Vùng Bắc Trung Bộ luôn thuộc Miền Trung.
  - Hủy/Shrink = lũy kế tháng. DIO = tồn kho / giá vốn bình quân ngày 30 ngày.
"""
import argparse, json, os, subprocess, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = 'rural-data-analystic'


def bq(sql_file):
    sql = open(os.path.join(HERE, sql_file), encoding='utf-8').read()
    out = subprocess.run(['bq', f'--project_id={PROJECT}', 'query', '--use_legacy_sql=false',
                          '--format=json', '--max_rows=100000', '--quiet'],
                         input=sql, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def f(v):
    try:
        return float(v) if v not in (None, '') else 0.0
    except (TypeError, ValueError):
        return 0.0


def div(a, b, k=1.0):
    return a * k / b if b else None


def rnd(v, n):
    return None if v is None else round(v, n)


def group(kt, D):
    if not kt:
        return 'KHAC'
    k = dt.date.fromisoformat(kt[:10])
    if k > D:
        return 'SKT'   # chưa khai trương tại ngày báo cáo
    if k.year < D.year - 1:
        return 'LFL'
    if k.year == D.year - 1:
        return 'STU'
    if (k.year, k.month) == (D.year, D.month):
        return 'NSO1'
    pm = (D.year, D.month - 1) if D.month > 1 else (D.year - 1, 12)
    if (k.year, k.month) == pm:
        return 'NSO2'
    return 'NSO'


def buckets(D):
    """12 kỳ: 6 tháng (M-5..M) rồi 6 tuần (W-5..W) — khớp hist.sql."""
    out = []
    for i in range(6):
        y, m = D.year, D.month - (5 - i)
        while m <= 0:
            y, m = y - 1, m + 12
        b0 = dt.date(y, m, 1)
        nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
        full = (nxt - b0).days
        b1 = min(nxt - dt.timedelta(days=1), D)
        out.append({'t': 'M', 'lb': f'T{m}' + (f'/{y % 100}' if m == 12 or i == 0 else ''), 'b0': b0.isoformat(),
                    'b1': b1.isoformat(), 'nd': (b1 - b0).days + 1, 'full': full})
    W0 = D - dt.timedelta(days=D.weekday())
    for i in range(6):
        b0 = W0 - dt.timedelta(days=7 * (5 - i))
        b1 = min(b0 + dt.timedelta(days=6), D)
        out.append({'t': 'W', 'lb': f'{b0.day:02d}/{b0.month:02d}', 'b0': b0.isoformat(), 'b1': b1.isoformat(),
                    'nd': (b1 - b0).days + 1, 'full': 7})
    return out


def build(sales, profile, src='admin_hr.store_profile_20261103', hist=None, be=None):
    S = {r['store']: r for r in sales}
    HI = {h['store']: h for h in (hist or [])}
    BE = {str(b['store']).strip(): f(b['be']) for b in (be or []) if f(b.get('be')) > 0}
    rd = next((r['rd'] for r in sales if r.get('rd')), None)
    rdl = next((r['rdl'] for r in sales if r.get('rdl')), None)
    D = dt.date.fromisoformat(rd)
    W0 = D - dt.timedelta(days=D.weekday())
    stores, missing = [], []
    for p in profile:
        sap = str(p['sap']).strip()
        s = S.get(sap, {})
        g = lambda k: f(s.get(k))
        tt = (p.get('tt') or '').strip()
        if tt.lower() == 'đang hoạt động':
            tt = 'Đang hoạt động'
        kt = p.get('kt') or None
        # CH đã khai trương sau ngày chụp danh sách: có doanh thu D-1 → coi là đang hoạt động
        if tt.startswith('Sắp khai trương') and kt and kt[:10] <= rd and g('d_s') > 0:
            tt = 'Đang hoạt động'
        gr = group(kt, D)
        mi = p.get('mi') or ''
        if (p.get('vu') or '') == 'Bắc Trung Bộ':
            mi = 'Miền Trung'   # quy ước: vùng Bắc Trung Bộ thuộc Miền Trung
        r = {
            'sap': sap, 'nm': p.get('nm') or '', 'mi': mi, 'vu': p.get('vu') or '',
            'ti': p.get('ti') or '', 'qu': p.get('qu') or '', 'gd': p.get('gd') or '', 'ql': p.get('ql') or '',
            'gr': gr, 'nh': gr, 'tt': tt, 'kt': kt, 'ky': int(kt[:4]) if kt else None,
            'lo': rnd(g('lo'), 2), 'sh': rnd(g('sh'), 2), 'st': rnd(g('st'), 2),
            'dio': rnd(div(g('st'), g('cg')), 1), 'dth': '',
        }
        for suf, rv in (('', '_s'), ('r', '_r')):
            # ngày
            r['d' + suf] = rnd(g('d' + rv), 2)
            r['dl' + suf] = rnd(g('dl' + rv), 2)
            r['bs' + suf] = rnd(div(g('d' + rv), g('d_b'), 1000), 1)
            r['dbs' + suf] = rnd(div(g('dl' + rv), g('dl_b'), 1000), 1)
            # tuần / tháng / năm: SPD = DT / số ngày có bán
            for per, cy, ly in (('w', 'w', 'wl'), ('m', 'm', 'ml'), ('y', 'y', 'yl')):
                spd, spdl = div(g(cy + rv), g(cy + '_n')), div(g(ly + rv), g(ly + '_n'))
                bsz, bszl = div(g(cy + rv), g(cy + '_b'), 1000), div(g(ly + rv), g(ly + '_b'), 1000)
                if per == 'w':
                    r['w' + suf], r['wl' + suf] = rnd(spd, 2), rnd(spdl, 2)
                    r['wbs' + suf], r['wbsl' + suf] = rnd(bsz, 1), rnd(bszl, 1)
                else:
                    r[per + suf], r[per + 'l' + suf] = rnd(g(cy + rv), 2), rnd(g(ly + rv), 2)
                    r[per + 'd' + suf], r[per + 'dl' + suf] = rnd(spd, 2), rnd(spdl, 2)
                    r[per + 'bs' + suf], r[per + 'bsl' + suf] = rnd(bsz, 1), rnd(bszl, 1)
        # bill (không phụ thuộc loại doanh thu)
        r['bl'], r['dbl'] = int(g('d_b')), int(g('dl_b'))
        r['wbl'], r['wbll'] = rnd(div(g('w_b'), g('w_n')), 1), rnd(div(g('wl_b'), g('wl_n')), 1)
        r['mb'], r['mbl'] = rnd(div(g('m_b'), g('m_n')), 1), rnd(div(g('ml_b'), g('ml_n')), 1)
        r['ybl'], r['ybll'] = rnd(div(g('y_b'), g('y_n')), 1), rnd(div(g('yl_b'), g('yl_n')), 1)
        # target (dùng chung cho SO và Retail)
        r['dt'] = rnd(g('dt'), 2)
        # target tuần: cộng target từng ngày T2→D (nếu đầu tuần rơi vào tháng trước thì quy đổi theo target ngày)
        r['wt'] = rnd(g('wt') if (W0.month == D.month) else g('dt') * ((D - W0).days + 1), 2)
        r['mt'] = rnd(g('mt'), 2)
        r['yt'] = rnd(g('ty') + g('mt'), 2)
        # KPI bổ sung: điểm hòa vốn, tháng trước (LM), S&L&C (shrink - loss + coupon)
        h = HI.get(sap)
        if BE.get(sap):
            r['be'] = BE[sap]
        if h:
            r['lmr'], r['lmn'] = rnd(h['rv'][4], 2), h['dn'][4]
            r['slc'], r['slcl'] = rnd(h['sl'][5], 2), rnd(h['sll'][5], 2)
            r['slcm'] = rnd(h['sl'][4], 2)
        # rút gọn: bỏ trường Retail trùng SO (trang tự lấy SO khi thiếu) và ô trống
        for k in [k for k in r if k.endswith('r') and k[:-1] in r and r[k] == r[k[:-1]] and k not in ('qu',)]:
            del r[k]
        r = {k: v for k, v in r.items() if v is not None and v != ''}
        stores.append(r)
    psap = {str(p['sap']).strip() for p in profile}
    missing = sorted(k for k, v in S.items() if k not in psap and f(v.get('m_s')) > 0)
    month_days = (dt.date(D.year + (D.month == 12), D.month % 12 + 1, 1) - dt.timedelta(days=1)).day
    meta = {
        'reportDate': rd, 'lyDay': rdl, 'n': len(stores),
        'mtdDays': D.day, 'daysInMonth': month_days,
        'wtdDays': (D - W0).days + 1, 'ytdDays': D.timetuple().tm_yday,
        'basis': 'Revenue',
        'src': 'BQ daily_sale_new_report + ' + src,
        'builtAt': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'salesNotInProfile': missing,
    }
    out = {'meta': meta, 'stores': stores}
    if hist:
        bk = buckets(D)
        keep = {r['sap'] for r in stores}
        out['hist'] = {'bk': bk, 'f': ['rv', 'dn', 'rvl', 'dnl', 'sl', 'sll'],
                       's': {h['store']: [[round(f(v), 1) if k in ('rv', 'rvl', 'sl', 'sll') else int(f(v)) for v in h[k]]
                                          for k in ('rv', 'dn', 'rvl', 'dnl', 'sl', 'sll')]
                             for h in hist if h['store'] in keep}}
    return out


def load_profile(path):
    """Nhận JSON từ bq (profile.sql) hoặc JSON xuất từ Google Sheet 'Storelist Rural' › Storeslist
    dạng {"values": [...]} với các cột A:J, P (Phân vùng), AF (QLKV), AJ (GĐV) — cột theo vị trí."""
    j = json.load(open(path, encoding='utf-8'))
    if isinstance(j, list):
        return j
    V = j['values']
    H = V[0]
    ix = {name: H.index(name) for name in H}
    def col(r, name):
        i = ix.get(name)
        return (r[i].strip() if i is not None and i < len(r) else '')
    out = []
    for r in V[1:]:
        sap = col(r, 'Mã SAP')
        if not sap:
            continue
        kt = col(r, 'Khai Trương')
        try:
            kt = (dt.date(1899, 12, 30) + dt.timedelta(days=int(float(kt)))).isoformat()
        except ValueError:
            try:
                kt = dt.datetime.strptime(kt, '%d/%m/%Y').date().isoformat()
            except ValueError:
                kt = None
        out.append({'sap': sap, 'nm': col(r, 'Tên cửa hàng'), 'tt': col(r, 'Tình Trạng'), 'kt': kt,
                    'mi': col(r, 'Miền'), 'ti': col(r, 'Tỉnh/TP cũ trước 1/7'), 'qu': col(r, 'Quận/ huyện cũ trước 1/7'),
                    'vu': col(r, 'Phân vùng'), 'ql': col(r, 'QLKV'), 'gd': col(r, 'GĐV')})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sales')
    ap.add_argument('--profile')
    ap.add_argument('--hist')
    ap.add_argument('--be')
    ap.add_argument('--out', default='dailysale_v9.json')
    a = ap.parse_args()
    sales = json.load(open(a.sales, encoding='utf-8')) if a.sales else bq('sales.sql')
    profile = load_profile(a.profile) if a.profile else bq('profile.sql')
    hist = json.load(open(a.hist, encoding='utf-8')) if a.hist else bq('hist.sql')
    be = json.load(open(a.be, encoding='utf-8')) if a.be else bq('be.sql')
    j = build(sales, profile, 'Storelist Rural (Storeslist)' if a.profile else 'admin_hr.store_profile_20261103', hist, be)
    hpart = j.pop('hist', None)
    if hpart:
        hp = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'dailysale_hist.json')
        with open(hp, 'w', encoding='utf-8') as fh:
            json.dump(hpart, fh, ensure_ascii=False, separators=(',', ':'))
    with open(a.out, 'w', encoding='utf-8') as fh:
        json.dump(j, fh, ensure_ascii=False, separators=(',', ':'))
    m = j['meta']
    print(f"OK {a.out}: {m['n']} CH · ngày {m['reportDate']} · WTD {m['wtdDays']} · MTD {m['mtdDays']}"
          f" · sale không có trong danh sách CH: {len(m['salesNotInProfile'])}", file=sys.stderr)


if __name__ == '__main__':
    main()
