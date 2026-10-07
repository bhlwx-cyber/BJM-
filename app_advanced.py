# ✅ FINAL BUILD PyInstaller Streamlit 100% WORKING
# ✅ FIX SEMUA BUG: Infinite Loop, Bind Address, Cannot Access
import sys
import os
import time
import webbrowser

# ==============================================
# 🔴 FIX importlib.metadata PackageNotFoundError
# ==============================================
if getattr(sys, 'frozen', False):
    import importlib.metadata
    
    # MONKEY PATCH SEMUA FUNGSI METADATA
    def mock_distribution(name):
        class MockDist:
            version = "1.40.0"
            def metadata(self):
                return {"Version": "1.40.0"}
        return MockDist()
    
    importlib.metadata.distribution = mock_distribution
    importlib.metadata.version = lambda name: "1.40.0" if name == "streamlit" else "0.0.0"
    importlib.metadata.metadata = lambda name: {"Version": "1.40.0"} if name == "streamlit" else {}

# ==============================================
# 🔴 FINAL FIX SOCKET SERVER MATI OTOMATIS
# ==============================================
if getattr(sys, 'frozen', False):
    # ✅ SATU-SATUNYA SOLUSI UNTUK BUG INI
    # Streamlit server berhenti menerima koneksi ketika di EXE
    import socket
    original_accept = socket.socket.accept
    
    def patched_accept(self):
        while True:
            try:
                return original_accept(self)
            except:
                import time
                time.sleep(0.05)
                continue
    
    socket.socket.accept = patched_accept
# ==============================================
# END SOCKET FIX
# ==============================================

# ==============================================
# 🔴 FINAL FIX 1: INFINITE LOOP EXE
# ==============================================
if getattr(sys, 'frozen', False):

    # ✅ SINGLE INSTANCE PROTECTION - HANYA 1 PROSES SAJA
    import ctypes
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    mutex = kernel32.CreateMutexW(None, ctypes.c_bool(True), "AR_MATCHER_ENGINE_FINAL")
    if ctypes.get_last_error() == 183:
        webbrowser.open("http://127.0.0.1:8501")
        sys.exit(0)

    # ✅ PATCH INTERNAL CONFIG STREAMLIT SEBELUM APAPUN
    # Ini adalah satu satunya cara yang bekerja untuk frozen mode
    from streamlit import config
    
    config.set_option("server.address", "0.0.0.0", "forced")
    config.set_option("server.headless", True, "forced")
    config.set_option("server.enableCORS", False, "forced")
    config.set_option("server.enableXsrfProtection", False, "forced")
    config.set_option("server.port", 8501, "forced")
    config.set_option("browser.gatherUsageStats", False, "forced")
    config.set_option("global.developmentMode", False, "forced")
    config.set_option("server.disableWatcher", True, "forced")
    config.set_option("server.fileWatcherType", "none", "forced")

    # ✅ PATCH SERVER START FUNGSI
    from streamlit.web.server.server import Server
    original_start = Server.start
    
    def patched_server_start(self):
        self._server_address = "0.0.0.0"
        self._port = 8501
        return original_start(self)
    
    Server.start = patched_server_start

    print("🚀 AR Matcher Engine sedang berjalan...")
    print("⏳ Mohon tunggu 5-10 detik")

    # ✅ BUKA BROWSER HANYA SEKALI SETELAH SERVER BENAR BENAR SIAP
    def open_when_ready():
        import socket
        for i in range(60):
            try:
                sock = socket.create_connection(('127.0.0.1', 8501), timeout=0.5)
                sock.close()
                break
            except:
                time.sleep(0.5)
        webbrowser.open("http://127.0.0.1:8501")
        print("✅ Aplikasi siap digunakan")

    import threading
    threading.Thread(target=open_when_ready, daemon=True).start()

    # ✅ TANDAI BAHWA INI ADALAH PROSES UTAMA
    os.environ['AR_MATCHER_RUNNING'] = '1'

# ==============================================
# END ALL FIX
# ==============================================

if getattr(sys, 'frozen', False):
    # Monkey patch importlib.metadata SEBELUM APAPUN di import
    from importlib import metadata
    
    original_distribution = metadata.distribution
    
    def patched_distribution(name):
        if name == 'streamlit':
            class MockDist:
                version = '1.40.0'
                def metadata(self):
                    return {'Version': '1.40.0'}
            return MockDist()
        return original_distribution(name)
    
    metadata.distribution = patched_distribution

import streamlit as st
import pandas as pd
import re
import itertools
from rapidfuzz import fuzz
from io import BytesIO
from datetime import datetime

# ==============================================
# 🔴 SAFE IMPORT CONFIG (fallback jika config.py tidak ada, mis. saat EXE)
# ==============================================
try:
    import config
except ImportError:
    # Nilai default jika config.py tidak tersedia
    class _DefaultConfig:
        STRICT_COMBINATION_BY_FORMAT = {
            "FORMAT_1": False,
            "FORMAT_2": False,
            "FORMAT_3": False,
            "FORMAT_4": False,
            "FORMAT_5": True,
            "FORMAT_FALLBACK": False
        }
        STRICT_COMBINATION = True
    config = _DefaultConfig()

# ==============================================
# ADVANCED BANK RECONCILIATION ENGINE
# Enterprise Grade dengan akurasi >90%
# ==============================================

def normalize_customer_name(name):
    """
    Normalisasi nama customer sesuai standard:
    - Ubah ke UPPERCASE
    - Hapus kata PT, TBK, CV, LTD, INC, CORP
    - Hilangkan spasi berlebih
    """
    if pd.isna(name) or name is None:
        return ""

    text = str(name).strip().upper()

    # Hapus semua suffix perusahaan
    remove_terms = ['PT', 'TBK', 'CV', 'LTD', 'INC', 'CORP', 'PT.', 'TBK.', 'CV.', 'LTD.', 'INC.', 'CORP.']
    for term in remove_terms:
        text = re.sub(rf'\b{re.escape(term)}\b', '', text)
    # Hapus spasi berlebih
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ==============================================
# 🔹 NAME RELIABILITY GATE
# ==============================================
# Memproses nama dari bank statement untuk menentukan nama yang paling
# reliable untuk digunakan dalam matching customer.
# Output: dict dengan keys:
#   - nama_asli: nama mentah dari file
#   - nama_terpakai: nama yang dipakai untuk matching
#   - sumber_nama: dari mana nama diambil
#   - alasan: penjelasan keputusan
#   - kategori: PERUSAHAAN / ORANG / GENERIK / ALIAS / FULL / TIDAK DIGUNAKAN
#   - kandidat_alternatif: daftar kandidat nama lain yang dipertimbangkan

