import csv
import io
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Dict
import chardet

from app.schemas.import_statement import ParsedTransaction


# Column name patterns for auto-detection
DATE_PATTERNS = [
    r'^date$', r'^trans.*date$', r'^posted.*date$', r'^posting.*date$',
    r'^transaction.*date$', r'^value.*date$', r'^effective.*date$'
]

DESCRIPTION_PATTERNS = [
    r'^description$', r'^memo$', r'^narrative$', r'^details$',
    r'^payee$', r'^merchant$', r'^name$', r'^particulars$',
    r'^transaction.*description$', r'^payment.*details$'
]

AMOUNT_PATTERNS = [
    r'^amount$', r'^value$', r'^transaction.*amount$', r'^sum$'
]

DEBIT_PATTERNS = [
    r'^debit$', r'^withdrawal$', r'^dr$', r'^debit.*amount$', r'^out$'
]

CREDIT_PATTERNS = [
    r'^credit$', r'^deposit$', r'^cr$', r'^credit.*amount$', r'^in$'
]

# Common date formats to try
DATE_FORMATS = [
    '%Y-%m-%d',      # 2024-01-15
    '%m/%d/%Y',      # 01/15/2024
    '%d/%m/%Y',      # 15/01/2024
    '%m-%d-%Y',      # 01-15-2024
    '%d-%m-%Y',      # 15-01-2024
    '%Y/%m/%d',      # 2024/01/15
    '%d %b %Y',      # 15 Jan 2024
    '%b %d, %Y',     # Jan 15, 2024
    '%d-%b-%Y',      # 15-Jan-2024
    '%m/%d/%y',      # 01/15/24
    '%d/%m/%y',      # 15/01/24
]


class CSVParseError(Exception):
    """Exception raised when CSV parsing fails"""
    pass


def detect_encoding(content: bytes) -> str:
    """Detect the encoding of CSV content"""
    result = chardet.detect(content)
    return result.get('encoding', 'utf-8') or 'utf-8'


def match_column(header: str, patterns: List[str]) -> bool:
    """Check if a header matches any of the given patterns"""
    header_lower = header.lower().strip()
    for pattern in patterns:
        if re.match(pattern, header_lower):
            return True
    return False


def detect_columns(headers: List[str]) -> Dict[str, Optional[int]]:
    """Auto-detect column indices based on header names"""
    columns = {
        'date': None,
        'description': None,
        'amount': None,
        'debit': None,
        'credit': None
    }

    for idx, header in enumerate(headers):
        if columns['date'] is None and match_column(header, DATE_PATTERNS):
            columns['date'] = idx
        elif columns['description'] is None and match_column(header, DESCRIPTION_PATTERNS):
            columns['description'] = idx
        elif columns['amount'] is None and match_column(header, AMOUNT_PATTERNS):
            columns['amount'] = idx
        elif columns['debit'] is None and match_column(header, DEBIT_PATTERNS):
            columns['debit'] = idx
        elif columns['credit'] is None and match_column(header, CREDIT_PATTERNS):
            columns['credit'] = idx

    return columns


def parse_date(date_str: str) -> Optional[date]:
    """Try to parse a date string using multiple formats"""
    date_str = date_str.strip()
    if not date_str:
        return None

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def parse_amount(amount_str: str) -> Optional[Decimal]:
    """Parse an amount string to Decimal"""
    if not amount_str:
        return None

    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[^\d.,\-]', '', amount_str.strip())
    if not cleaned:
        return None

    # Handle different decimal separators
    # If both . and , exist, assume last one is decimal separator
    if ',' in cleaned and '.' in cleaned:
        if cleaned.rfind(',') > cleaned.rfind('.'):
            # European format: 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # US format: 1,234.56
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # Could be decimal separator or thousands
        parts = cleaned.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Likely decimal separator
            cleaned = cleaned.replace(',', '.')
        else:
            # Likely thousands separator
            cleaned = cleaned.replace(',', '')

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_csv(content: bytes) -> Tuple[List[ParsedTransaction], List[str]]:
    """
    Parse CSV content and extract transactions.

    Returns:
        Tuple of (transactions, warnings)
    """
    warnings = []
    transactions = []

    # Detect encoding
    encoding = detect_encoding(content)
    try:
        text_content = content.decode(encoding)
    except UnicodeDecodeError:
        text_content = content.decode('utf-8', errors='replace')
        warnings.append(f"Encoding detection failed, used UTF-8 with replacements")

    # Parse CSV
    try:
        # Try to detect dialect
        sample = text_content[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(io.StringIO(text_content), dialect)
        rows = list(reader)
    except csv.Error as e:
        raise CSVParseError(f"Failed to parse CSV: {str(e)}")

    if len(rows) < 2:
        raise CSVParseError("CSV file contains no data rows")

    # Get headers and detect columns
    headers = rows[0]
    columns = detect_columns(headers)

    # Validate required columns
    if columns['date'] is None:
        raise CSVParseError("Could not detect date column. Expected headers like: Date, Transaction Date, Posted Date")

    if columns['description'] is None:
        raise CSVParseError("Could not detect description column. Expected headers like: Description, Memo, Payee")

    has_amount = columns['amount'] is not None
    has_debit_credit = columns['debit'] is not None or columns['credit'] is not None

    if not has_amount and not has_debit_credit:
        raise CSVParseError("Could not detect amount column. Expected headers like: Amount, Debit, Credit")

    # Parse data rows
    skipped_count = 0
    for row_num, row in enumerate(rows[1:], start=2):
        if len(row) <= max(filter(None, columns.values())):
            skipped_count += 1
            continue

        # Parse date
        date_val = parse_date(row[columns['date']])
        if date_val is None:
            skipped_count += 1
            continue

        # Parse description
        description = row[columns['description']].strip()
        if not description:
            skipped_count += 1
            continue

        # Parse amount
        amount = None
        if has_amount:
            amount = parse_amount(row[columns['amount']])
        elif has_debit_credit:
            # Use debit column (outgoing) or negative of credit
            if columns['debit'] is not None:
                debit = parse_amount(row[columns['debit']])
                if debit is not None and debit != 0:
                    amount = abs(debit)
            if amount is None and columns['credit'] is not None:
                credit = parse_amount(row[columns['credit']])
                if credit is not None and credit != 0:
                    # Credits are incoming, we want debits for bills
                    # Skip credits or mark as negative
                    continue

        if amount is None or amount <= 0:
            skipped_count += 1
            continue

        # For unified amount column, filter to only debits (negative or unmarked outgoing)
        if has_amount and not has_debit_credit:
            # If amount is negative, it's typically a debit
            if amount < 0:
                amount = abs(amount)
            # If positive with no debit/credit columns, include it
            # (some banks show all as positive debits)

        transactions.append(ParsedTransaction(
            date=date_val,
            description=description,
            amount=amount,
            original_description=description
        ))

    if skipped_count > 0:
        warnings.append(f"Skipped {skipped_count} rows due to missing or invalid data")

    if not transactions:
        raise CSVParseError("No valid transactions found in CSV")

    # Sort by date
    transactions.sort(key=lambda t: t.date)

    return transactions, warnings
