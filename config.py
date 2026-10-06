"""
AR Matcher - Central Configuration
Semua pengaturan dapat diubah tanpa mengubah kode utama
"""

# ==============================================
# 🔹 NAME RELIABILITY GATE - MODE PENGGUNAAN NAMA
# ==============================================
NAME_RELIABILITY_MODE = 'otomatis'  # 'otomatis' | 'selalu' | 'jangan'
NAME_SIMILARITY_THRESHOLD = 90

# ==============================================
# 🔹 AMOUNT TOLERANCE & CLASSIFICATION
# ==============================================
AMOUNT_TOLERANCE = {
    'EXACT_MATCH': 1,
    'PPH_DEDUCTED': (1.5, 2.5),
    'POSSIBLE_PPN': (10.0, 12.0),
    'SMALL_VARIANCE': 1.0,
    'ADMIN_OR_OTHER_TAX': 5.0
}

# ==============================================
# 🔹 NAME RELIABILITY GATE - KONFIGURASI TAMBAHAN
# ==============================================
ALIASES_CSV_PATH = 'aliases.csv'

GENERIC_NAMES = [
    'KLIEN', 'BPK', 'IBU', 'SDR', 'SDRI', 'BAPAK', 'IBU',
    'KANTOR PUSAT', 'BANK', 'BNI',
    'CUSTOMER', 'PELANGGAN', 'NASABAH', 'REKENING',
    'KANTOR', 'PUSAT', 'CAB', 'CABANG'
]

# ==============================================
# 🔹 FORMAT_5 (PHP BNI BJM) - KONFIGURASI
# ==============================================
FORMAT_5_STRATEGY = 'DEBIT_AS_CREDIT'
FORMAT_5_PASS_THROUGH_COLUMNS = ['TYPE', 'SISA UM (Rp)', 'ADJUST UM (Rp)', 'APPLY']
FORMAT_5_GENERIC_NAMES = [
    'KLIEN', 'BPK', 'IBU', 'SDR', 'SDRI', 'BAPAK',
    'KANTOR PUSAT', 'BANK', 'BNI'
]

# ==============================================
# 🔹 NON-AR KEYWORDS (BUKAN PIUTANG)
# ==============================================
NON_AR_KEYWORDS = [
    'JASA GIRO', 'BY KELOLA REK', 'BY PRINT RK', 'RES WTHOLD',
    'KONTRIBUSI', 'BY CETAK RK', 'BY RES WTHOLD', 'BY KELOLA',
    'JASA GIRO BULAN', 'WTHOLD T'
]

# ==============================================
# 🔹 STRICT COMBINATION (LAYER 4) - PER FORMAT
# ==============================================
# True: UNLOCKED MODE dilarang (kombinasi lintas customer tanpa nama -> UNIDENTIFIED)
# False: perilaku lama diizinkan (UNLOCKED MODE)
STRICT_COMBINATION_BY_FORMAT = {
    "FORMAT_1": False,
    "FORMAT_2": False,
    "FORMAT_3": False,
    "FORMAT_4": False,
    "FORMAT_5": True,
    "FORMAT_FALLBACK": False
}

# Backward compatibility: jika True, semua format strict
STRICT_COMBINATION = True

# Toleransi kombinasi (default 0.5%)
COMBINATION_TOLERANCE = 0.005

# Threshold similarity nama untuk kombinasi
NAME_SIMILARITY_THRESHOLD_COMBO = 80

# Invoice lebih tua dari ini = kandidat lemah
INVOICE_AGE_WEAK_THRESHOLD = 365

# ==============================================
# 🔹 UM (UANG MUKA) DETECTION
# ==============================================
UM_REFERENCE_PATTERN = r'UM.*?(?:INV\.?\s*|PELNS?\s*INV\.?\s*|PELNS?\s*)([A-Z0-9\-/]{8,})'

# ==============================================
# 🔹 INVOICE EXTRACTION
# ==============================================
INVISIBLE_CHARS = ['\u200e', '\u200f', '\u202a', '\u202b', '\u202c', '\u202d', '\u202e']

IGNORE_PATTERNS = [
    r'KWT\.?\s*\d+',
    r'\d{2}-\d{2}-\d{4}',
    r'\d{2}/\d{2}/\d{4}',
]