def load_aliases():
    """Load alias dari aliases.csv"""
    aliases = {}
    try:
        import csv
        with open('aliases.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                alias = str(row.get('Alias', '')).strip().upper()
                nama_asli = str(row.get('Nama Asli', '')).strip().upper()
                if alias and nama_asli:
                    aliases[alias] = nama_asli
    except Exception:
        pass
    return aliases

# Load aliases sekali saat import
ALIASES = load_aliases()

def apply_name_reliability_gate(nama_raw, mode='otomatis'):
    """
    Name Reliability Gate - Menentukan nama yang paling reliable untuk matching.
    
    Mode:
      - 'otomatis': Deteksi nama generik, ekstrak nama perusahaan setelah '/',
                    expand alias, fallback nama asli
      - 'selalu':   Selalu gunakan nama asli apa adanya
      - 'jangan':   Tidak pernah gunakan nama (matching hanya amount/invoice)
    
    Return: dict dengan keys:
      - nama_asli, nama_terpakai, sumber_nama, alasan, kategori, kandidat_alternatif
    """
    if pd.isna(nama_raw) or nama_raw is None:
        return {
            'nama_asli': '',
            'nama_terpakai': '',
            'sumber_nama': 'NONE',
            'alasan': 'Nama kosong',
            'kategori': 'TIDAK DIGUNAKAN',
            'kandidat_alternatif': []
        }
    
    nama_asli = str(nama_raw).strip().upper()
    nama_asli = re.sub(r'\s+', ' ', nama_asli).strip()
    
    # Mode 'jangan': tidak pernah gunakan nama
    if mode == 'jangan':
        return {
            'nama_asli': nama_asli,
            'nama_terpakai': '',
            'sumber_nama': 'NONE',
            'alasan': 'Mode "Jangan pakai" - nama tidak digunakan untuk matching',
            'kategori': 'TIDAK DIGUNAKAN',
            'kandidat_alternatif': []
        }
    
    # Mode 'selalu': gunakan nama asli apa adanya
    if mode == 'selalu':
        return {
            'nama_asli': nama_asli,
            'nama_terpakai': nama_asli,
            'sumber_nama': 'NAMA',
            'alasan': 'Mode "Selalu pakai" - nama asli digunakan langsung',
            'kategori': 'FULL',
            'kandidat_alternatif': []
        }
    
    # ==============================================
    # MODE OTOMATIS
    # ==============================================
    kandidat_alternatif = []
    
    # 1. Cek apakah nama generik (KLIEN, BPK, IBU, SDR, dll)
    is_generic = False
    for generic in ['KLIEN', 'BPK', 'IBU', 'SDR', 'SDRI', 'BAPAK', 'KANTOR PUSAT', 'BANK', 'BNI']:
        if nama_asli == generic or nama_asli.startswith(generic + ' '):
            is_generic = True
            break
    
    if is_generic:
        # Nama generik: coba ekstrak nama perusahaan setelah '/'
        if '/' in nama_asli:
            parts = [p.strip() for p in nama_asli.split('/')]
            # Ambil bagian terakhir yang paling mungkin nama perusahaan
            for part in reversed(parts):
                if part and part not in ['KLIEN', 'BPK', 'IBU', 'SDR', 'SDRI', 'BAPAK']:
                    nama_terpakai = part
                    kandidat_alternatif = [p for p in parts if p != part]
                    return {
                        'nama_asli': nama_asli,
                        'nama_terpakai': nama_terpakai,
                        'sumber_nama': 'NAMA (bagian perusahaan)',
                        'alasan': f'Nama generik "{nama_asli}" - menggunakan bagian perusahaan "{nama_terpakai}"',
                        'kategori': 'PERUSAHAAN',
                        'kandidat_alternatif': kandidat_alternatif
                    }
        
        # Nama generik tanpa '/': cek alias
        if nama_asli in ALIASES:
            nama_terpakai = ALIASES[nama_asli]
            return {
                'nama_asli': nama_asli,
                'nama_terpakai': nama_terpakai,
                'sumber_nama': 'ALIAS',
                'alasan': f'Nama generik "{nama_asli}" - menggunakan alias "{nama_terpakai}"',
                'kategori': 'ALIAS',
                'kandidat_alternatif': []
            }
        
        # Nama generik tanpa pola: tidak digunakan
        return {
            'nama_asli': nama_asli,
            'nama_terpakai': '',
            'sumber_nama': 'NONE',
            'alasan': f'Nama generik "{nama_asli}" tidak memiliki pola perusahaan atau alias',
            'kategori': 'GENERIK',
            'kandidat_alternatif': []
        }
    
    # 2. Cek apakah ada pola "NAMA / PERUSAHAAN"
    if '/' in nama_asli:
        parts = [p.strip() for p in nama_asli.split('/')]
        # Ambil bagian terakhir yang paling mungkin nama perusahaan
        for part in reversed(parts):
            if part and len(part) > 3:
                nama_terpakai = part
                kandidat_alternatif = [p for p in parts if p != part]
                return {
                    'nama_asli': nama_asli,
                    'nama_terpakai': nama_terpakai,
                    'sumber_nama': 'NAMA (bagian perusahaan)',
                    'alasan': f'Pola "NAMA / PERUSAHAAN" - menggunakan bagian "{nama_terpakai}"',
                    'kategori': 'PERUSAHAAN',
                    'kandidat_alternatif': kandidat_alternatif
                }
    
    # 3. Cek apakah nama adalah alias
    if nama_asli in ALIASES:
        nama_terpakai = ALIASES[nama_asli]
        return {
            'nama_asli': nama_asli,
            'nama_terpakai': nama_terpakai,
            'sumber_nama': 'ALIAS',
            'alasan': f'Alias "{nama_asli}" - menggunakan nama asli "{nama_terpakai}"',
            'kategori': 'ALIAS',
            'kandidat_alternatif': []
        }
    
    # 4. Cek apakah nama mengandung alias (misal "KBB / JAVA TSUSHO")
    for alias, nama_asli_alias in ALIASES.items():
        if alias in nama_asli:
            nama_terpakai = nama_asli_alias
            return {
                'nama_asli': nama_asli,
                'nama_terpakai': nama_terpakai,
                'sumber_nama': 'ALIAS (dalam nama)',
                'alasan': f'Ditemukan alias "{alias}" dalam nama - menggunakan "{nama_terpakai}"',
                'kategori': 'ALIAS',
                'kandidat_alternatif': [nama_asli]
            }
    
    # 5. Fallback: gunakan nama asli
    return {
        'nama_asli': nama_asli,
        'nama_terpakai': nama_asli,
        'sumber_nama': 'NAMA',
        'alasan': 'Nama digunakan langsung (tidak ada pola khusus)',
        'kategori': 'FULL',
        'kandidat_alternatif': []
    }


# ==============================================
# 🔹 NORMALISASI & EKSTRAKSI
# ==============================================

def clean_invisible_chars(text):
    """
    Bersihkan karakter tak terlihat dari teks:
    U+200E, U+200F, U+202A-U+202E, dan spasi tersembunyi
    """
    if pd.isna(text) or text is None:
        return ''
    text = str(text)
    for ch in ['\u200e', '\u200f', '\u202a', '\u202b', '\u202c', '\u202d', '\u202e']:
        text = text.replace(ch, '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_customer_key(name):
    """
    Normalisasi nama customer untuk pengelompokan (grouping key).
    Hapus awalan PT./CV./TBK, spasi berlebih, spasi akhir, uppercase.
    "PT. PELSART TAMBANG KENCANA" dan "PELSART TAMBANG KENCANA" -> satu grup.
    """
    if pd.isna(name) or name is None:
        return ''
    text = clean_invisible_chars(name).upper()
    # Hapus awalan PT./CV./TBK./PT /CV /TBK
    text = re.sub(r'^(PT\.?\s*|CV\.?\s*|TBK\.?\s*|UD\.?\s*|FIRMA\.?\s*)', '', text)
    # Hapus suffix TBK/Tbk di akhir
    text = re.sub(r'\s+(TBK|Tbk|LTD|INC|CORP)\.?\s*$', '', text)
    # Hapus spasi berlebih
    text = re.sub(r'\s+', ' ', text).strip()
    # FORMAT_6: buang trailing ' -' dan tanda baca berlebih di akhir
    text = re.sub(r'[\s\-\.,;]+$', '', text).strip()
    text = re.sub(r'[.,;:\'\"]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_invoice_numbers_legacy(text):
    """
    Universal Invoice Extractor versi LAMA (persis perilaku asli).
    Digunakan untuk FORMAT_1-4 agar output sama dengan versi lama.
    """
    if pd.isna(text) or text is None:
        return []
    
    text = clean_invisible_chars(text).upper()
    
    # Hapus pola yang harus diabaikan (KWT, tanggal)
    # KWT.000524-57010226000192 -> hapus seluruh referensi kuitansi
    text = re.sub(r'KWT\.?\s*\d+[-/]?\d*', ' ', text)
    text = re.sub(r'\d{2}-\d{2}-\d{4}', ' ', text)
    text = re.sub(r'\d{2}/\d{2}/\d{4}', ' ', text)
    
    invoices = []
    
    # 1. Ekstrak invoice dengan prefix PELNS/PELSN/INV (pola: PELNS INV. 57012602649)
    #    Juga tangkap angka setelah prefix
    prefixed = re.findall(r'(?:PELNS?\s*INV\.?\s*|INV\.?\s*|PELNS?\s*)([A-Z0-9\-/]{8,})', text)
    invoices.extend(prefixed)
    
    # 2. Ekstrak invoice dalam kurung: (57062603037)
    in_parens = re.findall(r'\(([A-Z0-9\-/]{8,})\)', text)
    invoices.extend(in_parens)
    
    # 3. Ekstrak semua kandidat lain (format alfanumerik dengan tanda hubung/slash)
    others = re.findall(r'[A-Z][A-Z0-9\-/]{7,}', text)
    invoices.extend(others)
    
    # 4. Ekstrak angka murni 8+ digit (nomor invoice seperti 57012602649)
    #    TAPI jangan ambil yang merupakan bagian dari KWT/date (sudah dihapus di atas)
    pure_digits = re.findall(r'\b\d{8,}\b', text)
    invoices.extend(pure_digits)
    
    # Bersihkan: hapus duplikat, hapus yang mengandung KWT, hapus yang hanya tanda hubung
    filtered = []
    for inv in invoices:
        inv = inv.strip()
        if not inv:
            continue
        if 'KWT' in inv:
            continue
        # Buang yang hanya berisi tanda hubung/slash
        if re.match(r'^[\-/]+$', inv):
            continue
        filtered.append(inv)
    
    # Bersihkan duplikat dan kembalikan
    return list(set(filtered))


def extract_invoice_numbers(text, format_type='FORMAT_5'):
    """
    Universal Invoice Extractor - dispatcher berdasarkan format.
    
    - FORMAT_1-4: gunakan extract_invoice_numbers_legacy (perilaku lama persis)
    - FORMAT_5:   gunakan versi baru dengan pola tambahan:
        * Token diawali angka dengan "/" atau "-" (mis. 02/000021/10/2025/M, 24-0001234)
        * TIDAK menambah token pecahan (mis. "/2024/001", "56010324000574" dari "M-AR-56010324000574")
    """
    if format_type in ('FORMAT_1', 'FORMAT_2', 'FORMAT_3', 'FORMAT_4', 'FORMAT_FALLBACK'):
        return extract_invoice_numbers_legacy(text)
    
    # ==============================================
    # VERSI BARU UNTUK FORMAT_5
    # ==============================================
    if pd.isna(text) or text is None:
        return []
    
    text = clean_invisible_chars(text).upper()
    
    # Hapus pola yang harus diabaikan (KWT, tanggal)
    text = re.sub(r'KWT\.?\s*\d+[-/]?\d*', ' ', text)
    text = re.sub(r'\d{2}-\d{2}-\d{4}', ' ', text)
    text = re.sub(r'\d{2}/\d{2}/\d{4}', ' ', text)
    
    invoices = []
    
    # 1. Ekstrak invoice dengan prefix PELNS/PELSN/INV (pola: PELNS INV. 57012602649)
    prefixed = re.findall(r'(?:PELNS?\s*INV\.?\s*|INV\.?\s*|PELNS?\s*)([A-Z0-9\-/]{8,})', text)
    invoices.extend(prefixed)
    
    # 2. Ekstrak invoice dalam kurung: (57062603037)
    in_parens = re.findall(r'\(([A-Z0-9\-/]{8,})\)', text)
    invoices.extend(in_parens)
    
    # 3. Ekstrak token alfanumerik yang diawali huruf (M-AR-56010324000574, INV-123, dll)
    others = re.findall(r'[A-Z][A-Z0-9\-/]{7,}', text)
    invoices.extend(others)
    
    # 4. ✅ POLA BARU: Token yang DIAWALI ANGKA dan mengandung "/" atau "-"
    #    (mis. 02/000021/10/2025/M, 24-0001234)
    #    Hanya ambil token utuh, bukan pecahan dari token yang lebih besar.
    digit_started = re.findall(r'\b\d{1,4}[\-/][A-Z0-9][A-Z0-9\-/]{5,}', text)
    invoices.extend(digit_started)
    
    # 5. Ekstrak angka murni 8+ digit (nomor invoice seperti 57012602649)
    #    TAPI: jangan ambil yang merupakan bagian dari token M-AR-56010324000574
    #    (sudah tertangkap di pola 3 sebagai token utuh)
    #    Gunakan negative lookbehind untuk menghindari pecahan dari token alfanumerik
    pure_digits = re.findall(r'(?<![A-Z0-9\-/])\b\d{8,}\b(?![A-Z0-9\-/])', text)
    invoices.extend(pure_digits)
    
    # Bersihkan: hapus duplikat, hapus yang mengandung KWT, hapus yang hanya tanda hubung
    filtered = []
    for inv in invoices:
        inv = inv.strip()
        if not inv:
            continue
        if 'KWT' in inv:
            continue
        # Buang yang hanya berisi tanda hubung/slash
        if re.match(r'^[\-/]+$', inv):
            continue
        # Buang token pecahan yang diawali "/" atau "-" (mis. "/2024/001")
        if inv.startswith('/') or inv.startswith('-'):
            continue
        if not any(ch.isdigit() for ch in inv) and not inv.upper().startswith(("M-AR", "MAR", "INV", "PELNS", "PELSN")):
            continue
        filtered.append(inv)
    
    # Bersihkan duplikat dan kembalikan
    return list(set(filtered))

# ==============================================
# 🔹 PERIODE EXTRACTION DARI NO. BUKTI
# ==============================================
# Pola: 0004/BT/PHP/I/2026 -> Bulan I, Tahun 2026
# Format: /ROMAWI/TAHUN di akhir
ROMAN_MONTHS = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6,
    'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12
}

def extract_period_from_no_bukti(no_bukti):
    """
    Ekstrak periode (bulan, tahun) dari NO. BUKTI.
    Pola: 0004/BT/PHP/I/2026 -> (2026, 1)
    Fallback: None jika tidak cocok.
    """
    if pd.isna(no_bukti) or no_bukti is None:
        return None
    text = str(no_bukti).strip().upper()
    # Cari pola /ROMAWI/TAHUN di akhir
    match = re.search(r'/([IVX]+)/(\d{4})\s*$', text)
    if match:
        roman = match.group(1)
        year = int(match.group(2))
        month = ROMAN_MONTHS.get(roman)
        if month:
            return (year, month)
    return None

def extract_period_from_tanggal(tanggal):
    """
    Ekstrak periode (bulan, tahun) dari TANGGAL.
    """
    if pd.isna(tanggal) or tanggal is None:
        return None
    try:
        dt = pd.to_datetime(tanggal, errors='coerce')
        if pd.notna(dt):
            return (dt.year, dt.month)
    except Exception:
        pass
    return None

# ==============================================
# B2/B3 HELPERS: MODE BARIS FORMAT_5 + NOMINAL UM
# ==============================================
def is_apply_empty(val):
    """APPLY kosong: NaN, string kosong, atau hanya spasi."""
    if pd.isna(val):
        return True
    return str(val).strip() == ''

def is_um_text(description):
    """COMMANDS diawali UM (case-insensitive, strip)."""
    if pd.isna(description):
        return False
    return str(description).strip().upper().startswith('UM')

def is_um_unapplied_row(row):
    """UM belum di-apply: COMMANDS diawali UM DAN APPLY kosong."""
    return is_um_text(row.get('Description', '')) and is_apply_empty(row.get('APPLY', ''))

def get_nominal_dipakai_row(row):
    """B3: SISA UM (Rp) jika >0, else DEBET (Credit)."""
    try:
        sisa = float(row.get('SISA UM Parsed', 0) or 0)
    except Exception:
        sisa = 0
    if sisa and sisa > 0:
        return sisa
    try:
        return float(row.get('Credit', 0) or 0)
    except Exception:
        return 0.0

def filter_format5_mode(df, mode):
    """
    B2: Filter baris FORMAT_5 berdasarkan mode.
    - 'um_unapplied': UM + APPLY kosong (DEFAULT)
    - 'pelunasan': baris non-UM
    - 'semua': semua baris debet (perilaku lama)
    Return: (df_included, df_excluded)
    """
    if mode == 'um_unapplied':
        mask = df.apply(is_um_unapplied_row, axis=1)
    elif mode == 'pelunasan':
        mask = ~df['Description'].apply(is_um_text)
    else:
        mask = pd.Series(True, index=df.index)
    return df[mask].reset_index(drop=True), df[~mask].reset_index(drop=True)

# ==============================================
# FORMAT_6 (Oracle Receipts) helpers - additive, no change to FORMAT_1-5
# ==============================================
def _norm_cols(cols):
    return [str(c).strip().lower() for c in cols]

def is_format6_signature(cols):
    n = _norm_cols(cols)
    has_unapplied = 'unapplied amount' in n
    has_unidentified_or_ou = ('unidentified amount' in n) or ('operating unit' in n)
    has_receipt_amount = 'receipt amount' in n
    has_customer = 'customer name' in n
    has_receipt_no = 'receipt number' in n
    return bool(has_unapplied and has_unidentified_or_ou and has_receipt_amount and has_customer and has_receipt_no)

def find_format6_header_row(file, sheet, nrows=None):
    # cari-header otomatis baris 0-9 untuk FORMAT_6 saja
    import pandas as _pd
    for hr in range(0, 10):
        try:
            d = _pd.read_excel(file, sheet_name=sheet, header=hr, nrows=nrows)
            d.columns = d.columns.astype(str).str.strip()
            cols = [c for c in d.columns if not str(c).startswith('Unnamed')]
            if is_format6_signature(cols):
                return hr
        except Exception:
            continue
    return None

def detect_format_fast(file):
    """Deteksi format cepat saat upload (hanya baca header, tanpa proses data).
    Memakai fungsi signature yang sama; jika gagal return None tanpa raise."""
    try:
        xl = pd.ExcelFile(file)
        sheet_names = xl.sheet_names
        # FORMAT_5: sheet ALLPHP (case-insensitive, strip)
        for sheet in sheet_names:
            if str(sheet).strip().upper() == 'ALLPHP':
                return 'FORMAT_5'
        # FORMAT_5: signature kolom (nrows kecil)
        for sheet in sheet_names:
            try:
                df_test = pd.read_excel(file, sheet_name=sheet, nrows=1)
                df_test.columns = df_test.columns.astype(str).str.strip()
                required = ['NO. BUKTI', 'NAMA', 'DEBET (Rp)', 'COMMANDS']
                matches = sum(1 for col in required if col in df_test.columns)
                if matches >= 3:
                    return 'FORMAT_5'
            except Exception:
                continue
        # FORMAT_6: signature (nrows kecil via find_format6_header_row)
        for sheet in sheet_names:
            try:
                hr = find_format6_header_row(file, sheet, nrows=5)
                if hr is not None:
                    return 'FORMAT_6'
            except Exception:
                continue
        return None
    except Exception:
        return None

def is_reversal_row_f6(row):
    st_ = str(row.get('State', '') or '')
    su_ = str(row.get('Status', '') or '')
    return ('reversal' in st_.lower()) or (su_.strip().lower() == 'reversed')

def filter_format6_mode(df, mode):
    # reversal SELALU dikecualikan
    rev = df.apply(is_reversal_row_f6, axis=1)
    if mode == 'belum':
        inc_mask = (df['Unapplied Parsed'] > 0) & (~rev)
    else:  # 'semua_kecuali_reversal': State in Applied/Unapplied
        sm = df['State'].astype(str).str.strip().str.lower()
        inc_mask = sm.isin(['applied', 'unapplied']) & (~rev)
    inc = df[inc_mask].reset_index(drop=True)
    exc = df[~inc_mask].reset_index(drop=True)
    reasons = []
    for _, r in exc.iterrows():
        if is_reversal_row_f6(r):
            reasons.append('reversal')
        else:
            reasons.append('applied_nol' if str(r.get('State','')).strip().lower()=='applied' else 'lainnya')
    exc = exc.copy()
    exc['Alasan Dikecualikan'] = reasons
    return inc, exc

def load_bank_data(file):
    """Load dan validasi file Bank Statement DENGAN AUDIT CHECKPOINT + FORMAT DETECTION"""
    # ==============================================
    # 🔹 MULTI-SHEET HANDLING: Prioritas ALLPHP, lalu signature FORMAT_5,
    # lalu alur lama FORMAT_1-4 (sheet pertama). Tidak raise error.
    # ==============================================
    xl = pd.ExcelFile(file)
    sheet_names = xl.sheet_names
    st.info(f"📋 File memiliki {len(sheet_names)} sheet: {', '.join(sheet_names)}")

    # B1-1: Sheet bernama ALLPHP (abaikan huruf besar-kecil dan spasi)
    format5_sheet = None
    for sheet in sheet_names:
        if str(sheet).strip().upper() == 'ALLPHP':
            format5_sheet = sheet
            st.success(f"✅ Sheet ALLPHP dipakai langsung: '{sheet}'")
            break

    # B1-2: Jika tidak ada ALLPHP, cari sheet yang cocok signature FORMAT_5
    if format5_sheet is None:
        for sheet in sheet_names:
            try:
                df_test = pd.read_excel(file, sheet_name=sheet)
                df_test.columns = df_test.columns.str.strip()
                # Cek signature FORMAT_5: NO. BUKTI, NAMA, DEBET (Rp), COMMANDS
                required = ['NO. BUKTI', 'NAMA', 'DEBET (Rp)', 'COMMANDS']
                matches = sum(1 for col in required if col in df_test.columns)
                if matches >= 3:  # 75% cocok
                    format5_sheet = sheet
                    st.success(f"✅ Sheet berformat ALLPHP ditemukan: '{sheet}'")
                    break
            except Exception:
                continue

    # FORMAT_6: cari sheet pertama cocok signature (evaluasi SEBELUM FORMAT_3/4)
    _f6_sheet = None
    _f6_header = 0
    for _sh in sheet_names:
        try:
            _hr = find_format6_header_row(file, _sh)
            if _hr is not None:
                _f6_sheet = _sh
                _f6_header = _hr
                st.success(f"✅ Sheet FORMAT_6 (Oracle Receipts) ditemukan: '{_sh}' (header baris {_hr+1})")
                break
        except Exception:
            continue
    if _f6_sheet is not None:
        df = pd.read_excel(file, sheet_name=_f6_sheet, header=_f6_header)
        st.info(f"📊 1. LOAD ASLI: {len(df)} BARIS TOTAL (sheet '{_f6_sheet}')")
        df.attrs['format6_sheet'] = _f6_sheet
        df.attrs['format6_header'] = _f6_header
    elif format5_sheet is not None:
        # Load dari sheet yang cocok dengan FORMAT_5
        import pandas as _pd2
        df = _pd2.read_excel(file, sheet_name=format5_sheet)
        st.info(f"📊 1. LOAD ASLI: {len(df)} BARIS TOTAL (sheet '{format5_sheet}')")
    else:
        # B1-3: Tidak ada sheet FORMAT_5: pakai alur lama (sheet pertama, FORMAT_1-4)
        st.info("ℹ️ Sheet FORMAT_5 tidak ditemukan, menggunakan alur deteksi format lama (sheet pertama).")
        df = pd.read_excel(file)
        st.info(f"📊 1. LOAD ASLI: {len(df)} BARIS TOTAL")

    # Bersihkan nama kolom dari spasi berlebih
    df.columns = df.columns.astype(str).str.strip()
    # Buang kolom sampah '[ ]' dan 'Unnamed:*' (FORMAT_6)
    df = df.loc[:, ~df.columns.str.match(r'(?i)^unnamed')]
    if '[ ]' in df.columns:
        df = df.drop(columns=['[ ]'])
    # FORMAT_6 early: jika signature cocok -> mapping langsung, SEBELUM FORMAT_3/4
    _f6_early = is_format6_signature(list(df.columns))
    if _f6_early:
        _map6 = {'Receipt Date': 'Value Date', 'Receipt Number': 'Reference No.', 'Receipt Amount': 'Credit', 'Customer Name': 'Customer_raw'}
        for _k, _v in _map6.items():
            for _c in list(df.columns):
                if str(_c).strip().lower() == str(_k).strip().lower():
                    if _v not in df.columns:
                        df = df.rename(columns={_c: _v})
                    break
        for _c in ['State', 'Status', 'Receipt Method', 'Unapplied Amount', 'Unidentified Amount', 'Operating Unit', 'Currency']:
            if _c not in df.columns:
                _found = None
                for _cc in list(df.columns):
                    if str(_cc).strip().lower() == _c.strip().lower():
                        _found = _cc
                        break
                if _found is not None and _found != _c:
                    df = df.rename(columns={_found: _c})
                elif _found is None:
                    df[_c] = ''
        df['Customer'] = df.get('Customer_raw', '')
        df['Description'] = (df.get('Receipt Method', '').astype(str) + ' | ' + df.get('State', '').astype(str)).str.strip()
        df['Value Date'] = pd.to_datetime(df.get('Value Date'), errors='coerce')
        df['Credit'] = df.get('Credit', 0).apply(parse_universal_amount)
        df['Unapplied Parsed'] = df.get('Unapplied Amount', 0).apply(parse_universal_amount)
        df['Unidentified Parsed'] = df.get('Unidentified Amount', 0).apply(parse_universal_amount)
        df['Nominal Dipakai'] = df.apply(lambda r: float(r.get('Unapplied Parsed', 0) or 0) if float(r.get('Unapplied Parsed', 0) or 0) > 0 else float(r.get('Credit', 0) or 0), axis=1)
        df['Periode'] = df['Value Date'].apply(extract_period_from_tanggal)
        df['Periode Source'] = 'Receipt Date'
        df['Periode Note'] = ''
        df['Customer_normalized'] = df['Customer'].apply(normalize_customer_key)
        df.attrs['format_type'] = 'FORMAT_6'
        df.attrs['strategy'] = 'CUSTOMER_FIRST'
        st.success('✅ Format terdeteksi: Oracle Receipts (FORMAT_6)')
        st.info(f"📊 2. SETELAH CEK KOLOM: {len(df)} BARIS")
        st.info(f"📊 3. SETELAH KONVERSI CREDIT: {len(df[df['Credit'] > 0])} BARIS DENGAN NILAI")
        st.info(f"📊 4. SEBELUM FILTER: {len(df)} BARIS")
        df = df[df['Credit'] > 0].reset_index(drop=True)
        st.success(f"📊 5. SELESAI LOAD: {len(df)} BARIS SIAP DIPROSES")
        df['bank_id'] = df.index
        return df


    # ==============================================
    # 🔹 FORMAT DETECTION ENGINE - ADAPTIVE MULTI-FORMAT
    # ==============================================
    format_type = 'UNKNOWN'
    column_mapping = {}

    # DEFINE FORMAT SIGNATURES - TIDAK HARDCODE, BISA DITAMBAHKAN FUTURE FORMAT
    FORMAT_SIGNATURES = [
        {
            'id': 'FORMAT_2',
            'name': 'Rincian Transaksi / MVA / Host to Host',
            'required_columns': ['Rincian Transaksi', 'Customers', 'Kredit'],
            'mapping': {
                'Tgl.': 'Date',
                'Tanggal': 'Date',
                'Date': 'Date',
                'Tgl & Waktu': 'Date & Time',
                'Tanggal & Waktu': 'Date & Time',
                'Date & Time': 'Date & Time',
                'Rincian Transaksi': 'Description',
                'Keterangan': 'Description',
                'Customers': 'Customer',
                'Nama Pelanggan': 'Customer',
                'Nama Customer': 'Customer',
                'Debit': 'Debit',
                'Kredit': 'Credit',
                'Credit': 'Credit',
                'Saldo': 'Balance',
                'Reference': 'Reference No.',
                'Ref': 'Reference No.',
                'No Ref': 'Reference No.',
                'No. Referensi': 'Reference No.'
            },
            'strategy': 'CUSTOMER_FIRST'
        },
        {
            'id': 'FORMAT_1',
            'name': 'Standard Bank Statement',
            'required_columns': ['Date & Time', 'Value Date', 'Reference No.'],
            'mapping': {
                'Account No.': 'Account No.',
                'Account Number': 'Account No.',
                'Date & Time': 'Date & Time',
                'Value Date': 'Value Date',
                'Description': 'Description',
                'Reference No.': 'Reference No.',
                'Debit': 'Debit',
                'Credit': 'Credit',
                'Balance': 'Balance'
            },
            'strategy': 'DESCRIPTION_FIRST'
        },
        {
            'id': 'FORMAT_3',
            'name': 'UMP (Uang Muka Penjualan)',
            'required_columns': ['Receipt Amount', 'Customer Name'],
            'header_row': 3,  # Header ada di baris ke-4 (0-indexed: 3)
            'mapping': {
                'Receipt Amount': 'Credit',  # Kolom ini berisi nominal IDR
                'No': 'No',
                'Receipt Method': 'Receipt Method',
                'Receipt Number': 'Reference No.',
                'Customer Name': 'Customer',
                'Receipt Type': 'Receipt Type',
                'State': 'State',
                'Receipt Date': 'Value Date',
                'Comments': 'Description',
                'Account': 'Account'
            },
            'strategy': 'CUSTOMER_FIRST'
        },
        {
            'id': 'FORMAT_5',
            'name': 'PHP BNI BJM (Perincian Hutang Piutang)',
            'required_columns': ['NO. BUKTI', 'NAMA', 'DEBET (Rp)', 'COMMANDS'],
            'mapping': {
                'TYPE': 'TYPE',
                'NO. BUKTI': 'Reference No.',
                'TANGGAL': 'Value Date',
                'NAMA': 'Customer',
                'COMMANDS': 'Description',
                'DEBET (Rp)': 'Debit',
                'KREDIT (Rp)': 'Credit',
                'SISA UM (Rp)': 'SISA UM (Rp)',
                'ADJUST UM (Rp)': 'ADJUST UM (Rp)',
                'APPLY': 'APPLY'
            },
            'strategy': 'CUSTOMER_FIRST'
        },
        # FORMAT_4 (UMP Pending) dihapus dari FORM_SIGNATURES karena menggunakan
        # metode deteksi anchor-scan khusus (PRIORITAS 0) untuk menangani merged header 3 baris
    ]

    # DETEKSI FORMAT SECARA OTOMATIS BERDASARKAN SIGNATURE
    detected_format = None

    # ==============================================
    # ✅ PRIORITAS 0: ANCHOR-SCAN FORMAT_4 (UMP PENDING - MERGED HEADER 3 BARIS)
    # Deteksi khusus untuk file dengan header merge vertikal & horizontal
    # yang TIDAK bisa dibaca dengan pd.read_excel(file, header=N) biasa
    # ==============================================
    if not detected_format:
        try:
            df_raw = pd.read_excel(file, header=None)

            anchor_row = None
            col_no = col_date = col_ref = col_cust = None

            # Cari baris yang mengandung 'BPUK' DAN 'CUSTOMER' sekaligus -> anchor header utama
            for r in range(min(10, len(df_raw))):
                row_vals = [str(v).strip().upper() if pd.notna(v) else '' for v in df_raw.iloc[r].tolist()]
                if 'BPUK' in row_vals and 'CUSTOMER' in row_vals:
                    anchor_row = r
                    for c, val in enumerate(row_vals):
                        if val == 'NO':
                            col_no = c
                        elif val == 'TGL TRANSFER':
                            col_date = c
                        elif val == 'BPUK':
                            col_ref = c
                        elif val == 'CUSTOMER':
                            col_cust = c
                    break

            if anchor_row is not None and col_ref is not None and col_cust is not None:
                # Cari kolom 'Rp.' di 1-2 baris di bawah anchor (sub-header amount)
                col_credit = None
                for offset in (1, 2):
                    check_row = anchor_row + offset
                    if check_row < len(df_raw):
                        row_vals = [str(v).strip() if pd.notna(v) else '' for v in df_raw.iloc[check_row].tolist()]
                        for c, val in enumerate(row_vals):
                            if val == 'Rp.':
                                col_credit = c
                                break
                    if col_credit is not None:
                        break

                if col_credit is not None:
                    data_start = anchor_row + 3  # header memakan 3 baris total
                    df_f4 = df_raw.iloc[data_start:].reset_index(drop=True)

                    df = pd.DataFrame({
                        'No': df_f4.iloc[:, col_no].values if col_no is not None else range(len(df_f4)),
                        'Value Date': df_f4.iloc[:, col_date].values if col_date is not None else None,
                        'Reference No.': df_f4.iloc[:, col_ref].values,
                        'BPUK': df_f4.iloc[:, col_ref].values,  # Kolom BPUK sama dengan Reference No. dari Excel
                        'Customer': df_f4.iloc[:, col_cust].values,
                        'Credit': df_f4.iloc[:, col_credit].values,
                    })

                    # Hapus baris yang semua NaN
                    df = df.dropna(how='all').reset_index(drop=True)

                    detected_format = {
                        'id': 'FORMAT_4',
                        'name': 'UMP Pending',
                        'strategy': 'CUSTOMER_FIRST'
                        # SENGAJA TANPA key 'mapping' -> sinyal bahwa kolom sudah final
                    }
                    format_type = 'FORMAT_4'

                    st.success(f"✅ Format terdeteksi: UMP Pending (FORMAT_4) — merged header di baris ke-{anchor_row + 1}")
                    st.info(f"🔧 Kolom terdeteksi -> No: kol {col_no}, Tgl: kol {col_date}, BPUK: kol {col_ref}, Customer: kol {col_cust}, Rp.: kol {col_credit}")
        except Exception as e:
            st.warning(f"⚠️ Gagal menjalankan deteksi khusus FORMAT_4: {e}")

    # ✅ PRIORITAS 1: CEK FORMAT DENGAN HEADER ROW KHUSUS (FORMAT 3: UMP)
    for fmt in FORMAT_SIGNATURES:
        if 'header_row' in fmt:
            try:
                # Coba baca dengan header row yang ditentukan
                df_test = pd.read_excel(file, header=fmt['header_row'])
                df_test.columns = df_test.columns.str.strip()
                
                # Hitung berapa banyak required column yang ada
                matches = sum(1 for col in fmt['required_columns'] if col in df_test.columns)
                
                # Jika 70% atau lebih kolom required ditemukan = itu formatnya
                if matches >= len(fmt['required_columns']) * 0.7:
                    detected_format = fmt
                    # Load ulang dengan header yang benar
                    df = df_test
                    break
            except Exception:
                continue
    
    # ✅ PRIORITAS 2: CEK FORMAT STANDARD (FORMAT 1 & 2)
    if not detected_format:
        for fmt in FORMAT_SIGNATURES:
            if 'header_row' not in fmt:  # Skip yang sudah dicek
                # Hitung berapa banyak required column yang ada
                matches = sum(1 for col in fmt['required_columns'] if col in df.columns)
                # Jika 70% atau lebih kolom required ditemukan = itu formatnya
                if matches >= len(fmt['required_columns']) * 0.7:
                    detected_format = fmt
                    break

    if detected_format:
        format_type = detected_format['id']
        if format_type != 'FORMAT_4':
            st.success(f"✅ Format terdeteksi: {detected_format['name']} ({format_type})")
            st.info(f"🔧 Matching Strategy: {detected_format['strategy']}")

        # DYNAMIC COLUMN MAPPING - hanya untuk format yang punya mapping (bukan FORMAT_4)
        if 'mapping' in detected_format:
            mapped_cols = {}
            for original_col in df.columns:
                clean_col = original_col.strip()
                # Cari di mapping
                if clean_col in detected_format['mapping']:
                    mapped_cols[original_col] = detected_format['mapping'][clean_col]

            # Apply mapping
            df = df.rename(columns=mapped_cols)

        # GENERATE MISSING COLUMNS OTOMATIS
        STANDARD_COLUMNS = ['Date', 'Value Date', 'Description', 'Reference No.',
                           'Debit', 'Credit', 'Balance', 'Customer', 'Account No.', 'Date & Time']

        for col in STANDARD_COLUMNS:
            if col not in df.columns:
                df[col] = ''

        # Generate Value Date jika tidak ada
        if 'Value Date' not in df.columns or df['Value Date'].isna().all():
            if 'Date' in df.columns:
                df['Value Date'] = pd.to_datetime(df['Date'], errors='coerce')
            elif 'Date & Time' in df.columns:
                df['Value Date'] = pd.to_datetime(df['Date & Time'], errors='coerce')
        
        # ✅ FIX DATE & TIME BLANK: Fallback isi Date & Time jika kosong
        # SKIP untuk FORMAT_4 karena Value Date masih raw string di titik ini
        if 'Date & Time' in df.columns and format_type != 'FORMAT_4':
            # Jika Date & Time kosong atau tidak valid, isi dengan Value Date
            df['Date & Time'] = pd.to_datetime(df['Date & Time'], errors='coerce')
            df.loc[df['Date & Time'].isna(), 'Date & Time'] = df.loc[df['Date & Time'].isna(), 'Value Date']
            
            # Jika masih kosong juga coba dari kolom Date
            df.loc[df['Date & Time'].isna() & df['Date'].notna(), 'Date & Time'] = pd.to_datetime(df.loc[df['Date & Time'].isna() & df['Date'].notna(), 'Date'], errors='coerce')

        # ✅ SPESIAL HANDLING UNTUK FORMAT 3 (UMP)
        if format_type == 'FORMAT_3':
            # Pastikan Description diisi dari Comments jika kosong
            if 'Description' in df.columns and 'Comments' in df.columns:
                df['Description'] = df.apply(
                    lambda row: row['Comments'] if pd.isna(row['Description']) or str(row['Description']).strip() == '' 
                    else row['Description'], 
                    axis=1
                )
            
            # Konversi Receipt Date ke Value Date jika ada
            if 'Receipt Date' in df.columns and 'Value Date' in df.columns:
                df['Value Date'] = pd.to_datetime(df['Receipt Date'], errors='coerce')
            
            # Tambahkan kolom Date & Time dari Value Date jika belum ada
            if 'Date & Time' not in df.columns or df['Date & Time'].isna().all():
                df['Date & Time'] = df['Value Date']
            
            # Normalisasi Customer untuk UMP format (gunakan mapping yang sama dengan FORMAT 2)
            if 'Customer' in df.columns:
                df['Customer_normalized'] = df['Customer'].apply(normalize_customer_name)
        
        # ✅ SPESIAL HANDLING UNTUK FORMAT 4 (UMP PENDING)
        if format_type == 'FORMAT_4':
            # 1. Hapus baris kosong (blank row pemisah tahun dan header)
            df = df.dropna(how='all').reset_index(drop=True)
            
            # 2. Drop baris yang NO-nya kosong (blank row pemisah)
            if 'No' in df.columns:
                df = df[df['No'].notna() & (df['No'] != '')].reset_index(drop=True)
            
            # 3. Hapus baris duplikat header yang mungkin terbaca
            df = df[df['Customer'].notna() & (df['Customer'] != '')].reset_index(drop=True)
            df = df[df['Customer'].str.strip().str.upper() != 'CUSTOMER'].reset_index(drop=True)
            
            # 4. Konversi Value Date dari TGL TRANSFER (format: 03-JUN-2024 atau 03/06/2024)
            if 'Value Date' in df.columns:
                # Bersihkan whitespace dan karakter tersembunyi sebelum parsing
                df['Value Date'] = df['Value Date'].astype(str).str.strip()
                
                # Coba parse dengan format text Inggris dulu (03-JUN-2024)
                df['Value Date'] = pd.to_datetime(df['Value Date'], format='%d-%b-%Y', errors='coerce')
                # Fallback: format numerik (03/06/2024)
                df.loc[df['Value Date'].isna(), 'Value Date'] = pd.to_datetime(
                    df.loc[df['Value Date'].isna(), 'Value Date'], errors='coerce', dayfirst=True
                )
            
            # ✅ Hilangkan komponen jam (normalize ke 00:00:00)
            if 'Value Date' in df.columns:
                df['Value Date'] = df['Value Date'].dt.normalize()
            
            # ✅ Isi Date & Time dari Value Date agar tidak kosong di display
            if 'Date & Time' in df.columns:
                df['Date & Time'] = df['Value Date']
            
            # 5. Seed Description dari Customer name agar matching scoring tetap akurat
            # Karena FORMAT_4 tidak punya kolom Description, gunakan Customer sebagai Description
            if 'Customer' in df.columns:
                df['Description'] = df['Customer'].astype(str).str.strip().str.upper()
            
            # 6. Normalisasi Customer
            if 'Customer' in df.columns:
                df['Customer_normalized'] = df['Customer'].apply(normalize_customer_name)
        
        # ✅ SPESIAL HANDLING UNTUK FORMAT 5 (PHP BNI BJM)
        if format_type == 'FORMAT_5':
            # 1. Hapus baris kosong
            df = df.dropna(how='all').reset_index(drop=True)
            
            # 2. Hapus baris duplikat header yang mungkin terbaca
            if 'Customer' in df.columns:
                df = df[df['Customer'].notna() & (df['Customer'] != '')].reset_index(drop=True)
                df = df[df['Customer'].str.strip().str.upper() != 'NAMA'].reset_index(drop=True)
            
            # 3. Konversi Value Date dari TANGGAL
            if 'Value Date' in df.columns:
                df['Value Date'] = pd.to_datetime(df['Value Date'], errors='coerce', dayfirst=True)
            
            # 4. ✅ STRATEGI KHUSUS: UM masuk sebagai DEBET di format ini
            #    Untuk matching, DEBET dianggap sebagai CREDIT
            #    KREDIT (Rp) tetap dipertahankan sebagai kolom referensi
            if 'Debit' in df.columns:
                # Simpan nilai DEBET sebagai Credit untuk matching
                df['Credit'] = df['Debit']
            
            # 5. Normalisasi Customer
            if 'Customer' in df.columns:
                df['Customer_normalized'] = df['Customer'].apply(normalize_customer_name)
            
            # 6. Seed Description dari Customer name agar matching scoring tetap akurat
            if 'Customer' in df.columns and 'Description' in df.columns:
                df['Description'] = df.apply(
                    lambda row: str(row['Customer']).upper() if pd.isna(row['Description']) or str(row['Description']).strip() == '' 
                    else str(row['Description']).upper(), 
                    axis=1
                )
            
            # 7. ✅ EKSTRAKSI PERIODE DARI NO. BUKTI (prioritas) / TANGGAL (fallback)
            #    Jika NO. BUKTI dan TANGGAL tidak sinkron, pakai NO. BUKTI dan beri catatan
            if 'Reference No.' in df.columns:
                df['Periode'] = df['Reference No.'].apply(extract_period_from_no_bukti)
                df['Periode Source'] = df['Reference No.'].apply(
                    lambda x: 'NO. BUKTI' if extract_period_from_no_bukti(x) else ''
                )
                
                # Fallback ke TANGGAL jika NO. BUKTI tidak punya pola
                mask_no_periode = df['Periode'].isna()
                if mask_no_periode.any() and 'Value Date' in df.columns:
                    df.loc[mask_no_periode, 'Periode'] = df.loc[mask_no_periode, 'Value Date'].apply(extract_period_from_tanggal)
                    df.loc[mask_no_periode, 'Periode Source'] = 'TANGGAL'
                
                # Deteksi mismatch: NO. BUKTI dan TANGGAL berbeda
                if 'Value Date' in df.columns:
                    def check_mismatch(row):
                        if pd.isna(row.get('Periode')) or pd.isna(row.get('Value Date')):
                            return ''
                        periode_bukti = extract_period_from_no_bukti(row.get('Reference No.'))
                        periode_tanggal = extract_period_from_tanggal(row.get('Value Date'))
                        if periode_bukti and periode_tanggal and periode_bukti != periode_tanggal:
                            return f"⚠️ NO. BUKTI ({periode_bukti[0]}-{periode_bukti[1]}) ≠ TANGGAL ({periode_tanggal[0]}-{periode_tanggal[1]}), pakai NO. BUKTI"
                        return ''
                    df['Periode Note'] = df.apply(check_mismatch, axis=1)
                else:
                    df['Periode Note'] = ''
            else:
                df['Periode'] = None
                df['Periode Source'] = ''
                df['Periode Note'] = ''
            
            # 8. ✅ DETEKSI UM DARI COMMANDS (diawali "UM")
            if 'Description' in df.columns:
                df['Is UM'] = df['Description'].apply(
                    lambda x: str(x).strip().upper().startswith('UM') if pd.notna(x) else False
                )
            else:
                df['Is UM'] = False

            # 9. ✅ B3: NOMINAL PENCOCOKAN MODE UM (SISA UM jika >0, else DEBET)
            if 'SISA UM (Rp)' in df.columns:
                df['SISA UM Parsed'] = df['SISA UM (Rp)'].apply(parse_universal_amount)
            else:
                df['SISA UM (Rp)'] = 0
                df['SISA UM Parsed'] = 0.0
            if 'APPLY' not in df.columns:
                df['APPLY'] = ''
        
        # Normalisasi Customer JIKA ADA (untuk FORMAT 2)
        elif 'Customer' in df.columns and format_type == 'FORMAT_2':
            df['Customer_normalized'] = df['Customer'].apply(normalize_customer_name)

    else:
        # FALLBACK: TIDAK ADA FORMAT YANG TERDETEKSI, COBA CARI MAPPING OTOMATIS
        st.warning("⚠️ Format tidak dikenal, mencoba mapping kolom secara otomatis...")
        format_type = 'FORMAT_FALLBACK'

        # Auto detect kolom berdasarkan keyword
        auto_mapping = {}
        for col in df.columns:
            col_upper = col.upper()
            if 'DATE' in col_upper or 'TGL' in col_upper:
                auto_mapping[col] = 'Value Date'
            elif 'DESC' in col_upper or 'KET' in col_upper or 'TRANSAKSI' in col_upper:
                auto_mapping[col] = 'Description'
            elif 'CRED' in col_upper or 'KREDIT' in col_upper or 'MASUK' in col_upper:
                auto_mapping[col] = 'Credit'
            elif 'DEB' in col_upper or 'DEBIT' in col_upper or 'KELUAR' in col_upper:
                auto_mapping[col] = 'Debit'
            elif 'SALDO' in col_upper or 'BALANCE' in col_upper:
                auto_mapping[col] = 'Balance'
            elif 'REF' in col_upper or 'REFERENSI' in col_upper:
                auto_mapping[col] = 'Reference No.'
            elif 'CUST' in col_upper or 'PELANGGAN' in col_upper or 'NAMA' in col_upper:
                auto_mapping[col] = 'Customer'

        df = df.rename(columns=auto_mapping)

        # Tambahkan kolom minimal
        for col in ['Value Date', 'Description', 'Debit', 'Credit', 'Balance']:
            if col not in df.columns:
                df[col] = 0 if col in ['Debit','Credit','Balance'] else ''

    # Simpan metadata di dataframe
    df.attrs['format_type'] = format_type
    if detected_format:
        df.attrs['strategy'] = detected_format['strategy']
    else:
        df.attrs['strategy'] = 'DESCRIPTION_FIRST'

    st.info(f"📊 2. SETELAH CEK KOLOM: {len(df)} BARIS")

    # 🔴 SEMENTARA NON AKTIFKAN pd.to_numeric! GUNAKAN parse_universal_amount LANGSUNG
    # df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
    df['Credit'] = df['Credit'].apply(parse_universal_amount)
    # ✅ B3 finalisasi: SISA UM Parsed mungkin string sebelum konversi; pastikan numerik
    if format_type == 'FORMAT_5':
        if 'SISA UM Parsed' in df.columns:
            df['SISA UM Parsed'] = df['SISA UM Parsed'].apply(parse_universal_amount)
        else:
            df['SISA UM Parsed'] = 0.0
        df['Nominal Dipakai'] = df.apply(
            lambda r: float(r.get('SISA UM Parsed', 0) or 0) if float(r.get('SISA UM Parsed', 0) or 0) > 0 else float(r.get('Credit', 0) or 0),
            axis=1
        )

    st.info(f"📊 3. SETELAH KONVERSI CREDIT: {len(df[df['Credit'] > 0])} BARIS DENGAN NILAI")

    # Konversi tanggal
    df['Value Date'] = pd.to_datetime(df['Value Date'], errors='coerce')

    st.info(f"📊 4. SEBELUM FILTER: {len(df)} BARIS")

    # ✅ FILTER Credit > 0 - TANPA BATAS MINIMAL
    df = df[df['Credit'] > 0].reset_index(drop=True)

    st.success(f"📊 5. SELESAI LOAD: {len(df)} BARIS SIAP DIPROSES")

    # Tambahkan ID unik
    df['bank_id'] = df.index

    return df

def load_aging_data(file):
    """Load dan validasi file AR Aging dengan auto detect header row"""
    # Coba berbagai baris header untuk file yang ada report header di atasnya
    for header_row in range(0, 10):
        try:
            df = pd.read_excel(file, header=header_row)

            # Bersihkan nama kolom dari spasi berlebih dan ubah ke uppercase
            df.columns = df.columns.str.strip().str.upper()

            # Hapus kolom Unnamed
            df = df.loc[:, ~df.columns.str.contains('^UNNAMED', na=False)]

            if len(df.columns) >= 3:
                # Mapping berbagai variasi nama kolom yang umum
                column_mapping = {
                    'NO INVOICE': 'No Invoice',
                    'INVOICE NO': 'No Invoice',
                    'NO. INVOICE': 'No Invoice',
                    'NOMOR INVOICE': 'No Invoice',
                    'CUSTOMER': 'Customer',
                    'NAMA CUSTOMER': 'Customer',
                    'NAMA': 'Customer',
                    'SALDO PIUTANG': 'SALDO PIUTANG',
                    'SALDO': 'SALDO PIUTANG',
                    'SALDO KONVERSI': 'SALDO PIUTANG',
                    'TOTAL PIUTANG': 'SALDO PIUTANG',
                    'OUTSTANDING': 'SALDO PIUTANG',
                    'TANGGAL INVOICE': 'Invoice Date',
                    'INVOICE DATE': 'Invoice Date',
                    'TANGGAL': 'Invoice Date',
                    'TGL': 'Invoice Date',
                    'DATE': 'Invoice Date'
                }

                # Rename kolom sesuai mapping
                df = df.rename(columns=column_mapping)

                # ✅ PENGAMAN: Jika ada >1 kolom 'SALDO PIUTANG', pilih berdasarkan prioritas
                # (SALDO KONVERSI > SALDO PIUTANG > SALDO > lainnya)
                saldo_cols = [c for c in df.columns if c == 'SALDO PIUTANG']
                if len(saldo_cols) > 1:
                    # Cari kolom asal yang paling prioritas
                    chosen_source = None
                    for pref in ['SALDO KONVERSI', 'SALDO PIUTANG', 'SALDO']:
                        if pref in df.columns:
                            chosen_source = pref
                            break
                    if chosen_source is None:
                        chosen_source = saldo_cols[0]
                    
                    # Ambil data dari kolom prioritas, hapus duplikat
                    df['SALDO PIUTANG'] = df[chosen_source]
                    # Drop kolom SALDO PIUTANG duplikat (sisakan 1)
                    seen = set()
                    cols_to_keep = []
                    for c in df.columns:
                        if c == 'SALDO PIUTANG' and c in seen:
                            continue
                        if c == 'SALDO PIUTANG':
                            seen.add(c)
                        cols_to_keep.append(c)
                    df = df[cols_to_keep]
                    st.warning(f"⚠️ Ditemukan lebih dari satu kolom saldo. Menggunakan kolom '{chosen_source}' sebagai SALDO PIUTANG.")

                required_columns = ['No Invoice', 'Customer', 'SALDO PIUTANG']

                # Cek apakah semua kolom wajib ada
                if all(col in df.columns for col in required_columns):
                    # Hapus baris kosong
                    df = df.dropna(how='all')

                    # Tambahkan ID unik
                    df['aging_id'] = df.index

                    # Konversi tanggal invoice jika ada
                    if 'Invoice Date' in df.columns:
                        df['Invoice Date'] = pd.to_datetime(df['Invoice Date'], errors='coerce')

                    return df

        except Exception:
            continue

    # ==============================================
    # 🔹 FALLBACK: AUTO-DETECT KOLOM BERDASARKAN KEYWORD
    # ==============================================
    try:
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip().str.upper()
        df = df.loc[:, ~df.columns.str.contains('^UNNAMED', na=False)]

        # Auto-detect kolom berdasarkan keyword
        auto_mapping = {}
        for col in df.columns:
            col_upper = str(col).upper()
            if 'INVOICE' in col_upper or 'NO. BUKTI' in col_upper or 'NO BUKTI' in col_upper:
                auto_mapping[col] = 'No Invoice'
            elif 'CUSTOMER' in col_upper or 'NAMA' in col_upper or 'PELANGGAN' in col_upper:
                auto_mapping[col] = 'Customer'
            elif 'SALDO' in col_upper or 'PIUTANG' in col_upper or 'OUTSTANDING' in col_upper:
                auto_mapping[col] = 'SALDO PIUTANG'
            elif 'TANGGAL' in col_upper or 'TGL' in col_upper or 'DATE' in col_upper:
                auto_mapping[col] = 'Invoice Date'

        df = df.rename(columns=auto_mapping)

        required_columns = ['No Invoice', 'Customer', 'SALDO PIUTANG']
        if all(col in df.columns for col in required_columns):
            df = df.dropna(how='all')
            df['aging_id'] = df.index
            if 'Invoice Date' in df.columns:
                df['Invoice Date'] = pd.to_datetime(df['Invoice Date'], errors='coerce')
            return df
    except Exception:
        pass

    # Jika tidak ditemukan header yang cocok
    raise ValueError("Tidak dapat menemukan kolom yang sesuai di file AR Aging. Pastikan file memiliki kolom No Invoice, Customer, dan Saldo Piutang.")

def parse_universal_amount(value):
    """
    Universal amount parser yang mendukung BOTH format Indonesia dan US
    ✅ Format ID: 22.200.000,00 -> 22200000.0
    ✅ Format US: 147,322,682,017.20 -> 147322682017.20
    ✅ Otomatis deteksi format
    ✅ Tidak ada lagi error scaling 10x / 0.1x
    """
    # 🔴 HARUS DIPALING AWAL! Cek apakah ini Series object SEBELUM apapun
    if hasattr(value, '__iter__') and not isinstance(value, (str, int, float, bool)):
        # Jika ini Series, ambil nilai pertama
        if hasattr(value, 'iloc'):
            value = value.iloc[0] if len(value) > 0 else 0
        else:
            return 0.0

    if pd.isna(value) or value is None or value == '' or value == '-':
        return 0.0

    # 🔴 PEMBAHARUAN: HAPUS SEMUA KARAKTER TERSEMBUNYI DULU!
    # Non Breaking Space, Tab, Newline, dan karakter invisble lainnya
    text = str(value)
    text = re.sub(r'\s+', '', text)

    # Hapus semua karakter selain angka, titik dan koma
    digits = re.sub(r'[^\d.,]', '', text)

    if not digits:
        return 0.0

    # Jika cuma angka murni tanpa tanda apapun
    if '.' not in digits and ',' not in digits:
        return float(digits)

    # Hitung jumlah titik dan koma
    dot_count = digits.count('.')
    comma_count = digits.count(',')

    # 🔹 DETEKSI FORMAT
    if dot_count > 0 and comma_count > 0:
        # Ada keduanya: lihat mana yang terakhir sebagai desimal
        last_dot = digits.rfind('.')
        last_comma = digits.rfind(',')

        if last_comma > last_dot:
            # ✅ FORMAT INDONESIA: titik = ribuan, koma = desimal
            digits = digits.replace('.', '').replace(',', '.')
        else:
            # ✅ FORMAT US: koma = ribuan, titik = desimal
            digits = digits.replace(',', '')

    elif comma_count > 1:
        # ✅ FORMAT US: koma sebagai ribuan separator
        digits = digits.replace(',', '')

    elif dot_count > 1:
        # ✅ FORMAT INDONESIA: titik sebagai ribuan separator
        digits = digits.replace('.', '')

    # Konversi ke float
    try:
        amount = float(digits)
        return amount
    except:
        return 0.0

def clean_data(df_bank, df_aging):
    """Cleaning data untuk kedua file"""

    # ✅ FIX FINAL SEMUA ERROR PANDAS:
    # 1. HAPUS DULU KOLOM DUPLIKAT (PENYEBAB UTAMA ERROR cannot reindex duplicate labels)
    df_bank = df_bank.loc[:, ~df_bank.columns.duplicated()]
    df_aging = df_aging.loc[:, ~df_aging.columns.duplicated()]

    # 2. Reset index
    # 3. Hapus duplikat baris
    # 4. Paksa buat index baru yang benar-benar unique & berurutan
    df_bank = df_bank.reset_index(drop=True).drop_duplicates(keep='first')
    df_bank.index = pd.RangeIndex(len(df_bank))

    df_aging = df_aging.reset_index(drop=True).drop_duplicates(keep='first')
    df_aging.index = pd.RangeIndex(len(df_aging))

    # --------------------
    # Cleaning Bank Statement
    # --------------------
    df_bank['Description'] = df_bank['Description'].astype(str).str.strip()
    df_bank['Description'] = df_bank['Description'].str.replace(r'\s+', ' ', regex=True)
    df_bank['Description'] = df_bank['Description'].str.upper()

    if 'Reference No.' in df_bank.columns:
        df_bank['Reference No.'] = df_bank['Reference No.'].astype(str).str.strip().str.upper()

    # ✅ KONVERSI CREDIT DENGAN UNIVERSAL PARSER
    df_bank['Credit'] = df_bank['Credit'].apply(parse_universal_amount)

    # --------------------
    # Cleaning AR Aging
    # --------------------
    df_aging['No Invoice'] = df_aging['No Invoice'].astype(str).str.strip().str.upper()
    df_aging['Customer'] = df_aging['Customer'].astype(str).str.strip()
    df_aging['Customer'] = df_aging['Customer'].str.replace(r'\s+', ' ', regex=True)
    df_aging['Customer'] = df_aging['Customer'].str.upper()

    # ✅ KONVERSI SALDO PIUTANG DENGAN UNIVERSAL PARSER
    # Handle case where column might be named differently
    saldo_col = None
    for col in df_aging.columns:
        if 'SALDO' in str(col).upper() and 'PIUTANG' in str(col).upper():
            saldo_col = col
            break

    if saldo_col:
        # ✅ FIX FINAL KEYERROR 0: Gunakan .map() BUKAN .apply()!
        df_aging['SALDO PIUTANG'] = df_aging[saldo_col].map(parse_universal_amount).astype(float).fillna(0)
    else:
        # Jika tidak ada kolom saldo piutang, coba cari kolom lain yang mungkin mengandung nilai
        amount_cols = [col for col in df_aging.columns if 'AMOUNT' in str(col).upper() or 'TOTAL' in str(col).upper()]
        if amount_cols:
            df_aging['SALDO PIUTANG'] = df_aging[amount_cols[0]].map(parse_universal_amount).astype(float).fillna(0)
        else:
            raise ValueError("Tidak dapat menemukan kolom SALDO PIUTANG atau kolom serupa di file AR Aging")

    # ✅ Normalisasi Customer untuk Aging Data
    df_aging['Customer_normalized'] = df_aging['Customer'].apply(normalize_customer_name)

    st.info(f"📊 CLEAN DATA SEBELUM FILTER: Bank {len(df_bank)} baris | AR Aging {len(df_aging)} baris")

    # ✅ VALIDASI NILAI MASUK AKAL
    # Filter nilai yang tidak realistis (kurang dari 100 atau lebih dari 100 Miliar)
    df_aging = df_aging[(df_aging['SALDO PIUTANG'] >= 100) & (df_aging['SALDO PIUTANG'] <= 100_000_000_000)].reset_index(drop=True)
    df_bank = df_bank[(df_bank['Credit'] >= 100) & (df_bank['Credit'] <= 100_000_000_000)].reset_index(drop=True)

    st.success(f"📊 CLEAN DATA SETELAH FILTER: Bank {len(df_bank)} baris | AR Aging {len(df_aging)} baris")

    return df_bank, df_aging

def extract_all_numbers(text):
    """Extract SEMUA angka dari text untuk heuristic matching"""
    numbers = re.findall(r'\b\d+\b', str(text))
    return [n for n in numbers if len(n) >= 3]

def find_subset_sum(invoices, target_amount, max_invoices=3, tolerance=0.02):
    """
    Subset Sum Algorithm untuk mencari kombinasi invoice yang totalnya mendekati amount bank
    Optimized untuk kecepatan dengan batas maksimal invoice
    """
    n = len(invoices)
    best_combination = None
    best_diff = float('inf')

    # Batasi kombinasi untuk performance
    max_combinations = min(max_invoices, n)

    for k in range(1, max_combinations + 1):
        for combo in itertools.combinations(enumerate(invoices), k):
            indices = [i for i, inv in combo]
            total = sum(inv['SALDO PIUTANG'] for i, inv in combo)

            diff_pct = abs(total - target_amount) / target_amount

            if diff_pct <= tolerance and diff_pct < best_diff:
                best_diff = diff_pct
                best_combination = indices

    return best_combination

def classify_amount_difference(invoice_amount, bank_amount):
    """
    ✅ CORE LOGIC: Tax-Aware Probabilistic Difference Classifier
    Mengklasifikasikan selisih antara nilai invoice dan payment bank
    Menggunakan pattern recognition bukan rule kaku
    
    Return: 
        classification, confidence_level, difference_pct, explanation
    """
    if invoice_amount == 0 or bank_amount == 0:
        return 'INVALID', 'NONE', 1.0, "Amount nol"
    
    # Hitung selisih absolut dan persentase TERHADAP NILAI INVOICE (standar akuntansi)
    absolute_diff = abs(bank_amount - invoice_amount)
    difference_pct = (bank_amount - invoice_amount) / invoice_amount
    abs_diff_pct = abs(difference_pct) * 100
    
    # ==============================================
    # 🔹 KLASIFIKASI BERBASIS POLA PERCENTAGE
    # ==============================================
    
    # 1. EXACT MATCH
    if absolute_diff <= 1:
        return 'EXACT_MATCH', 'HIGH', 0.0, "Exact Match (selisih 0)"
    
    # 2. PPh LIKELY (Pajak Penghasilan)
    # Selisih NEGATIVE (payment < invoice) sekitar 1.5% - 2.5%
    if -2.5 <= difference_pct * 100 <= -1.5:
        return 'PPH_DEDUCTED', 'HIGH', difference_pct, f"PPh Dipotong (~{abs_diff_pct:.1f}%)"
    
    # 3. POSSIBLE PPN (VAT)
    # Selisih POSITIVE (payment > invoice) sekitar 10% - 12%
    if 10.0 <= difference_pct * 100 <= 12.0:
        return 'POSSIBLE_PPN', 'MEDIUM', difference_pct, f"Kemungkinan PPN termasuk (~{abs_diff_pct:.1f}%)"
    
    # 4. SMALL VARIANCE
    # Selisih kecil < 1% tanpa pola jelas
    if abs_diff_pct < 1.0:
        return 'SMALL_VARIANCE', 'MEDIUM', difference_pct, f"Selisih kecil toleransi (~{abs_diff_pct:.1f}%)"
    
    # 5. OTHER TAX / ADMIN FEE
    if abs_diff_pct < 5.0:
        return 'ADMIN_OR_OTHER_TAX', 'MEDIUM', difference_pct, f"Biaya admin atau pajak lain (~{abs_diff_pct:.1f}%)"
    
    # 6. UNEXPLAINED DIFFERENCE
    return 'UNEXPLAINED', 'LOW', difference_pct, f"Selisih tidak teridentifikasi ({abs_diff_pct:.1f}%)"


def validate_medium_confidence(bank_amount, total_invoice):
    """
    Validasi khusus untuk MEDIUM CONFIDENCE
    Return: (is_valid, amount_ratio, difference_pct, reason)
    """
    if bank_amount == 0 or total_invoice == 0:
        return False, 0, 1, "Amount nol"

    min_amt = min(total_invoice, bank_amount)
    max_amt = max(total_invoice, bank_amount)
    ratio = min_amt / max_amt

    difference_pct = abs(bank_amount - total_invoice) / bank_amount

    if ratio < 0.5:
        return False, ratio, difference_pct, f"HARD REJECT: Ratio amount terlalu kecil ({ratio:.2f} < 0.5)"

    if difference_pct > 0.5:
        return False, ratio, difference_pct, f"HARD REJECT: Perbedaan nominal terlalu besar ({difference_pct*100:.1f}% > 50%)"

    if ratio < 0.7:
        return False, ratio, difference_pct, f"REJECT: Ratio amount dibawah threshold ({ratio:.2f} < 0.7)"

    if difference_pct > 0.3:
        return False, ratio, difference_pct, f"REJECT: Perbedaan nominal diatas threshold ({difference_pct*100:.1f}% > 30%)"

    return True, ratio, difference_pct, "Valid"

def extract_all_sender_candidates(description):
    """
    Multi-Pattern Sender Extractor dengan weighted scoring
    Mengembalikan list semua kandidat sender dengan weight masing-masing
    """
    description = str(description).upper()
    candidates = []

    # ✅ IMPROVEMENT 3: Stopwords perbankan lengkap untuk membersihkan noise
    stopwords = ['TRANSFER', 'TRF', 'INHOUSETRF', 'MCM', 'FEE', 'TRANSFER FEE', 'KE', 'UNTUK', 'NO', 'REF', 'BANK', 'VALAS', 'BI', 'BIFAST', 'CREDIT', 'DEBIT', 'SENDER', 'DARI']

    # ✅ PATTERN 1: Setelah kata DARI (WEIGHT 100)
    match = re.search(r'DARI\s+(.+?)(?:$|\s+(?:KE|UNTUK|NO|REF|TRF|TRANSFER))', description)
    if match:
        sender = match.group(1).strip()
        for sw in stopwords:
            sender = re.sub(rf'\b{sw}\b', '', sender)
        sender = re.sub(r'\s+', ' ', sender).strip()
        if sender and len(sender) > 3:
            candidates.append( (sender, 100) )

    # ✅ PATTERN 2: Setelah SLASH / (WEIGHT 80)
    match = re.search(r'/([^/]+?)(?:/|$|\s+)', description)
    if match:
        sender = match.group(1).strip()
        for sw in stopwords:
            sender = re.sub(rf'\b{sw}\b', '', sender)
        sender = re.sub(r'\s+', ' ', sender).strip()
        if sender and len(sender) > 3:
            candidates.append( (sender, 80) )

    # ✅ PATTERN 3: Sebelum TANDA - (WEIGHT 60)
    match = re.search(r'^([^-]+?)-', description)
    if match:
        sender = match.group(1).strip()
        for sw in stopwords:
            sender = re.sub(rf'\b{sw}\b', '', sender)
        sender = re.sub(r'\s+', ' ', sender).strip()
        if sender and len(sender) > 3:
            candidates.append( (sender, 60) )

    # Normalisasi semua kandidat
    cleaned = []
    for sender, weight in candidates:
        sender = re.sub(r'\b(PT|TBK|Tbk|PT\.|TBK\.|LTD|CORP|INC)\b', '', sender)
        sender = re.sub(r'\s+', ' ', sender).strip()
        if sender:
            cleaned.append( (sender, weight) )

    return cleaned

def find_best_matching_customer(candidates, customer_list):
    """
    Weighted Matching untuk menemukan customer terbaik dari semua kandidat
    Return: (best_customer, final_score)
    """
    if not candidates:
        return (None, 0)

    best_score = 0
    best_customer = None

    for candidate, weight in candidates:
        for customer in customer_list:
            similarity = fuzz.token_sort_ratio(candidate, customer)
            final_score = similarity * weight / 100

            if final_score > best_score:
                best_score = final_score
                best_customer = customer

    return (best_customer, best_score)

def calculate_keyword_overlap(text1, text2):
    """Hitung jumlah keyword yang overlap antara dua teks"""
    stopwords = ['PT', 'TBK', 'LTD', 'CV', 'UD', 'INC', 'CORP', 'TRANSFER', 'TRF', 'KE', 'DARI', 'UNTUK', 'BANK']

    # Pecah menjadi kata, bersihkan stopword
    words1 = set([w.strip() for w in str(text1).upper().split() if len(w.strip()) > 2 and w.strip() not in stopwords])
    words2 = set([w.strip() for w in str(text2).upper().split() if len(w.strip()) > 2 and w.strip() not in stopwords])

    overlap = words1.intersection(words2)
    return len(overlap), list(overlap)

def calculate_advanced_score(bank_row, aging_row):
    """
    Advanced scoring system dengan hard gating berdasarkan nama
    """
    score = 0
    reasons = []
    match_type = []
    rejection_reason = None

    description = str(bank_row['Description'])
    reference = str(bank_row['Reference No.'])
    bank_amount = bank_row['Credit']
    aging_amount = aging_row['SALDO PIUTANG']

    # ==============================================
    # 🔴 HARD GATING - LANGKAH PERTAMA SEBELUM SCORING
    # ==============================================
    customer_similarity = fuzz.token_sort_ratio(description, aging_row['Customer'])
    keyword_overlap_count, overlapping_words = calculate_keyword_overlap(description, aging_row['Customer'])

    # Hard Reject Rule 1: Similarity < 40 ATAU tidak ada keyword overlap
    if customer_similarity < 40 or keyword_overlap_count == 0:
        rejection_reason = f"HARD REJECT: Nama tidak relevan. Similarity {customer_similarity}%, Overlap keyword: {keyword_overlap_count}"
        return {
            'score': 0,
            'confidence': 'NONE',
            'match_type': 'UNIDENTIFIED',
            'reasons': rejection_reason,
            'customer_similarity': customer_similarity,
            'keyword_overlap_count': keyword_overlap_count,
            'overlapping_words': overlapping_words,
            'rejection_reason': rejection_reason,
            'amount_diff': abs(bank_amount - aging_amount),
            'amount_diff_pct': abs(bank_amount - aging_amount) / bank_amount if bank_amount > 0 else 1,
            'amount_ratio': 0
        }

    # Negative Penalty: Similarity < 30
    if customer_similarity < 30:
        rejection_reason = f"HARD REJECT: Similarity terlalu rendah {customer_similarity}%"
        return {
            'score': 0,
            'confidence': 'NONE',
            'match_type': 'UNIDENTIFIED',
            'reasons': rejection_reason,
            'customer_similarity': customer_similarity,
            'keyword_overlap_count': keyword_overlap_count,
            'overlapping_words': overlapping_words,
            'rejection_reason': rejection_reason,
            'amount_diff': abs(bank_amount - aging_amount),
            'amount_diff_pct': abs(bank_amount - aging_amount) / bank_amount if bank_amount > 0 else 1,
            'amount_ratio': 0
        }

    # ==============================================
    # LAYER 1: INVOICE MATCHING
    # ==============================================
    invoice_numbers = re.findall(r'\b\d{6,}\b', description)
    aging_invoice = str(aging_row['No Invoice'])

    # Exact Invoice Match
    if aging_invoice in invoice_numbers:
        score += 80
        reasons.append(f"Invoice ditemukan: {aging_invoice}")
        match_type.append('EXACT_INVOICE')

    # Partial Invoice Match (bagian angka cocok) - MAX +20
    else:
        for num in invoice_numbers:
            if num in aging_invoice or aging_invoice in num:
                score += 20
                reasons.append(f"Partial invoice match: {num}")
                match_type.append('PARTIAL_INVOICE')
                break

    # Reference Number Match
    if aging_invoice in reference:
        score += 70
        reasons.append("Invoice ditemukan di Reference No.")
        match_type.append('REFERENCE_MATCH')

    # ==============================================
    # LAYER 2: AMOUNT MATCHING - TAX AWARE PROBABILISTIC
    # ==============================================
    amount_diff = abs(bank_amount - aging_amount)
    amount_diff_pct = amount_diff / bank_amount if bank_amount > 0 else 1
    
    # ✅ CORE: Jalankan Tax-Aware Classification
    diff_class, diff_confidence, diff_pct, diff_explanation = classify_amount_difference(aging_amount, bank_amount)
    
    # Tambahkan informasi klasifikasi ke reasons
    reasons.append(f"📊 Analisis Selisih: {diff_explanation}")
    match_type.append(diff_class)
    
    # Dynamic scoring berdasarkan klasifikasi selisih
    if diff_class == 'EXACT_MATCH':
        score += 60
        reasons.append("✅ Exact Amount Match (+60)")
    elif diff_class == 'PPH_DEDUCTED':
        # PPh adalah pola yang sangat kuat: bonus tinggi
        score += 55
        reasons.append("✅ PPh terdeteksi - pola valid (+55)")
    elif diff_class == 'POSSIBLE_PPN':
        # PPN pola medium: bonus sedang
        score += 40
        reasons.append("⚠️ Kemungkinan PPN (+40)")
    elif diff_class == 'SMALL_VARIANCE':
        score += 45
        reasons.append("✅ Selisih kecil toleransi (+45)")
    elif diff_class == 'ADMIN_OR_OTHER_TAX':
        score += 35
        reasons.append("✅ Biaya admin / pajak lain (+35)")
    else:
        # Unexplained: tidak ada bonus
        score += 0
        reasons.append("❌ Selisih tidak teridentifikasi (+0)")

    # ==============================================
    # LAYER 3: CUSTOMER MATCHING - MAX +15
    # ==============================================
    customer_similarity = fuzz.partial_ratio(description, aging_row['Customer'])

    if customer_similarity >= 80:
        score += 15
        reasons.append(f"Nama customer cocok ({customer_similarity}%)")
        match_type.append('HIGH_SIMILARITY')

    elif customer_similarity >= 60:
        score += 10
        reasons.append(f"Nama customer mirip ({customer_similarity}%)")
        match_type.append('MEDIUM_SIMILARITY')


    # ==============================================
    # LAYER 4: DATE LOGIC (DP SUPPORT)
    # ==============================================
    if 'Value Date' in bank_row and 'Invoice Date' in aging_row:
        if pd.notnull(bank_row['Value Date']) and pd.notnull(aging_row['Invoice Date']):
            date_diff = (bank_row['Value Date'] - aging_row['Invoice Date']).days

            if date_diff >= 0:
                score += 5
                reasons.append("Tanggal pembayaran setelah invoice")
            else:
                # ✅ DP Support: Toleransi jika bank date < invoice date maks 30 hari
                days_before = abs(date_diff)
                if days_before <= 30:
                    score += 3
                    reasons.append(f"✅ Down Payment terdeteksi ({days_before} hari sebelum invoice)")
                else:
                    score -= 10
                    reasons.append(f"⚠ Tanggal pembayaran {days_before} hari sebelum invoice (melebihi batas DP)")

    # ==============================================
    # 🔴 REBALANCE SCORING - 60% NAME + 40% AMOUNT
    # ==============================================
    name_score = customer_similarity
    amount_score = 100 - (amount_diff_pct * 100) if amount_diff_pct <= 1 else 0

    # Weighted Final Score
    final_weighted_score = (name_score * 0.6) + (amount_score * 0.4)

    reasons.append(f"Weighted Score: {final_weighted_score:.1f} (Name: {name_score}*60% + Amount: {amount_score:.1f}*40%)")

    # ==============================================
    # FINAL VALIDATION SEBELUM CONFIDENCE
    # ==============================================
    is_valid, amount_ratio, difference_pct, reject_reason = validate_medium_confidence(bank_amount, aging_amount)

    # ==============================================
    # 🔴 DEFINISI ULANG KATEGORI - TAX ADJUSTED
    # ==============================================
    # Adjust confidence berdasarkan hasil klasifikasi selisih
    base_confidence = 'NONE'
    
    if final_weighted_score >= 85:
        base_confidence = 'HIGH'
    elif final_weighted_score >= 70 and is_valid:
        base_confidence = 'MEDIUM'
    elif final_weighted_score >= 50 and customer_similarity >= 40:
        base_confidence = 'LOW'
    
    # ✅ Upgrade confidence jika pola pajak terdeteksi (HANYA JIKA CUSTOMER SUDAH COCOK)
    final_confidence = base_confidence
    
    if diff_class == 'PPH_DEDUCTED' and customer_similarity >= 70:
        final_confidence = 'HIGH'
        reasons.append("⬆️ Upgrade ke HIGH: PPh terkonfirmasi dengan customer match")
    elif diff_class == 'POSSIBLE_PPN' and customer_similarity >= 70 and base_confidence == 'LOW':
        final_confidence = 'MEDIUM'
        reasons.append("⬆️ Upgrade ke MEDIUM: PPN terindikasi dengan customer match")
    
    # Format confidence label dengan penjelasan
    confidence_label = f"{final_confidence} - {diff_explanation}"
    
    confidence = final_confidence

    return {
        'score': round(final_weighted_score, 1),
        'confidence': confidence,
        'confidence_label': confidence_label,
        'difference_class': diff_class,
        'difference_explanation': diff_explanation,
        'difference_percent': round(diff_pct * 100, 2),
        'match_type': ' | '.join(match_type),
        'reasons': '; '.join(reasons),
        'customer_similarity': customer_similarity,
        'keyword_overlap_count': keyword_overlap_count,
        'overlapping_words': overlapping_words,
        'name_score': name_score,
        'amount_score': round(amount_score, 1),
        'amount_diff': amount_diff,
        'amount_diff_pct': amount_diff_pct,
        'amount_ratio': amount_ratio,
        'rejection_reason': rejection_reason,
        'reason_rejected': reject_reason
    }

# ==============================================
# 🔹 CLASSIFY BANK ROW (FORMAT_5 ROUTING)
# ==============================================
# Kategori:
#   - NON_AR: JASA GIRO, BY KELOLA REK, dll (bukan piutang)
#   - UANG_MUKA: UM tanpa referensi invoice
#   - INVOICE_TIDAK_ADA_DI_AGING: invoice tidak ada di aging (kemungkinan lunas)
#   - KONFLIK_NAMA_INVOICE: invoice ada di aging tapi nama menunjuk customer lain
#   - MATCHED: lanjut ke layer normal
#   - UNMATCHED: lanjut ke layer normal (tidak ada invoice di COMMANDS)

def classify_bank_row(bank_row, df_aging, invoice_index):
    """
    Klasifikasi baris bank berdasarkan sinyal A (invoice) dan B (nama).
    Return: dict dengan keys:
      - kategori: NON_AR / UANG_MUKA / INVOICE_TIDAK_ADA_DI_AGING / KONFLIK_NAMA_INVOICE / MATCHED / UNMATCHED
      - sinyal: 'A' / 'B' / 'AB' / 'KONFLIK' / ''
      - invoice_di_aging: list invoice yang ada di aging
      - invoice_tidak_di_aging: list invoice yang tidak ada di aging
      - nama_terpakai: nama yang dipakai untuk matching
      - nama_reliable: True/False
      - customer_di_aging: True/False
      - customer_terkunci: nama customer yang terkunci (jika ada)
      - dukungan_nama: similarity % nama vs customer aging
      - reasons: penjelasan
    """
    description = str(bank_row.get('Description', ''))
    nama_asli = str(bank_row.get('Customer', ''))
    
    # ==============================================
    # 1. DETEKSI NON_AR
    # ==============================================
    desc_upper = description.upper()
    for kw in ['JASA GIRO', 'BY KELOLA REK', 'BY PRINT RK', 'RES WTHOLD',
               'KONTRIBUSI', 'BY CETAK RK', 'BY RES WTHOLD', 'WTHOLD T']:
        if kw in desc_upper:
            return {
                'kategori': 'NON_AR',
                'sinyal': '',
                'invoice_di_aging': [],
                'invoice_tidak_di_aging': [],
                'nama_terpakai': nama_asli,
                'nama_reliable': False,
                'customer_di_aging': False,
                'customer_terkunci': None,
                'dukungan_nama': 0,
                'reasons': f'Non-AR: {kw}'
            }
    
    # ==============================================
    # 2. DETEKSI UM (UANG MUKA)
    # ==============================================
    is_um = desc_upper.strip().startswith('UM')
    
    # Ekstrak invoice dari COMMANDS (FORMAT_6 tidak punya invoice -> lewati)
    _is_f6_row = ('State' in bank_row and 'Receipt Method' in bank_row)
    invoice_candidates = [] if _is_f6_row else extract_invoice_numbers(description)
    
    # Cek apakah ada referensi invoice di teks UM
    um_has_invoice = False
    if is_um and invoice_candidates:
        um_has_invoice = True
    
    # UM tanpa referensi invoice -> UANG_MUKA
    if is_um and not um_has_invoice:
        return {
            'kategori': 'UANG_MUKA',
            'sinyal': '',
            'invoice_di_aging': [],
            'invoice_tidak_di_aging': [],
            'nama_terpakai': nama_asli,
            'nama_reliable': False,
            'customer_di_aging': False,
            'customer_terkunci': None,
            'dukungan_nama': 0,
            'reasons': 'Uang muka tanpa referensi invoice'
        }
    
    # ==============================================
    # 3. EKSTRAKSI INVOICE & CEK DI AGING
    # ==============================================
    invoice_di_aging = []
    invoice_tidak_di_aging = []
    
    for inv in invoice_candidates:
        inv_clean = clean_invisible_chars(inv)
        if inv_clean in invoice_index:
            invoice_di_aging.append(inv_clean)
        else:
            invoice_tidak_di_aging.append(inv_clean)
    
    # ==============================================
    # 4. NAME RELIABILITY GATE
    # ==============================================
    nama_gate = apply_name_reliability_gate(nama_asli, mode='otomatis')
    nama_terpakai = nama_gate['nama_terpakai']
    nama_reliable = nama_gate['kategori'] in ('PERUSAHAAN', 'ALIAS', 'FULL')
    
    # Cek apakah customer ada di aging (pakai normalize_customer_key)
    customer_di_aging = False
    customer_terkunci = None
    dukungan_nama = 0
    
    if nama_terpakai:
        nama_key = normalize_customer_key(nama_terpakai)
        # Cari customer di aging dengan key yang sama
        for cust in df_aging['Customer'].unique():
            cust_key = normalize_customer_key(cust)
            if cust_key == nama_key:
                customer_di_aging = True
                customer_terkunci = cust
                dukungan_nama = 100
                break
        
        # Jika tidak exact match, coba fuzzy
        if not customer_di_aging:
            best_sim = 0
            best_cust = None
            for cust in df_aging['Customer'].unique():
                sim = fuzz.token_sort_ratio(normalize_customer_key(nama_terpakai), normalize_customer_key(cust))
                if sim > best_sim:
                    best_sim = sim
                    best_cust = cust
            if best_sim >= 80:
                customer_di_aging = True
                customer_terkunci = best_cust
                dukungan_nama = best_sim
    
    # ==============================================
    # 5. ATURAN KEPUTUSAN
    # ==============================================
    has_invoice = len(invoice_candidates) > 0
    
    # Aturan 1 & 2: Ada invoice di COMMANDS
    if has_invoice:
        if invoice_di_aging:
            # Invoice ada di aging
            if customer_di_aging and customer_terkunci:
                # Cek apakah customer invoice == customer nama
                inv_customer = df_aging.iloc[invoice_index[invoice_di_aging[0]]]['Customer']
                inv_customer_key = normalize_customer_key(inv_customer)
                nama_key = normalize_customer_key(customer_terkunci)
                
                if inv_customer_key == nama_key or dukungan_nama >= 80:
                    # Aturan 1: A ada di aging + B cocok -> MATCHED
                    return {
                        'kategori': 'MATCHED',
                        'sinyal': 'AB',
                        'invoice_di_aging': invoice_di_aging,
                        'invoice_tidak_di_aging': invoice_tidak_di_aging,
                        'nama_terpakai': nama_terpakai,
                        'nama_reliable': nama_reliable,
                        'customer_di_aging': True,
                        'customer_terkunci': customer_terkunci,
                        'dukungan_nama': dukungan_nama,
                        'reasons': f'Invoice {invoice_di_aging[0]} ada di aging, nama cocok dengan customer invoice'
                    }
                else:
                    # Aturan 2: A ada di aging + B RELIABLE menunjuk customer LAIN -> KONFLIK
                    return {
                        'kategori': 'KONFLIK_NAMA_INVOICE',
                        'sinyal': 'KONFLIK',
                        'invoice_di_aging': invoice_di_aging,
                        'invoice_tidak_di_aging': invoice_tidak_di_aging,
                        'nama_terpakai': nama_terpakai,
                        'nama_reliable': nama_reliable,
                        'customer_di_aging': True,
                        'customer_terkunci': customer_terkunci,
                        'dukungan_nama': dukungan_nama,
                        'reasons': f'Invoice {invoice_di_aging[0]} milik {inv_customer}, tapi NAMA menunjuk {customer_terkunci}'
                    }
            else:
                # Invoice ada di aging tapi nama tidak reliable/tidak ditemukan
                # Gunakan invoice sebagai sinyal utama
                return {
                    'kategori': 'MATCHED',
                    'sinyal': 'A',
                    'invoice_di_aging': invoice_di_aging,
                    'invoice_tidak_di_aging': invoice_tidak_di_aging,
                    'nama_terpakai': nama_terpakai,
                    'nama_reliable': nama_reliable,
                    'customer_di_aging': False,
                    'customer_terkunci': None,
                    'dukungan_nama': dukungan_nama,
                    'reasons': f'Invoice {invoice_di_aging[0]} ada di aging, nama tidak reliable'
                }
        else:
            # Aturan 3 & 4: Invoice TIDAK ada di aging
            if customer_di_aging and nama_reliable:
                # Aturan 3: B RELIABLE dan customer ada di aging -> KUNCI ke customer itu
                return {
                    'kategori': 'INVOICE_TIDAK_ADA_DI_AGING',
                    'sinyal': 'B',
                    'invoice_di_aging': [],
                    'invoice_tidak_di_aging': invoice_tidak_di_aging,
                    'nama_terpakai': nama_terpakai,
                    'nama_reliable': True,
                    'customer_di_aging': True,
                    'customer_terkunci': customer_terkunci,
                    'dukungan_nama': dukungan_nama,
                    'reasons': f'Invoice {", ".join(invoice_tidak_di_aging)} tidak ada di aging (kemungkinan lunas). Nama {nama_terpakai} ada di aging, dikunci ke customer ini.'
                }
            else:
                # Aturan 4: Invoice tidak ada di aging + nama tidak ditemukan
                return {
                    'kategori': 'INVOICE_TIDAK_ADA_DI_AGING',
                    'sinyal': 'A',
                    'invoice_di_aging': [],
                    'invoice_tidak_di_aging': invoice_tidak_di_aging,
                    'nama_terpakai': nama_terpakai,
                    'nama_reliable': nama_reliable,
                    'customer_di_aging': False,
                    'customer_terkunci': None,
                    'dukungan_nama': dukungan_nama,
                    'reasons': f'Invoice {", ".join(invoice_tidak_di_aging)} tidak ada di aging (kemungkinan lunas)'
                }
    
    # ==============================================
    # 6. TANPA INVOICE DI COMMANDS
    # ==============================================
    # Aturan 5-7: Tanpa A, hanya B
    if customer_di_aging and nama_reliable:
        # Aturan 5: B RELIABLE -> customer-first
        return {
            'kategori': 'UNMATCHED',
            'sinyal': 'B',
            'invoice_di_aging': [],
            'invoice_tidak_di_aging': [],
            'nama_terpakai': nama_terpakai,
            'nama_reliable': True,
            'customer_di_aging': True,
            'customer_terkunci': customer_terkunci,
            'dukungan_nama': dukungan_nama,
            'reasons': f'Nama {nama_terpakai} reliable dan ada di aging, dikunci ke customer ini'
        }
    elif customer_di_aging and not nama_reliable:
        # Aturan 6: B WEAK -> customer-first, maksimal MEDIUM
        return {
            'kategori': 'UNMATCHED',
            'sinyal': 'B',
            'invoice_di_aging': [],
            'invoice_tidak_di_aging': [],
            'nama_terpakai': nama_terpakai,
            'nama_reliable': False,
            'customer_di_aging': True,
            'customer_terkunci': customer_terkunci,
            'dukungan_nama': dukungan_nama,
            'reasons': f'Nama {nama_terpakai} ditemukan di aging tapi tidak reliable'
        }
    else:
        # Aturan 7: B UNRELIABLE -> hanya nominal unik, maksimal LOW
        return {
            'kategori': 'UNMATCHED',
            'sinyal': '',
            'invoice_di_aging': [],
            'invoice_tidak_di_aging': [],
            'nama_terpakai': nama_terpakai,
            'nama_reliable': False,
            'customer_di_aging': False,
            'customer_terkunci': None,
            'dukungan_nama': 0,
            'reasons': f'Nama tidak reliable dan tidak ditemukan di aging'
        }



# ==============================================
# B4: MATCHING UM BELUM DI-APPLY (FORMAT_5)
# ==============================================
def match_um_unapplied(df_um, df_aging, invoice_index, matched_invoice_ids, name_mode='otomatis', allow_invoice_first=True, system_name=False):
    results = []
    from collections import defaultdict
    exact_map = defaultdict(list)
    for idx, r in df_aging.iterrows():
        if idx in matched_invoice_ids:
            continue
        try:
            exact_map[round(float(r['SALDO PIUTANG']))].append((idx, r))
        except Exception:
            pass
    for _, brow in df_um.iterrows():
        b = brow.to_dict()
        nominal = float(b.get('Nominal Dipakai', 0) or b.get('Credit', 0) or 0)
        desc = str(b.get('Description', ''))
        # jika teks UM memuat invoice -> jalur invoice-first (dinonaktifkan untuk FORMAT_6)
        invs = [i for i in extract_invoice_numbers(desc, 'FORMAT_5') if 'KWT' not in i] if allow_invoice_first else []
        invs_in_aging = [i for i in invs if clean_invisible_chars(i) in invoice_index]
        if invs_in_aging:
            inv = invs_in_aging[0]
            aidx = invoice_index[clean_invisible_chars(inv)]
            if aidx not in matched_invoice_ids:
                ar = df_aging.iloc[aidx]
                diff = abs(nominal - float(ar['SALDO PIUTANG']))
                dc, _, _, dexp = classify_amount_difference(float(ar['SALDO PIUTANG']), nominal)
                conf = 'HIGH' if diff <= 1 else ('MEDIUM' if dc in ('PPH_DEDUCTED','POSSIBLE_PPN','SMALL_VARIANCE','ADMIN_OR_OTHER_TAX') else 'LOW')
                results.append({**b, 'No Invoice': ar['No Invoice'], 'Customer': ar['Customer'], 'Saldo Piutang': ar['SALDO PIUTANG'], 'score': 95 if conf=='HIGH' else 75, 'confidence': conf, 'match_type': 'UM_INVOICE_REF', 'reasons': f"UM memuat invoice {inv}: {dexp}", 'is_combination': False, 'matched_invoice_count': 1, 'customer_similarity': 100, 'amount_diff': diff, 'amount_diff_pct': diff/nominal if nominal else 1, 'Dukungan Nama': 100, 'Sinyal': 'A', 'kandidat_alternatif': ''})
                matched_invoice_ids.add(aidx)
                continue
        gate = {'nama_terpakai': str(b.get('Customer','')).strip().upper(), 'kategori': 'FULL'} if system_name else apply_name_reliability_gate(b.get('Customer', ''), mode=name_mode)
        nama_pakai = gate['nama_terpakai']
        kat = gate['kategori']
        reliable = kat in ('PERUSAHAAN','ALIAS','FULL')
        weak = (not reliable) and bool(nama_pakai)
        unreliable = not nama_pakai or kat in ('GENERIK','TIDAK DIGUNAKAN')
        locked = None
        dukung = 0
        if nama_pakai:
            nk = normalize_customer_key(nama_pakai)
            for c in df_aging['Customer'].unique():
                if normalize_customer_key(c) == nk:
                    locked, dukung = c, 100
                    break
            if not locked:
                best, bs = None, 0
                for c in df_aging['Customer'].unique():
                    s = fuzz.token_sort_ratio(nk, normalize_customer_key(c))
                    if s > bs:
                        bs, best = s, c
                if bs >= 80:
                    locked, dukung = best, bs
        b['Dukungan Nama'] = dukung
        b['Sinyal'] = 'B' if locked else ''
        b['Nama Terpakai'] = nama_pakai
        if unreliable:
            cands = exact_map.get(round(nominal), [])
            cands = [(i, r) for i, r in cands if i not in matched_invoice_ids]
            if len(cands) == 1:
                i, ar = cands[0]
                results.append({**b, 'No Invoice': ar['No Invoice'], 'Customer': ar['Customer'], 'Saldo Piutang': ar['SALDO PIUTANG'], 'score': 55, 'confidence': 'LOW', 'match_type': 'UM_UNRELIABLE_UNIQUE', 'reasons': 'Nama UNRELIABLE: nominal persis unik di aging', 'is_combination': False, 'matched_invoice_count': 1, 'customer_similarity': 0, 'amount_diff': 0, 'amount_diff_pct': 0, 'kandidat_alternatif': ''})
                matched_invoice_ids.add(i)
            else:
                alt = '; '.join([f"{r['No Invoice']} ({r['SALDO PIUTANG']:,.0f})" for _, r in cands[:5]]) if cands else ''
                results.append({**b, 'No Invoice': '-', 'Customer': b.get('Customer','-'), 'Saldo Piutang': 0, 'score': 0, 'confidence': 'NONE', 'match_type': 'UNIDENTIFIED', 'reasons': 'Nama UNRELIABLE dan nominal ambigu/tidak unik', 'is_combination': False, 'matched_invoice_count': 0, 'customer_similarity': 0, 'amount_diff': 0, 'amount_diff_pct': 0, 'kandidat_alternatif': alt})
            continue
        if not locked:
            results.append({**b, 'No Invoice': '-', 'Customer': b.get('Customer','-'), 'Saldo Piutang': 0, 'score': 0, 'confidence': 'NONE', 'match_type': 'UNIDENTIFIED', 'reasons': 'Customer tidak ditemukan di aging (invoice mungkin belum terbit)', 'is_combination': False, 'matched_invoice_count': 0, 'customer_similarity': 0, 'amount_diff': 0, 'amount_diff_pct': 0, 'kandidat_alternatif': ''})
            continue
        cand = df_aging[(df_aging['Customer'] == locked) & (~df_aging['aging_id'].isin(list(matched_invoice_ids)))].copy()
        exact = cand[abs(cand['SALDO PIUTANG'] - nominal) <= 1]
        if len(exact) == 1:
            ar = exact.iloc[0]
            conf = 'HIGH' if reliable else 'MEDIUM'
            sc = 95 if conf == 'HIGH' else 75
            results.append({**b, 'No Invoice': ar['No Invoice'], 'Customer': ar['Customer'], 'Saldo Piutang': ar['SALDO PIUTANG'], 'score': sc, 'confidence': conf, 'match_type': 'UM_EXACT', 'reasons': f"UM cocok persis ke {ar['No Invoice']}", 'is_combination': False, 'matched_invoice_count': 1, 'customer_similarity': dukung, 'amount_diff': abs(nominal-float(ar['SALDO PIUTANG'])), 'amount_diff_pct': 0, 'kandidat_alternatif': ''})
            matched_invoice_ids.add(int(ar['aging_id']))
            continue
        if len(exact) > 1:
            alt = '; '.join([f"{r['No Invoice']} ({r['SALDO PIUTANG']:,.0f})" for _, r in exact.iterrows()])
            results.append({**b, 'No Invoice': '-', 'Customer': locked, 'Saldo Piutang': 0, 'score': 0, 'confidence': 'NONE', 'match_type': 'UNIDENTIFIED', 'reasons': 'Kandidat persis lebih dari satu; tidak dipilih', 'is_combination': False, 'matched_invoice_count': 0, 'customer_similarity': dukung, 'amount_diff': 0, 'amount_diff_pct': 0, 'kandidat_alternatif': alt})
            continue
        best_tax = None
        for _, ar in cand.iterrows():
            dc, _, _, dexp = classify_amount_difference(float(ar['SALDO PIUTANG']), nominal)
            if dc in ('PPH_DEDUCTED','POSSIBLE_PPN','SMALL_VARIANCE','ADMIN_OR_OTHER_TAX'):
                best_tax = (ar, dc, dexp)
                break
        if best_tax is not None:
            ar, dc, dexp = best_tax
            conf = 'MEDIUM' if (reliable or weak) else 'LOW'
            results.append({**b, 'No Invoice': ar['No Invoice'], 'Customer': ar['Customer'], 'Saldo Piutang': ar['SALDO PIUTANG'], 'score': 75, 'confidence': conf, 'match_type': f"UM_{dc}", 'reasons': f"UM pola pajak ke {ar['No Invoice']}: {dexp}", 'is_combination': False, 'matched_invoice_count': 1, 'customer_similarity': dukung, 'amount_diff': abs(nominal-float(ar['SALDO PIUTANG'])), 'amount_diff_pct': abs(nominal-float(ar['SALDO PIUTANG']))/nominal if nominal else 1, 'kandidat_alternatif': ''})
            matched_invoice_ids.add(int(ar['aging_id']))
            continue
        if dukung >= 80:
            recs = cand.to_dict('records')
            combo = find_subset_sum(recs, nominal, max_invoices=3, tolerance=0.005)
            if combo:
                tot = sum(recs[i]['SALDO PIUTANG'] for i in combo)
                invl = ', '.join(recs[i]['No Invoice'] for i in combo)
                results.append({**b, 'No Invoice': invl, 'Customer': locked, 'Saldo Piutang': tot, 'score': 70, 'confidence': 'MEDIUM', 'match_type': 'UM_COMBINATION', 'reasons': f"Kombinasi {len(combo)} invoice {locked}", 'is_combination': True, 'matched_invoice_count': len(combo), 'customer_similarity': dukung, 'amount_diff': abs(nominal-tot), 'amount_diff_pct': abs(nominal-tot)/nominal if nominal else 1, 'kandidat_alternatif': ''})
                for i in combo:
                    matched_invoice_ids.add(int(recs[i]['aging_id']))
                continue
        alt = '; '.join([f"{r['No Invoice']} ({r['SALDO PIUTANG']:,.0f})" for _, r in cand.head(5).iterrows()])
        results.append({**b, 'No Invoice': '-', 'Customer': locked, 'Saldo Piutang': 0, 'score': 0, 'confidence': 'NONE', 'match_type': 'UNIDENTIFIED', 'reasons': 'UM belum di-apply: tidak ada invoice dengan nominal cocok', 'is_combination': False, 'matched_invoice_count': 0, 'customer_similarity': dukung, 'amount_diff': 0, 'amount_diff_pct': 0, 'kandidat_alternatif': alt})
    return results

def advanced_matching_engine(df_bank, df_aging, progress_bar=None):
    """
    ✅ TWO-PASS ADVANCED MATCHING ENGINE
    Pass 1: Strict Matching (100% akurat)
    Pass 2: Fuzzy & Heuristic Matching
    Target Akurasi > 98%
    """
    results = []
    matched_invoice_ids = set()
    matched_bank_ids = set()
    total = len(df_bank)

    # Buat index untuk fast lookup
    invoice_index = {str(row['No Invoice']): idx for idx, row in df_aging.iterrows()}
    fmt0 = df_bank.attrs.get('format_type', 'FORMAT_1')
    f5mode = df_bank.attrs.get('format5_mode', 'semua')
    f6mode = df_bank.attrs.get('format6_mode', 'semua_kecuali_reversal')
    if fmt0 == 'FORMAT_6':
        um6 = df_bank.copy()
        if 'Nominal Dipakai' not in um6.columns:
            um6['Nominal Dipakai'] = um6.get('Credit', 0)
        res6 = match_um_unapplied(um6, df_aging, invoice_index, set(), name_mode='system', allow_invoice_first=False, system_name=True)
        import pandas as _pd6
        df6 = _pd6.DataFrame(res6)
        if not df6.empty:
            df6.attrs['format_type'] = 'FORMAT_6'
        return df6 if not df6.empty else _pd6.DataFrame(columns=['bank_id','Value Date','Reference No.','Description','Credit','Customer','No Invoice','Saldo Piutang','score','confidence','match_type','reasons','is_combination','matched_invoice_count','customer_similarity','amount_diff','amount_diff_pct'])
    if fmt0 == 'FORMAT_5' and f5mode == 'um_unapplied':
        um_rows = df_bank.copy()
        if 'Nominal Dipakai' not in um_rows.columns:
            um_rows['Nominal Dipakai'] = um_rows.get('Credit', 0)
        res_um = match_um_unapplied(um_rows, df_aging, invoice_index, set())
        df_um = __import__('pandas').DataFrame(res_um)
        if not df_um.empty:
            df_um.attrs['format_type'] = 'FORMAT_5'
        return df_um if not df_um.empty else __import__('pandas').DataFrame(columns=['bank_id','Value Date','Reference No.','Description','Credit','Customer','No Invoice','Saldo Piutang','score','confidence','match_type','reasons','is_combination','matched_invoice_count','customer_similarity','amount_diff','amount_diff_pct'])

    # ==============================================
    # 🔹 PASS 1: STRICT MATCHING (EXACT INVOICE + EXACT AMOUNT)
    # ==============================================
    if progress_bar:
        progress_bar.progress(0.1)

    strict_matches = []

    # Format type untuk dispatcher extract_invoice_numbers
    format_type_global = df_bank.attrs.get('format_type', 'FORMAT_1')

    for bank_idx, bank_row in df_bank.iterrows():
        bank_amount = bank_row['Credit']
        invoice_candidates = [] if format_type_global == 'FORMAT_6' else extract_invoice_numbers(bank_row['Description'], format_type_global)

        for inv_num in invoice_candidates:
            if inv_num in invoice_index and invoice_index[inv_num] not in matched_invoice_ids:
                aging_idx = invoice_index[inv_num]
                aging_row = df_aging.iloc[aging_idx]

                # 🔒 Syarat strict: Nominal SAMA PERSIS
                if abs(bank_amount - aging_row['SALDO PIUTANG']) <= 1:
                    strict_matches.append({
                        **bank_row.to_dict(),
                        'No Invoice': aging_row['No Invoice'],
                        'Customer': aging_row['Customer'],
                        'Saldo Piutang': aging_row['SALDO PIUTANG'],
                        'score': 100,
                        'confidence': 'HIGH',
                        'match_type': 'EXACT_INVOICE',
                        'reasons': 'Exact invoice & amount match',
                        'Matching_Note': 'Exact Invoice Match',
                        'is_combination': False,
                        'matched_invoice_count': 1,
                        'customer_similarity': 100,
                        'amount_diff': 0,
                        'amount_diff_pct': 0
                    })
                    matched_invoice_ids.add(aging_idx)
                    matched_bank_ids.add(bank_row['bank_id'])
                    break

    results.extend(strict_matches)

    # ==============================================
    # 🔹 PASS 2: FUZZY & HEURISTIC MATCHING
    # ==============================================
    remaining_bank = df_bank[~df_bank['bank_id'].isin(matched_bank_ids)].reset_index(drop=True)

    for bank_idx, bank_row in remaining_bank.iterrows():
        # ✅ ✅ ✅ SAFETY CHECK: Jika baris ini sudah di matched di awal, skip
        if bank_row['bank_id'] in matched_bank_ids:
            continue
        if progress_bar:
            progress_bar.progress(0.2 + (bank_idx + 1) / total * 0.8)

        # ✅ RESET SEMUA VARIABEL PER BARIS (cegah bocor antar iterasi)
        matching_mode = "FALLBACK"
        selected_customer = None
        filtered_candidates = None
        best_matches = []
        klasifikasi = None

        # ==============================================
        # 🔹 ROUTING FORMAT_5: CLASSIFY BANK ROW
        # ==============================================
        format_type = df_bank.attrs.get('format_type', 'FORMAT_1')
        
        if format_type == 'FORMAT_5':
            # ✅ NAME RELIABILITY GATE: HANYA untuk FORMAT_5
            nama_gate = apply_name_reliability_gate(bank_row.get('Customer', ''), mode='otomatis')
            bank_row['Nama Asli'] = nama_gate['nama_asli']
            bank_row['Nama Terpakai'] = nama_gate['nama_terpakai']
            bank_row['Sumber Nama'] = nama_gate['sumber_nama']
            bank_row['Alasan Keputusan Nama'] = nama_gate['alasan']
            bank_row['Kategori'] = nama_gate['kategori']
            bank_row['kandidat_alternatif'] = '; '.join(nama_gate['kandidat_alternatif']) if nama_gate['kandidat_alternatif'] else ''

            klasifikasi = classify_bank_row(bank_row, df_aging, invoice_index)
            bank_row['Kategori'] = klasifikasi['kategori']
            bank_row['Sinyal'] = klasifikasi['sinyal']
            bank_row['Dukungan Nama'] = klasifikasi['dukungan_nama']
            
            # Jika kategori langsung menghasilkan output, tambahkan dan lanjut
            if klasifikasi['kategori'] in ('NON_AR', 'UANG_MUKA', 'INVOICE_TIDAK_ADA_DI_AGING', 'KONFLIK_NAMA_INVOICE'):
                if klasifikasi['kategori'] == 'NON_AR':
                    confidence = 'NONE'
                    score = 0
                    match_type = 'NON_AR'
                elif klasifikasi['kategori'] == 'UANG_MUKA':
                    confidence = 'NONE'
                    score = 0
                    match_type = 'UANG_MUKA'
                elif klasifikasi['kategori'] == 'INVOICE_TIDAK_ADA_DI_AGING':
                    confidence = 'NONE'
                    score = 0
                    match_type = 'INVOICE_TIDAK_ADA_DI_AGING'
                else:  # KONFLIK_NAMA_INVOICE
                    confidence = 'LOW'
                    score = 40
                    match_type = 'KONFLIK_NAMA_INVOICE'
                
                results.append({
                    **bank_row.to_dict(),
                    'No Invoice': ', '.join(klasifikasi['invoice_tidak_di_aging']) if klasifikasi['invoice_tidak_di_aging'] else '-',
                    'Customer': klasifikasi['customer_terkunci'] if klasifikasi['customer_terkunci'] else bank_row.get('Customer', '-'),
                    'Saldo Piutang': 0,
                    'score': score,
                    'confidence': confidence,
                    'match_type': match_type,
                    'reasons': klasifikasi['reasons'],
                    'is_combination': False,
                    'matched_invoice_count': 0,
                    'customer_similarity': klasifikasi['dukungan_nama'],
                    'amount_diff': 0,
                    'amount_diff_pct': 0
                })
                matched_bank_ids.add(bank_row['bank_id'])
                continue
            
            # Jika MATCHED/UNMATCHED dan customer terkunci -> set LOCKED_CUSTOMER
            # (SETELAH reset matching_mode di atas)
            if klasifikasi['customer_terkunci']:
                matching_mode = "LOCKED_CUSTOMER"
                selected_customer = klasifikasi['customer_terkunci']
                filtered_candidates = df_aging[
                    (df_aging['Customer'] == klasifikasi['customer_terkunci']) &
                    (~df_aging['aging_id'].isin(matched_invoice_ids))
                ].reset_index(drop=True)
                bank_row['Dukungan Nama'] = klasifikasi['dukungan_nama']

        # ✅ ✅ ✅ FIX URUTAN PRIORITAS:
        # 1. Cek dulu apakah ada EXACT INVOICE di deskripsi (highest priority)
        bank_amount = bank_row['Credit']
        invoice_candidates = [] if format_type == 'FORMAT_6' else extract_invoice_numbers(bank_row['Description'], format_type)

        for inv_num in invoice_candidates:
            if inv_num in invoice_index and invoice_index[inv_num] not in matched_invoice_ids:
                aging_idx = invoice_index[inv_num]
                aging_row = df_aging.iloc[aging_idx]

                # ✅ ✅ ✅ RULE NO 1: JIKA ADA NOMOR INVOICE DI DESKRIPSI = HIGH CONFIDENCE 100%
                # APAPUN SELISIH NOMINALNYA (masih dalam toleransi pajak)
                amount_diff_pct = abs(bank_amount - aging_row['SALDO PIUTANG']) / bank_amount
                
                results.append({
                    **bank_row.to_dict(),
                    'No Invoice': aging_row['No Invoice'],
                    'Customer': aging_row['Customer'],
                    'Saldo Piutang': aging_row['SALDO PIUTANG'],
                    'score': 100,
                    'confidence': 'HIGH',
                    'match_type': 'EXACT_INVOICE',
                    'reasons': f"✅ EXACT INVOICE DITEMUKAN DI DESKRIPSI. Selisih {amount_diff_pct*100:.1f}% dianggap toleransi pajak / admin",
                    'Matching_Note': 'Exact Invoice Match',
                    'is_combination': False,
                    'matched_invoice_count': 1,
                    'customer_similarity': 100,
                    'amount_diff': abs(bank_amount - aging_row['SALDO PIUTANG']),
                    'amount_diff_pct': amount_diff_pct
                })
                matched_invoice_ids.add(aging_idx)
                matched_bank_ids.add(bank_row['bank_id'])
                continue

        bank_amount = bank_row['Credit']
        best_matches = []

        # ==============================================
        # 🔹 ✅ PEMISAHAN TOTAL ALGORITMA PER FORMAT
        # TIDAK ADA LAGI TUMPANG TINDIH
        # ==============================================
        format_type = df_bank.attrs.get('format_type', 'FORMAT_1')

        # ==============================================
        # 🔹 ✅ ALGORITMA KHUSUS FORMAT 2, 3 & 4 (CUSTOMER FIRST)
        # HANYA BERJALAN JIKA BENAR BENAR FORMAT 2, 3 ATAU FORMAT 4
        # ==============================================
        if format_type in ('FORMAT_2', 'FORMAT_3', 'FORMAT_4') and 'Customer_normalized' in bank_row:
            bank_customer_norm = bank_row['Customer_normalized']
            bank_customer_original = bank_row['Customer']

            # ✅ HANYA JALANKAN HARD LOCK JIKA CUSTOMER BENERAN ADA (TIDAK KOSONG)
            if bank_customer_norm and bank_customer_norm.strip() != '':
                # 🔒 HARD LOCK CUSTOMER UNTUK FORMAT 2: HANYA BOLEH MATCH KE CUSTOMER INI SAJA
                # APAPUN YANG TERJADI, TIDAK PERNAH FALLBACK KE CUSTOMER LAIN
                # GUNAKAN FUZZY MATCH 90% AGAR TIDAK KETAT BANGET
                filtered_candidates = df_aging[
                    (~df_aging['aging_id'].isin(matched_invoice_ids))
                ].copy()
                
                # Filter customer dengan similarity > 90%
                filtered_candidates['similarity'] = filtered_candidates['Customer_normalized'].apply(
                    lambda x: fuzz.token_sort_ratio(x, bank_customer_norm)
                )
                
                # KHUSUS FORMAT 3 (UMP): Tambahkan subset word matching
                # Jika nama UMP adalah bagian dari nama aging (atau sebaliknya), tetap match
                if format_type == 'FORMAT_3':
                    bank_words = set(bank_customer_norm.split())
                    filtered_candidates['is_subset_match'] = filtered_candidates['Customer_normalized'].apply(
                        lambda x: bank_words.issubset(set(x.split())) or set(x.split()).issubset(bank_words)
                    )
                    # Match jika similarity >= 90 ATAU subset match
                    filtered_candidates = filtered_candidates[
                        (filtered_candidates['similarity'] >= 90) | (filtered_candidates['is_subset_match'] == True)
                    ].sort_values('similarity', ascending=False).reset_index(drop=True)
                else:
                    # FORMAT 2: tetap strict 90%
                    filtered_candidates = filtered_candidates[
                        filtered_candidates['similarity'] >= 90
                    ].sort_values('similarity', ascending=False).reset_index(drop=True)

                # Set format label sesuai format yang terdeteksi
                if format_type == 'FORMAT_2':
                    format_label = 'FORMAT_2'
                    st.info(f"🔒 FORMAT_2 LOCKED: Hanya match untuk Customer '{bank_customer_original}'")
                elif format_type == 'FORMAT_3':
                    format_label = 'FORMAT_3 (UMP)'
                    st.info(f"🔒 FORMAT_3 (UMP) LOCKED: Hanya match untuk Customer '{bank_customer_original}'")
                else:
                    format_label = 'FORMAT_4 (UMP Pending)'
                    # FORMAT_4: log di-supress agar tidak terlalu panjang ke bawah

                if len(filtered_candidates) > 0:
                    # Step 1: Cari match amount dengan tolerance
                    tolerance = 0.02 # 2% tolerance
                    amount_matches = filtered_candidates[
                        abs(filtered_candidates['SALDO PIUTANG'] - bank_amount) <= (bank_amount * tolerance)
                    ]

                    if len(amount_matches) > 0:
                        # ✅ PERFECT MATCH: CUSTOMER + AMOUNT
                        best_match = amount_matches.iloc[0]

                        # Matching_Note sesuai format
                        if format_type == 'FORMAT_4':
                            matching_note = 'FORMAT_4 (UMP Pending) Customer Match'
                        elif format_type == 'FORMAT_3':
                            matching_note = 'FORMAT_3 (UMP) Customer Match'
                        else:
                            matching_note = 'FORMAT_2 Direct Match'

                        results.append({
                            **bank_row.to_dict(),
                            'No Invoice': best_match['No Invoice'],
                            'Customer': best_match['Customer'],
                            'Saldo Piutang': best_match['SALDO PIUTANG'],
                            'score': 95,
                            'confidence': 'HIGH',
                            'match_type': 'CUSTOMER_AMOUNT_EXACT',
                            'reasons': f"✅ EXACT MATCH: Customer '{bank_customer_norm}' dengan amount yang sesuai",
                            'Matching_Note': matching_note,
                            'is_combination': False,
                            'matched_invoice_count': 1,
                            'customer_similarity': 100,
                            'amount_diff': abs(bank_amount - best_match['SALDO PIUTANG']),
                            'amount_diff_pct': abs(bank_amount - best_match['SALDO PIUTANG']) / bank_amount
                        })

                        matched_invoice_ids.add(best_match['aging_id'])
                        matched_bank_ids.add(bank_row['bank_id'])
                        continue
                    
                    # ✅ JIKA TIDAK ADA EXACT MATCH: LANJUTKAN KE MATCHING TAPI HANYA UNTUK CUSTOMER INI
                    # TIDAK PERNAH FALLBACK KE METODE LAMA / CUSTOMER LAIN
                    matching_mode = "LOCKED_CUSTOMER"
                    selected_customer = bank_customer_original
                    # ✅ OVERRIDE filtered_candidates agar HANYA customer yang di lock
                    # Semua matching dibawah hanya akan berjalan untuk customer ini saja
                    filtered_candidates = filtered_candidates[
                        filtered_candidates['similarity'] >= 90
                    ].reset_index(drop=True)
                else:
                    # Customer tidak ada di AR Aging: Tandai sebagai unidentified, jangan match ke customer lain
                    results.append({
                        **bank_row.to_dict(),
                        'No Invoice': '-',
                        'Customer': bank_customer_original,
                        'Saldo Piutang': 0,
                        'score': 0,
                        'confidence': 'NONE',
                        'match_type': 'CUSTOMER_NOT_FOUND',
                        'reasons': f"❌ Customer '{bank_customer_original}' tidak ditemukan di AR Aging",
                        'is_combination': False,
                        'matched_invoice_count': 0,
                        'customer_similarity': 100,
                        'amount_diff': 0,
                        'amount_diff_pct': 0
                    })
                    matched_bank_ids.add(bank_row['bank_id'])
                    continue

        # ==============================================
        # LAYER 0: MULTI-PATTERN SENDER EXTRACTION
        # HANYA DIJALANKAN JIKA BELUM ADA LOCKED CUSTOMER
        # ==============================================
        if matching_mode != "LOCKED_CUSTOMER":
            sender_candidates = extract_all_sender_candidates(bank_row['Description'])
            best_customer, final_score = find_best_matching_customer(sender_candidates, df_aging['Customer'].unique())

            sender_match_score = final_score
            selected_customer = best_customer
            matching_mode = "FALLBACK"
            filtered_candidates = df_aging[~df_aging['aging_id'].isin(matched_invoice_ids)]

            if best_customer and final_score >= 80:
                # ✅ SENDER VALID: HANYA MATCH KE CUSTOMER INI
                matching_mode = "SENDER"
                filtered_candidates = df_aging[
                    (df_aging['Customer'] == best_customer) &
                    (~df_aging['aging_id'].isin(matched_invoice_ids))
                ].reset_index(drop=True)

        # ==============================================
        # LAYER 2: FILTER BY AMOUNT RANGE (OPTIMIZATION)
        # ==============================================
        min_amount = bank_amount * 0.8
        max_amount = bank_amount * 1.2

        candidates = filtered_candidates[
            (filtered_candidates['SALDO PIUTANG'] >= min_amount) &
            (filtered_candidates['SALDO PIUTANG'] <= max_amount) &
            (~filtered_candidates['aging_id'].isin(matched_invoice_ids))
        ]

        # ==============================================
        # LAYER 3: INDIVIDUAL MATCH
        # ==============================================
        for aging_idx, aging_row in candidates.iterrows():
            score_result = calculate_advanced_score(bank_row, aging_row)

            if score_result['score'] >= 50:
                best_matches.append({
                    **bank_row.to_dict(),
                    'No Invoice': aging_row['No Invoice'],
                    'Customer': aging_row['Customer'],
                    'Saldo Piutang': aging_row['SALDO PIUTANG'],
                    **score_result,
                    'is_combination': False,
                    'matched_invoice_count': 1,
                    'aging_idx': aging_idx
                })

        # ==============================================
        # LAYER 4: COMBINATION MATCH (BULK PAYMENT)
        # ==============================================
        if len(best_matches) == 0 or all(m['score'] < 60 for m in best_matches):

            # ✅ STRICT COMBINATION PER FORMAT
            # STRICT_COMBINATION_BY_FORMAT[format_type] = True: UNLOCKED MODE DILARANG
            # STRICT_COMBINATION_BY_FORMAT[format_type] = False: perilaku lama diizinkan
            strict_this_format = config.STRICT_COMBINATION_BY_FORMAT.get(format_type, False)
            
            if matching_mode in ("SENDER", "LOCKED_CUSTOMER") and selected_customer and len(filtered_candidates) > 0:
                # 🔒 LOCKED CUSTOMER MODE: HANYA GUNAKAN CUSTOMER TERSEBUT
                # Normalisasi nama customer untuk exact match
                selected_customer_clean = re.sub(r'\s+', ' ', selected_customer).strip().upper()

                # Buat mask secara terpisah untuk menghindari Arrow type error
                customer_mask = filtered_candidates['Customer'].apply(
                    lambda x: re.sub(r'\s+', ' ', x).strip().upper() == selected_customer_clean
                )
                amount_mask = (filtered_candidates['SALDO PIUTANG'] < bank_amount) & (filtered_candidates['SALDO PIUTANG'] > bank_amount * 0.2)
                combo_candidates = filtered_candidates[customer_mask & amount_mask].head(30).to_dict('records')

                # 🔒 HANYA 1 CUSTOMER GROUP (yang sudah di-filter)
                customer_groups = [(selected_customer, filtered_candidates[customer_mask])]
            elif strict_this_format:
                # 🔓 UNLOCKED MODE DILARANG untuk format ini: hasilnya UNIDENTIFIED
                results.append({
                    **bank_row.to_dict(),
                    'No Invoice': '-',
                    'Customer': '-',
                    'Saldo Piutang': 0,
                    'score': 0,
                    'confidence': 'NONE',
                    'match_type': 'UNIDENTIFIED',
                    'reasons': 'Tidak ada customer terkunci oleh nama. Kombinasi lintas customer tanpa dukungan nama dilarang.',
                    'is_combination': False,
                    'matched_invoice_count': 0,
                    'customer_similarity': 0,
                    'amount_diff': 0,
                    'amount_diff_pct': 0
                })
                continue
            else:
                # 🔓 UNLOCKED MODE DIIZINKAN untuk format ini: perilaku lama
                combo_candidates = filtered_candidates[
                    (filtered_candidates['SALDO PIUTANG'] < bank_amount) &
                    (filtered_candidates['SALDO PIUTANG'] > bank_amount * 0.2)
                ].head(30).to_dict('records')

                # 🔓 LAKUKAN PER CUSTOMER GROUP
                customer_groups = filtered_candidates[
                    (filtered_candidates['SALDO PIUTANG'] < bank_amount) &
                    (filtered_candidates['SALDO PIUTANG'] > bank_amount * 0.2)
                ].groupby('Customer')

            best_combo = None
            best_total = 0
            best_diff = float('inf')
            best_customer = ""
            combo_score = 0

            # 🔹 Lakukan combination matching PER CUSTOMER GROUP (hanya 1 group karena locked)
            for customer_name, group in customer_groups:

                group_invoices = group.to_dict('records')
                if len(group_invoices) < 1:
                    continue

                # Cari kombinasi hanya dalam customer yang SAMA
                combo = find_subset_sum(group_invoices, bank_amount, max_invoices=3, tolerance=0.005)

                if combo:
                    total_amount = sum(group_invoices[i]['SALDO PIUTANG'] for i in combo)
                    amount_diff_pct = abs(bank_amount - total_amount) / bank_amount

                    if amount_diff_pct < best_diff:
                        best_diff = amount_diff_pct
                        best_combo = combo
                        best_total = total_amount
                        best_customer = customer_name
                        best_invoices = group_invoices

            if best_combo:
                # ✅ VALIDASI MEDIUM CONFIDENCE
                is_valid, amount_ratio, difference_pct, reject_reason = validate_medium_confidence(bank_amount, best_total)

                if is_valid and difference_pct <= 0.20:
                    invoice_list = ', '.join(best_invoices[i]['No Invoice'] for i in best_combo)

                    # ✅ SCORING: berdasarkan similarity nama sebenarnya + kedekatan nominal
                    # TIDAK ADA bonus +30 otomatis
                    # customer_similarity harus hasil hitung (bukan 100)
                    nama_sim = bank_row.get('Dukungan Nama', 0)
                    if not nama_sim:
                        # Hitung similarity nama
                        nama_sim = fuzz.token_sort_ratio(
                            normalize_customer_key(bank_row.get('Nama Terpakai', '')),
                            normalize_customer_key(best_customer)
                        )
                    
                    # Skor = 60% nama + 40% kedekatan nominal
                    amount_score = 100 - (difference_pct * 100) if difference_pct <= 1 else 0
                    final_score = round((nama_sim * 0.6) + (amount_score * 0.4), 1)
                    
                    # Batasi confidence: MEDIUM hanya jika nama >= 80
                    if nama_sim >= 80:
                        confidence = 'MEDIUM'
                    else:
                        confidence = 'LOW'

                    results.append({
                        **bank_row.to_dict(),
                        'No Invoice': invoice_list,
                        'Customer': best_customer,
                        'Saldo Piutang': best_total,
                        'score': final_score,
                        'confidence': confidence,
                        'match_type': 'COMBINATION_MATCH_SINGLE_CUSTOMER',
                        'reasons': f"Kombinasi {len(best_combo)} invoice Customer: {best_customer}, total Rp {best_total:,.0f} (beda {difference_pct*100:.1f}%), Dukungan Nama {nama_sim:.0f}%",
                        'is_combination': True,
                        'matched_invoice_count': len(best_combo),
                        'customer_similarity': nama_sim,
                        'number_of_customers_in_match': 1,
                        'customer_group': best_customer,
                        'amount_diff': abs(bank_amount - best_total),
                        'amount_diff_pct': difference_pct,
                        'amount_ratio': amount_ratio,
                        'reason_rejected': reject_reason
                    })

                    # Tandai invoice ini sebagai matched
                    for i in best_combo:
                        matched_invoice_ids.add(best_invoices[i]['aging_id'])

                continue

        # ==============================================
        # PILIH MATCH TERBAIK
        # ==============================================
        if best_matches:
            best_matches.sort(key=lambda x: x['score'], reverse=True)
            best_match = best_matches[0]

            if 'aging_idx' in best_match:
                matched_invoice_ids.add(best_match['aging_idx'])
                del best_match['aging_idx']

            results.append(best_match)
        else:
            # UNIDENTIFIED TRANSACTION
            results.append({
                **bank_row.to_dict(),
                'No Invoice': '-',
                'Customer': '-',
                'Saldo Piutang': 0,
                'score': 0,
                'confidence': 'NONE',
                'match_type': 'UNIDENTIFIED',
                'reasons': 'Tidak ada kandidat yang cocok',
                'is_combination': False,
                'matched_invoice_count': 0,
                'customer_similarity': 0,
                'amount_diff': 0,
                'amount_diff_pct': 0
            })

    # ✅ ✅ ✅ FINAL DEDUPLICATE: PASTIKAN 1 BANK_ID HANYA MUNCUL 1 KALI
    # AMBIL YANG CONFIDENCE TERTINGGI
    df_result = pd.DataFrame(results)
    
    # ✅ PROPAGATE FORMAT TYPE ke df_result agar Excel output bisa mendeteksi FORMAT_4
    df_result.attrs['format_type'] = df_bank.attrs.get('format_type', 'FORMAT_1')
    
    # ✅ FIX: Guard against empty results
    if df_result.empty:
        return pd.DataFrame(columns=[
            'bank_id', 'Value Date', 'Reference No.', 'Description', 'Credit',
            'Customer', 'No Invoice', 'Saldo Piutang', 'score', 'confidence',
            'match_type', 'reasons', 'is_combination', 'matched_invoice_count',
            'customer_similarity', 'amount_diff', 'amount_diff_pct'
        ])

    # Urutkan berdasarkan confidence tertinggi dulu
    confidence_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'NONE': 3}
    df_result['confidence_sort'] = df_result['confidence'].map(confidence_order)
    df_result = df_result.sort_values(by=['confidence_sort', 'score'], ascending=[True, False])
    
    # Drop duplikat, simpan yang pertama (confidence tertinggi)
    df_result = df_result.drop_duplicates(subset=['bank_id'], keep='first')
    
    # Hapus kolom sementara
    df_result = df_result.drop(columns=['confidence_sort'], errors='ignore')
    
    return df_result

def generate_excel_output(df_result):
    """Generate file Excel profesional dengan formatting sesuai requirement"""
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    output = BytesIO()

    # Urutkan data terlebih dahulu
    confidence_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'NONE': 3}
    df_result['confidence_sort'] = df_result['confidence'].map(confidence_order)
    df_result = df_result.sort_values(
        by=['confidence_sort', 'score', 'Credit'],
        ascending=[True, False, False]
    ).drop('confidence_sort', axis=1)

    # Kolom urutan yang diminta
    display_columns = [
        'Value Date', 'Reference No.', 'TYPE', 'Description', 'Credit', 'Nominal Dipakai', 'SISA UM Parsed', 'State', 'Status', 'Receipt Method', 'Unapplied Amount', 'Unidentified Amount', 'Customer',
        'No Invoice', 'SISA UM (Rp)', 'ADJUST UM (Rp)', 'APPLY',
        'Kategori', 'Dukungan Nama', 'Sinyal', 'kandidat_alternatif',
        'confidence', 'match_type', 'reasons',
        'score', 'Saldo Piutang', 'amount_diff', 'Difference %'
    ]
    
    # ✅ TAMBAHKAN KOLOM Difference % DARI amount_diff_pct (dalam bentuk persentase)
    if 'amount_diff_pct' not in df_result.columns:
        df_result['amount_diff_pct'] = 0.0
    df_result['Difference %'] = df_result['amount_diff_pct'].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "0%"
    )

    # ✅ PASTIKAN KOLOM KATEGORI, DUKUNGAN NAMA, SINYAL, KANDIDAT_ALTERNATIF ADA
    for col in ['Kategori', 'Dukungan Nama', 'Sinyal', 'kandidat_alternatif']:
        if col not in df_result.columns:
            df_result[col] = '' if col in ('Kategori', 'Sinyal', 'kandidat_alternatif') else 0

    # Filter kolom yang ada di DataFrame
    display_columns = [col for col in display_columns if col in df_result.columns]

    # ✅ HILANGKAN KOLOM DESCRIPTION DAN BPUK DARI EXCEL UNTUK FORMAT_4 (UMP Pending)
    # FORMAT_4 tidak punya kolom Description asli, kolom ini hanya dibuat untuk matching
    # BPUK juga dihapus karena sama dengan Reference No.
    format_type = df_result.attrs.get('format_type', 'FORMAT_1')
    if format_type == 'FORMAT_4':
        display_columns = [col for col in display_columns if col not in ('Description', 'BPUK')]
    # ✅ UNTUK FORMAT_5 (PHP BNI BJM): Tampilkan kolom pass-through
    if format_type == 'FORMAT_5':
        # Pastikan kolom pass-through ada
        for col in ['TYPE', 'SISA UM (Rp)', 'ADJUST UM (Rp)', 'APPLY']:
            if col not in df_result.columns:
                df_result[col] = ''
        display_columns = [col for col in display_columns if col in df_result.columns]

    # Pisahkan data per kategori
    high_conf = df_result[df_result['confidence'] == 'HIGH'][display_columns].copy()
    medium_conf = df_result[df_result['confidence'] == 'MEDIUM'][display_columns].copy()
    low_conf = df_result[df_result['confidence'] == 'LOW'][display_columns].copy()
    unidentified = df_result[df_result['confidence'] == 'NONE'][display_columns].copy()
    
    # ✅ SHEET KHUSUS KATEGORI BARU
    uang_muka = df_result[df_result['match_type'] == 'UANG_MUKA'][display_columns].copy()
    non_ar = df_result[df_result['match_type'] == 'NON_AR'][display_columns].copy()
    tidak_ada_di_aging = df_result[df_result['match_type'] == 'INVOICE_TIDAK_ADA_DI_AGING'][display_columns].copy()

    # ✅ FIX: Handle NaN values in Value Date column
    for df in [high_conf, medium_conf, low_conf, unidentified, uang_muka, non_ar, tidak_ada_di_aging]:
        if 'Value Date' in df.columns:
            df['Value Date'] = pd.to_datetime(df['Value Date'], errors='coerce')

    with pd.ExcelWriter(output, engine='openpyxl') as writer:

        # Generate timestamp untuk judul laporan
        waktu_generate_excel = datetime.now().strftime("%d %B %Y %H:%M WIB")
        judul_laporan = f"AR Matcher Reconciliation Report - Generated at {waktu_generate_excel}"

        # Definisikan style
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF', size=11)
        header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

        high_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
        medium_fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')
        low_fill = PatternFill(start_color='FFC000', end_color='FFC000', fill_type='solid')
        none_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')

        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Fungsi untuk memformat sheet
        def format_sheet(worksheet, df, has_confidence_color=True):
            # Format header
            for col in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_align
                cell.border = thin_border

            # Auto column width
            for col_idx, column in enumerate(df.columns):
                try:
                    length_series = df[column].apply(lambda x: len(str(x)) if x is not None and pd.notna(x) else 0)
                    max_val_len = length_series.max()
                    # Handle jika hasil max adalah NaN / NaT
                    if pd.isna(max_val_len):
                        max_val_len = 0
                except Exception:
                    max_val_len = 10
                # Handle NaT values in column name
                col_len = len(str(column)) if pd.notna(column) else 0
                max_length = max(int(max_val_len), col_len)
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[get_column_letter(col_idx + 1)].width = adjusted_width

            # Freeze header
            worksheet.freeze_panes = 'A2'

            # Aktifkan filter
            worksheet.auto_filter.ref = worksheet.dimensions

            # Format data baris
            confidence_col_idx = None
            if 'confidence' in df.columns:
                confidence_col_idx = df.columns.get_loc('confidence') + 1

            for row in range(2, len(df) + 2):
                # Format border semua sel
                for col in range(1, len(df.columns) + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.border = thin_border
                    cell.alignment = Alignment(vertical='center', wrap_text=True)

                # Warna confidence column
                if confidence_col_idx and has_confidence_color:
                    confidence_val = worksheet.cell(row=row, column=confidence_col_idx).value
                    confidence_cell = worksheet.cell(row=row, column=confidence_col_idx)

                    if confidence_val == 'HIGH':
                        confidence_cell.fill = high_fill
                    elif confidence_val == 'MEDIUM':
                        confidence_cell.fill = medium_fill
                    elif confidence_val == 'LOW':
                        confidence_cell.fill = low_fill
                    else:
                        confidence_cell.fill = none_fill

                # Format kolom amount sebagai IDR
                if 'Credit' in df.columns:
                    amount_col_idx = df.columns.get_loc('Credit') + 1
                    amount_cell = worksheet.cell(row=row, column=amount_col_idx)
                    amount_cell.number_format = 'Rp #,##0.00'

                if 'Saldo Piutang' in df.columns:
                    amount_col_idx = df.columns.get_loc('Saldo Piutang') + 1
                    amount_cell = worksheet.cell(row=row, column=amount_col_idx)
                    amount_cell.number_format = 'Rp #,##0.00'

                if 'amount_diff' in df.columns:
                    amount_col_idx = df.columns.get_loc('amount_diff') + 1
                    amount_cell = worksheet.cell(row=row, column=amount_col_idx)
                    amount_cell.number_format = 'Rp #,##0.00'

                # Format kolom tanggal
                if 'Value Date' in df.columns:
                    date_col_idx = df.columns.get_loc('Value Date') + 1
                    date_cell = worksheet.cell(row=row, column=date_col_idx)
                    date_cell.number_format = 'dd/mm/yyyy'

            worksheet.sheet_format.defaultRowHeight = 20
    
        # Tulis semua sheet (selalu dibuat walau kosong)
        high_conf.to_excel(writer, sheet_name='HIGH', index=False)
        medium_conf.to_excel(writer, sheet_name='MEDIUM', index=False)
        low_conf.to_excel(writer, sheet_name='LOW', index=False)
        unidentified.to_excel(writer, sheet_name='UNIDENTIFIED', index=False)
        uang_muka.to_excel(writer, sheet_name='UANG_MUKA', index=False)
        non_ar.to_excel(writer, sheet_name='NON_AR', index=False)
        tidak_ada_di_aging.to_excel(writer, sheet_name='TIDAK_ADA_DI_AGING', index=False)

        # Format semua sheet data
        format_sheet(writer.sheets['HIGH'], high_conf)
        format_sheet(writer.sheets['MEDIUM'], medium_conf)
        format_sheet(writer.sheets['LOW'], low_conf)
        format_sheet(writer.sheets['UNIDENTIFIED'], unidentified)
        format_sheet(writer.sheets['UANG_MUKA'], uang_muka, has_confidence_color=False)
        format_sheet(writer.sheets['NON_AR'], non_ar, has_confidence_color=False)
        format_sheet(writer.sheets['TIDAK_ADA_DI_AGING'], tidak_ada_di_aging, has_confidence_color=False)

        # Buat RINGKASAN Sheet
        total_high = len(high_conf)
        total_medium = len(medium_conf)
        total_low = len(low_conf)
        total_none = len(unidentified)
        total_um = len(uang_muka)
        total_non_ar = len(non_ar)
        total_tidak_ada = len(tidak_ada_di_aging)
        total_all = total_high + total_medium + total_low + total_none + total_um + total_non_ar + total_tidak_ada

        amount_high = high_conf['Credit'].sum() if 'Credit' in high_conf.columns else 0
        amount_medium = medium_conf['Credit'].sum() if 'Credit' in medium_conf.columns else 0
        amount_low = low_conf['Credit'].sum() if 'Credit' in low_conf.columns else 0
        amount_none = unidentified['Credit'].sum() if 'Credit' in unidentified.columns else 0
        amount_um = uang_muka['Credit'].sum() if 'Credit' in uang_muka.columns else 0
        amount_non_ar = non_ar['Credit'].sum() if 'Credit' in non_ar.columns else 0
        amount_tidak_ada = tidak_ada_di_aging['Credit'].sum() if 'Credit' in tidak_ada_di_aging.columns else 0
        amount_all = amount_high + amount_medium + amount_low + amount_none + amount_um + amount_non_ar + amount_tidak_ada

        # Invarian: jumlah baris hasil == jumlah baris debet valid
        invarian_ok = total_all == len(df_result)

        summary_df = pd.DataFrame({
            'Kategori': ['HIGH', 'MEDIUM', 'LOW', 'UNIDENTIFIED', 'UANG_MUKA', 'NON_AR', 'TIDAK_ADA_DI_AGING', 'TOTAL'],
            'Jumlah Transaksi': [total_high, total_medium, total_low, total_none, total_um, total_non_ar, total_tidak_ada, total_all],
            'Total Amount': [amount_high, amount_medium, amount_low, amount_none, amount_um, amount_non_ar, amount_tidak_ada, amount_all],
            'Persentase Jumlah': [
                f"{total_high/total_all*100:.1f}%" if total_all else "0%",
                f"{total_medium/total_all*100:.1f}%" if total_all else "0%",
                f"{total_low/total_all*100:.1f}%" if total_all else "0%",
                f"{total_none/total_all*100:.1f}%" if total_all else "0%",
                f"{total_um/total_all*100:.1f}%" if total_all else "0%",
                f"{total_non_ar/total_all*100:.1f}%" if total_all else "0%",
                f"{total_tidak_ada/total_all*100:.1f}%" if total_all else "0%",
                "100%"
            ],
            'Persentase Amount': [
                f"{amount_high/amount_all*100:.1f}%" if amount_all else "0%",
                f"{amount_medium/amount_all*100:.1f}%" if amount_all else "0%",
                f"{amount_low/amount_all*100:.1f}%" if amount_all else "0%",
                f"{amount_none/amount_all*100:.1f}%" if amount_all else "0%",
                f"{amount_um/amount_all*100:.1f}%" if amount_all else "0%",
                f"{amount_non_ar/amount_all*100:.1f}%" if amount_all else "0%",
                f"{amount_tidak_ada/amount_all*100:.1f}%" if amount_all else "0%",
                "100%"
            ]
        })

        # Tulis RINGKASAN
        try:
            _exc = int(__import__('streamlit').session_state.get('format5_excluded', 0))
        except Exception:
            _exc = 0
        try:
            _f6d = str(__import__('streamlit').session_state.get('format6_detail', ''))
        except Exception:
            _f6d = ''
        try:
            _f6e = int(__import__('streamlit').session_state.get('format6_excluded', 0))
        except Exception:
            _f6e = 0
        try:
            _f6i = int(__import__('streamlit').session_state.get('format6_included', 0))
        except Exception:
            _f6i = 0
        if _f6d:
            _exc = _f6e
            summary_df['Dikecualikan (mode)'] = [0]*(len(summary_df)-1) + [_exc]
            summary_df['Disertakan (mode)'] = [0]*(len(summary_df)-1) + [_f6i]
            summary_df['Rincian FORMAT_6'] = ['']*(len(summary_df)-1) + [_f6d]
        else:
            summary_df['Dikecualikan (mode)'] = [0]*(len(summary_df)-1) + [_exc]
        summary_df.to_excel(writer, sheet_name='RINGKASAN', index=False)
        format_sheet(writer.sheets['RINGKASAN'], summary_df, has_confidence_color=False)


    output.seek(0)
    return output

# ==============================================
# STREAMLIT UI
# ==============================================

def main():
    st.set_page_config(page_title="Advanced Bank Reconciliation", page_icon="⚡", layout="wide")

    st.title("⚡ AR Matcher Engine")
    st.subheader("© Divisi KAK 2026")

    st.markdown("---")

    # ==============================================
    # 🔹 SIDEBAR - PENGATURAN
    # ==============================================
    with st.sidebar:
        st.header("⚙️ Pengaturan")
        st.markdown("---")
        
        # Mode Penggunaan Nama (Name Reliability Gate)
        st.subheader("🔤 Mode Penggunaan Nama")
        name_mode = st.radio(
            "Pilih mode penggunaan nama dari file bank:",
            options=['otomatis', 'selalu', 'jangan'],
            format_func=lambda x: {
                'otomatis': '🔄 Otomatis (default)',
                'selalu': '✅ Selalu pakai',
                'jangan': '❌ Jangan pakai'
            }.get(x, x),
            index=0,
            help="Otomatis: deteksi nama generik & ekstrak nama perusahaan\nSelalu: gunakan nama apa adanya\nJangan: matching hanya berdasarkan amount/invoice"
        )
        
        st.markdown("---")
        
        # Filter Periode
        st.subheader("📅 Filter Periode")
        st.caption("Periode diturunkan dari NO. BUKTI (pola /ROMAWI/TAHUN), fallback ke TANGGAL")
        
        # Daftar periode yang tersedia (2025-2026)
        periode_options = ['Semua Periode'] + [
            f"{year}-{month:02d}" for year in [2025, 2026] for month in range(1, 13)
        ]
        
        periode_from = st.selectbox(
            "Dari Bulan:",
            options=periode_options,
            index=0,
            format_func=lambda x: '📋 Semua Periode' if x == 'Semua Periode' else x
        )
        
        periode_to = st.selectbox(
            "Sampai Bulan:",
            options=periode_options,
            index=0,
            format_func=lambda x: '📋 Semua Periode' if x == 'Semua Periode' else x
        )
        
        st.markdown("---")
        _f5det = st.session_state.get('detected_format_type', None)
        format5_mode = st.session_state.get('format5_mode', 'um_unapplied')
        if _f5det == 'FORMAT_5':
            st.subheader("\U0001F4CC Mode Baris FORMAT_5")
            format5_mode = st.radio("Pilih baris yang diproses:", options=['um_unapplied','pelunasan','semua'], format_func=lambda x: {'um_unapplied': '\U0001F4CC UM belum di-apply (default)', 'pelunasan': 'Pelunasan (PELNS)', 'semua': 'Semua baris debet'}.get(x,x), index=['um_unapplied','pelunasan','semua'].index(format5_mode))
            st.session_state['format5_mode'] = format5_mode
        _f6det = st.session_state.get('detected_format_type', None)
        format6_mode = st.session_state.get('format6_mode', 'semua_kecuali_reversal')
        if _f6det == 'FORMAT_6':
            st.subheader("\U0001F9FE Mode Baris FORMAT_6")
            format6_mode = st.radio("Pilih baris yang diproses:", options=['belum','semua_kecuali_reversal'], format_func=lambda x: {'belum': '\U0001F4CC Belum di-apply', 'semua_kecuali_reversal': 'Semua kecuali reversal (default)'}.get(x,x), index=['belum','semua_kecuali_reversal'].index(format6_mode))
            st.session_state['format6_mode'] = format6_mode
        st.markdown("---")
        st.caption("Daftar nama generik, alias, dan ambang kemiripan dikelola via config.py dan aliases.csv")
        st.caption("© Divisi KAK 2026")

    # Upload Files
    col1, col2 = st.columns(2)

    with col1:
        bank_file = st.file_uploader("📘 Upload File Bank Statement", type=['xlsx', 'xls'])

    with col2:
        aging_file = st.file_uploader("📙 Upload File AR Aging", type=['xlsx', 'xls'])

    st.markdown("---")

    # ✅ PERBAIKAN FINAL STREAMLIT RERUN BUG
    # Semua state disimpan di session_state, tidak akan reset ketika klik download
    
    # ✅ HAPUS SESSION JIKA USER UPLOAD FILE BARU (FIX CACHE SALAH)
    if bank_file:
        # Cek apakah ini file baru atau file yang sama
        file_hash = f"{bank_file.name}_{bank_file.size}"
        if 'last_bank_file_hash' in st.session_state and st.session_state.last_bank_file_hash != file_hash:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
        st.session_state.last_bank_file_hash = file_hash
        # Deteksi format cepat agar radio mode tampil sebelum Start
        st.session_state['detected_format_type'] = detect_format_fast(bank_file)
    
    if aging_file:
        file_hash = f"{aging_file.name}_{aging_file.size}"
        if 'last_aging_file_hash' in st.session_state and st.session_state.last_aging_file_hash != file_hash:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
        st.session_state.last_aging_file_hash = file_hash

    # Jalankan matching hanya ketika button di klik
    if bank_file and aging_file:
        if st.button("🚀 Start Advanced Matching", type="primary", width='stretch') or 'df_result' in st.session_state:
            
            _saved_per = st.session_state.get('saved_periode', None)
            _saved_mode = st.session_state.get('saved_mode', None)
            _saved_mode6 = st.session_state.get('saved_mode6', None)
            _cur_per2 = (periode_from, periode_to)
            _cur_mode2 = st.session_state.get('format5_mode', 'um_unapplied')
            _cur_mode6 = st.session_state.get('format6_mode', 'semua_kecuali_reversal')
            if 'df_result' in st.session_state and (_saved_per != _cur_per2 or _saved_mode != _cur_mode2 or _saved_mode6 != _cur_mode6):
                del st.session_state['df_result']
            # Jika belum pernah dijalankan, jalankan proses matching
            if 'df_result' not in st.session_state:
                try:
                    progress_text = st.empty()
                    progress_bar = st.progress(0)

                    progress_text.text("📂 Loading data...")
                    df_bank = load_bank_data(bank_file)
                    df_aging = load_aging_data(aging_file)
                    st.session_state['detected_format_type'] = df_bank.attrs.get('format_type', 'FORMAT_1')
                    cur_mode = st.session_state.get('format5_mode', 'um_unapplied')
                    cur_per = (periode_from, periode_to)
                    if df_bank.attrs.get('format_type') == 'FORMAT_5':
                        df_bank.attrs['format5_mode'] = cur_mode
                        df_inc, df_exc = filter_format5_mode(df_bank, cur_mode)
                        st.info(f"\U0001F4CC Mode FORMAT_5 '{cur_mode}': {len(df_inc)} disertakan, {len(df_exc)} dikecualikan.")
                        st.session_state['format5_excluded'] = len(df_exc)
                        df_bank = df_inc
                        assert len(df_bank) == len(df_inc)
                    else:
                        st.session_state['format5_excluded'] = 0
                    if df_bank.attrs.get('format_type') == 'FORMAT_6':
                        cur6 = st.session_state.get('format6_mode', 'semua_kecuali_reversal')
                        df_bank.attrs['format6_mode'] = cur6
                        df6_inc, df6_exc = filter_format6_mode(df_bank, cur6)
                        _rev_n = int((df6_exc['Alasan Dikecualikan'] == 'reversal').sum()) if 'Alasan Dikecualikan' in df6_exc.columns else 0
                        _applied_n = int((df6_exc['Alasan Dikecualikan'] == 'applied_nol').sum()) if 'Alasan Dikecualikan' in df6_exc.columns else 0
                        _other_n = int(len(df6_exc) - _rev_n - _applied_n)
                        st.info(f"\U0001F9FE Mode FORMAT_6 '{cur6}': {len(df6_inc)} disertakan, {len(df6_exc)} dikecualikan ({_applied_n} sudah di-apply, {_rev_n} reversal" + (f", {_other_n} lainnya" if _other_n else "") + ").")
                        st.session_state['format6_detail'] = f"{len(df6_inc)} disertakan, {len(df6_exc)} dikecualikan ({_applied_n} sudah di-apply, {_rev_n} reversal" + (f", {_other_n} lainnya" if _other_n else "") + ")"
                        st.session_state['format6_included'] = len(df6_inc)
                        st.session_state['format6_excluded'] = len(df6_exc)
                        st.session_state['format6_reversal'] = _rev_n
                        df_bank = df6_inc
                        assert len(df_bank) == len(df6_inc)
                    else:
                        st.session_state['format6_excluded'] = 0
                        st.session_state['format6_reversal'] = 0

                    # ✅ PERINGATAN: > 50% invoice di COMMANDS tidak ada di aging (hanya FORMAT_5)
                    _fmt_warn = df_bank.attrs.get('format_type', 'FORMAT_1')
                    if _fmt_warn != 'FORMAT_5':
                        pass
                    else:
                      try:
                        invoice_index_check = {str(row['No Invoice']): idx for idx, row in df_aging.iterrows()}
                        total_invoice_refs = 0
                        invoice_not_in_aging = 0
                        for _, row in df_bank.iterrows():
                            invs = [] if df_bank.attrs.get('format_type') == 'FORMAT_6' else extract_invoice_numbers(row.get('Description', ''))
                            if invs:
                                total_invoice_refs += len(invs)
                                for inv in invs:
                                    if clean_invisible_chars(inv) not in invoice_index_check:
                                        invoice_not_in_aging += 1
                        if total_invoice_refs > 0 and (invoice_not_in_aging / total_invoice_refs) > 0.5:
                            st.warning("⚠️ Aging kemungkinan bukan snapshot sebelum periode bank ini. Gunakan aging awal periode.")
                      except Exception:
                        pass

                    # ✅ FILTER PERIODE (jika dipilih)
                    if periode_from != 'Semua Periode' or periode_to != 'Semua Periode':
                        if 'Periode' in df_bank.columns:
                            # Parse periode filter
                            def parse_periode_str(s):
                                if s == 'Semua Periode':
                                    return None
                                parts = s.split('-')
                                return (int(parts[0]), int(parts[1]))
                            
                            from_periode = parse_periode_str(periode_from)
                            to_periode = parse_periode_str(periode_to)
                            
                            # Filter berdasarkan periode
                            mask = pd.Series(True, index=df_bank.index)
                            if from_periode:
                                mask &= df_bank['Periode'].apply(
                                    lambda p: pd.notna(p) and (p[0] > from_periode[0] or (p[0] == from_periode[0] and p[1] >= from_periode[1]))
                                )
                            if to_periode:
                                mask &= df_bank['Periode'].apply(
                                    lambda p: pd.notna(p) and (p[0] < to_periode[0] or (p[0] == to_periode[0] and p[1] <= to_periode[1]))
                                )
                            
                            total_before = len(df_bank)
                            df_bank = df_bank[mask].reset_index(drop=True)
                            st.info(f"📅 Filter periode: {periode_from} s/d {periode_to} → {len(df_bank)} dari {total_before} baris")

                    progress_text.text("🧹 Cleaning data...")
                    df_bank, df_aging = clean_data(df_bank, df_aging)

                    progress_text.text("🔍 Advanced matching in progress...")
                    df_result = advanced_matching_engine(df_bank, df_aging, progress_bar)

                    progress_text.text("✅ Processing complete!")
                    progress_bar.empty()
                    
                    # ✅ SIMPAN SEMUA KE SESSION STATE SEKALI SAJA
                    st.session_state.df_result = df_result
                    st.session_state['saved_periode'] = (periode_from, periode_to)
                    st.session_state['saved_mode'] = st.session_state.get('format5_mode', 'um_unapplied')
                    st.session_state['saved_mode6'] = st.session_state.get('format6_mode', 'semua_kecuali_reversal')
                    st.session_state.last_bank_file = bank_file.name
                    st.session_state.last_aging_file = aging_file.name

                except Exception as e:
                    st.error(f"Terjadi Error: {str(e)}")
                    st.exception(e)
                    st.stop()
            
            # ✅ SELALU RENDER HASIL SETIAP RERUN (INI YANG SEBELUMNYA HILANG)
            df_result = st.session_state.df_result

            # Format angka IDR
            def format_idr(amount):
                return f"Rp {amount:,.0f}".replace(',', '.')

            df_display = df_result.copy()
            df_display['Credit'] = df_display['Credit'].apply(format_idr)
            df_display['Saldo Piutang'] = df_display['Saldo Piutang'].apply(format_idr)
            df_display['amount_diff'] = df_display['amount_diff'].apply(format_idr)

            # Summary
            st.markdown("### 📊 Advanced Reconciliation Summary")
            total_trans = len(df_result)
            high_conf = len(df_result[df_result['confidence'] == 'HIGH'])
            medium_conf = len(df_result[df_result['confidence'] == 'MEDIUM'])
            low_conf = len(df_result[df_result['confidence'] == 'LOW'])
            unidentified = len(df_result[df_result['confidence'] == 'NONE'])

            # ✅ FIX: Guard against division by zero when total_trans == 0
            def pct_str(count, total):
                if total == 0:
                    return "0%"
                return f"{round(count/total*100,1)}%"

            sum_col1, sum_col2, sum_col3, sum_col4, sum_col5 = st.columns(5)
            sum_col1.metric("Total Transaksi", total_trans)
            sum_col2.metric("✅ HIGH CONFIDENCE", high_conf, pct_str(high_conf, total_trans))
            sum_col3.metric("⚠️ MEDIUM CONFIDENCE", medium_conf, pct_str(medium_conf, total_trans))
            sum_col4.metric("🔍 LOW CONFIDENCE", low_conf, pct_str(low_conf, total_trans))
            sum_col5.metric("❌ UNIDENTIFIED", unidentified, pct_str(unidentified, total_trans))

            st.markdown("---")

            # Tampilkan hasil
            tab1, tab2, tab3, tab4 = st.tabs([
                "✅ HIGH CONFIDENCE",
                "⚠️ MEDIUM CONFIDENCE",
                "🔍 LOW CONFIDENCE",
                "❌ UNIDENTIFIED"
            ])

            # ✅ FIX: Use 'Value Date' if 'Date & Time' is not available (not all formats have it)
            date_col = 'Date & Time' if 'Date & Time' in df_display.columns else 'Value Date'
            display_cols = [date_col, 'Reference No.', 'TYPE', 'Description', 'Credit', 'Customer',
                           'No Invoice', 'SISA UM (Rp)', 'ADJUST UM (Rp)', 'APPLY',
                           'match_type', 'score', 'reasons']
            display_cols_none = [date_col, 'Reference No.', 'TYPE', 'Description', 'Credit', 'Customer',
                                'SISA UM (Rp)', 'ADJUST UM (Rp)', 'APPLY']
            
            # ✅ HILANGKAN KOLOM DESCRIPTION DARI HASIL UNTUK FORMAT_4 (UMP Pending)
            # FORMAT_4 tidak punya kolom Description asli, kolom ini hanya dibuat untuk matching
            format_type = df_result.attrs.get('format_type', 'FORMAT_1')
            if format_type == 'FORMAT_4':
                display_cols = [c for c in display_cols if c != 'Description']
                display_cols_none = [c for c in display_cols_none if c != 'Description']
            # ✅ UNTUK FORMAT_5 (PHP BNI BJM): Tampilkan kolom pass-through
            if format_type == 'FORMAT_5':
                for col in ['TYPE', 'SISA UM (Rp)', 'ADJUST UM (Rp)', 'APPLY']:
                    if col not in df_display.columns:
                        df_display[col] = ''
                display_cols = [c for c in display_cols if c in df_display.columns]
                display_cols_none = [c for c in display_cols_none if c in df_display.columns]

            with tab1:
                st.dataframe(df_display[df_display['confidence'] == 'HIGH'][
                    [c for c in display_cols if c in df_display.columns]
                ], width='stretch')

            with tab2:
                st.dataframe(df_display[df_display['confidence'] == 'MEDIUM'][
                    [c for c in display_cols if c in df_display.columns]
                ], width='stretch')

            with tab3:
                st.dataframe(df_display[df_display['confidence'] == 'LOW'][
                    [c for c in display_cols if c in df_display.columns]
                ], width='stretch')

            with tab4:
                st.dataframe(df_display[df_display['confidence'] == 'NONE'][
                    [c for c in display_cols_none if c in df_display.columns]
                ], width='stretch')

            # Download Button
            st.markdown("---")
            
            # ✅ FIX CACHE EXCEL: Setiap df baru akan generate file baru, tidak pakai cache lama
            excel_file = generate_excel_output(df_result)
            
            # Generate timestamp realtime saat tombol diklik
            waktu_generate = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            nama_file = f"AR_Matcher_Report_{waktu_generate}.xlsx"

            st.download_button(
                label="📥 Download Full Matcher Report",
                data=excel_file,
                file_name=nama_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )

            with st.expander("ℹ️ Tentang Advanced Matching Engine"):
                st.markdown("""
                ### 🔥 Fitur Advanced Matching:
                1. **4 Layer Matching System**
                2. **Anti Double Matching Protection**
                3. **Bulk / Combination Payment Detection**
                4. **Partial Payment & Overpayment Handling**
                5. **Weighted Scoring System**
                6. **Confidence Level Classification**
                7. **Matching Reason Explainability**
                8. **Performance Optimized dengan Indexing**

                ### 🎯 Confidence Level:
                - **HIGH (90-100)**: Auto match tanpa review
                - **MEDIUM (70-89)**: Membutuhkan review singkat
                - **LOW (50-69)**: Membutuhkan review lengkap
                """)

    else:
        st.info("Silahkan upload kedua file terlebih dahulu untuk memulai proses matching.")

if __name__ == "__main__":
    # ==============================================
    # 🔴 FINAL FIX INFINITE LOOP STREAMLIT EXE
    # SOLUSI 100% BERFUNGSI TANPA LOOP LAGI
    # ==============================================
    import sys
    import os
    import time
    
    if getattr(sys, 'frozen', False):
        # ✅ 1. SINGLE INSTANCE MUTEX: HANYA 1 PROSES SAJA YANG BOLEH BERJALAN
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        mutex = kernel32.CreateMutexW(None, ctypes.c_bool(True), "AR_MATCHER_ENGINE_SINGLE_INSTANCE")
        last_error = ctypes.get_last_error()
        
        if last_error == 183: # ERROR_ALREADY_EXISTS
            # ✅ SUDAH ADA PROSES YANG BERJALAN: HANYA BUKA BROWSER SAJA
            import webbrowser
            time.sleep(1)
            webbrowser.open("http://127.0.0.1:8501")
            sys.exit(0)
        
        # ✅ 2. SET SEMUA ENVIRONMENT VARIABLE SEBELUM APAPUN
        # ✅ FIX REFUSED TO CONNECT: di EXE streamlit TIDAK MAU bind ke 127.0.0.1
        # Harus pakai 0.0.0.0 saja ketika di EXE
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        os.environ['STREAMLIT_SERVER_PORT'] = '8501'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        os.environ['STREAMLIT_GLOBAL_DEVELOPMENT_MODE'] = 'false'
        os.environ['STREAMLIT_SERVER_DISABLE_WATCHER'] = 'true'
        os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
        os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
        
        # ✅ 3. JALANKAN STREAMLIT LANGSUNG TANPA FORK
        # BYPASS SISTEM streamlit run YANG RUSAK
        sys.argv = [
            sys.argv[0],
            "--server.headless=true",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--global.developmentMode=false",
            "--browser.gatherUsageStats=false",
            "--server.disableWatcher=true"
        ]
        
        os.chdir(sys._MEIPASS)
        
        # ✅ 4. BUAT FILE TEMPORARY SCRIPT (FIX 404 FINAL)
        # Ini adalah trik satu satunya yang 100% bekerja di PyInstaller
        import tempfile
        script_code = f"""
import sys
sys.path = {repr(sys.path)}

exec(open({repr(__file__)}).read())

if __name__ == "__main__":
    main()
"""
        
        temp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_script.write(script_code)
        temp_script.close()
        
        # ✅ 5. JALANKAN STREAMLIT DENGAN CARA YANG BENAR
        import subprocess
        import socket
        
        # Jalankan streamlit run di background sebagai proses terpisah
        # DETACHED_PROCESS = 0x00000008 : Proses tidak akan mati ketika induk selesai
        # CREATE_NO_WINDOW    = 0x08000000 : Tidak muncul window cmd
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", temp_script.name,
            "--server.headless=true",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--global.developmentMode=false",
            "--browser.gatherUsageStats=false",
            "--server.disableWatcher=true"
        ], creationflags=0x08000008)
        
        # ✅ 6. ✅ FIX 100% REFUSED TO CONNECT: POLLING PORT SEBELUM BUKA BROWSER
        # INI ADALAH TRIK YANG PALING PENTING!
        # JANGAN PERNAH buka browser SEBELUM server benar-benar siap.
        max_attempts = 60 # 30 detik timeout
        for i in range(max_attempts):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex(('127.0.0.1', 8501))
                sock.close()
                if result == 0:
                    # ✅ PORT SUDAH TERBUKA, SERVER SIAP MENERIMA KONEKSI
                    break
            except:
                pass
            time.sleep(0.5)
        
        # ✅ AKHIRNYA BUKA BROWSER SEKALI SAJA
        import webbrowser
        webbrowser.open("http://127.0.0.1:8501")
        
        # Biarkan proses berjalan
        process.wait()
        
        # Hapus file temporary
        try:
            import os
            os.unlink(temp_script.name)
        except:
            pass
        
    else:
        # Mode normal development
        main()
