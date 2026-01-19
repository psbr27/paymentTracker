import io
import os
import re
import tempfile
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Dict, Any
import json

import pdfplumber

from app.schemas.import_statement import ParsedTransaction
from app.services.claude_service import call_claude, extract_json_from_response, ClaudeError


class PDFParseError(Exception):
    """Exception raised when PDF parsing fails"""
    pass


# Common date formats to try
DATE_FORMATS = [
    '%m/%d/%y',      # 10/15/25 (Bank of America format)
    '%m/%d/%Y',      # 01/15/2024
    '%d/%m/%Y',      # 15/01/2024
    '%Y-%m-%d',      # 2024-01-15
    '%m-%d-%Y',      # 01-15-2024
    '%d-%m-%Y',      # 15-01-2024
    '%Y/%m/%d',      # 2024/01/15
    '%d %b %Y',      # 15 Jan 2024
    '%b %d, %Y',     # Jan 15, 2024
    '%d-%b-%Y',      # 15-Jan-2024
    '%d/%m/%y',      # 15/01/24
    '%b %d %Y',      # Jan 15 2024
    '%d %B %Y',      # 15 January 2024
]

# Regex patterns for transaction extraction
# Pattern for Bank of America style: DATE DESCRIPTION AMOUNT
BOA_TRANSACTION_PATTERN = re.compile(
    r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+'  # Date
    r'(.+?)\s+'                         # Description (non-greedy)
    r'(-?[\d,]+\.\d{2})$',              # Amount
    re.MULTILINE
)

# Alternative pattern for amounts at end of line
TRANSACTION_LINE_PATTERN = re.compile(
    r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+'   # Date at start
    r'(.+?)'                            # Description
    r'\s+(-?[\d,]+\.\d{2})\s*$',        # Amount at end
    re.MULTILINE
)

# Pattern to match date at start of line
DATE_START_PATTERN = re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+)', re.MULTILINE)

# Pattern to extract amount from end of text
AMOUNT_PATTERN = re.compile(r'(-?[\d,]+\.\d{2})\s*$')


PDF_TEXT_EXTRACTION_PROMPT = """You are a bank statement parser. Extract all WITHDRAWAL/DEBIT transactions from the following bank statement text.

For each withdrawal transaction, extract:
- date: The transaction date (format: YYYY-MM-DD)
- description: The merchant/payee name (simplified, e.g., "DUKEENERGY" becomes "Duke Energy", "T-MOBILE" becomes "T-Mobile")
- amount: The transaction amount as a POSITIVE number

IMPORTANT:
- Only extract WITHDRAWALS (money going out) - these typically have negative amounts or are listed under "Withdrawals"
- DO NOT include deposits or credits
- Simplify merchant names to be human-readable
- Return ONLY a valid JSON array, no explanations
- If you cannot find any transactions, return an empty array []

BANK STATEMENT TEXT:
{statement_text}

JSON OUTPUT (array of {{date, description, amount}}):"""


def parse_date(date_str: str) -> Optional[date]:
    """Try to parse a date string using multiple formats"""
    if not date_str:
        return None

    date_str = date_str.strip()

    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # Handle 2-digit years
            if parsed.year < 100:
                if parsed.year > 50:
                    parsed = parsed.replace(year=1900 + parsed.year)
                else:
                    parsed = parsed.replace(year=2000 + parsed.year)
            return parsed.date()
        except ValueError:
            continue

    return None


def parse_amount(amount_str: str) -> Optional[Decimal]:
    """Parse an amount string to Decimal"""
    if not amount_str:
        return None

    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[^\d.,\-]', '', str(amount_str).strip())
    if not cleaned:
        return None

    # Handle different decimal separators
    if ',' in cleaned and '.' in cleaned:
        if cleaned.rfind(',') > cleaned.rfind('.'):
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        parts = cleaned.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def clean_description(desc: str) -> str:
    """Clean up a transaction description"""
    # Remove common bank codes
    desc = re.sub(r'\s+DES:\w+', ' ', desc)
    desc = re.sub(r'\s+ID:[\w\d]+', ' ', desc)
    desc = re.sub(r'\s+INDN:[\w\s]+', ' ', desc)
    desc = re.sub(r'\s+CO\s+ID:[\w\d]+', ' ', desc)
    desc = re.sub(r'\s+(WEB|PPD|CCD)(\s|$)', ' ', desc)
    desc = re.sub(r'\s+PMT\s+INFO:.*', '', desc)
    desc = re.sub(r'\s+Conf#\s*\w+', '', desc)
    desc = re.sub(r'\d{10,}', '', desc)  # Remove long numbers
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc[:100] if desc else desc


def extract_transactions_from_text_regex(text: str) -> List[ParsedTransaction]:
    """Extract transactions using regex patterns"""
    transactions = []

    # Check if we're in withdrawals section
    in_withdrawals = False
    in_deposits = False

    # Split into lines and process
    lines = text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Track which section we're in
        line_lower = line.lower()
        if 'withdrawal' in line_lower and 'subtraction' in line_lower:
            in_withdrawals = True
            in_deposits = False
            i += 1
            continue
        elif 'deposit' in line_lower and 'addition' in line_lower:
            in_withdrawals = False
            in_deposits = True
            i += 1
            continue
        elif 'service fee' in line_lower or 'total service' in line_lower:
            in_withdrawals = False
            in_deposits = False

        # Try to match transaction pattern
        # Look for date at start
        date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+)', line)

        if date_match:
            date_str = date_match.group(1)
            rest = date_match.group(2)

            # Check if amount is on same line (look for -XXX.XX or XXX.XX at end)
            amount_match = re.search(r'(-?[\d,]+\.\d{2})\s*$', rest)

            if amount_match:
                amount_str = amount_match.group(1)
                description = rest[:amount_match.start()].strip()
            else:
                # Amount might be on next line or description continues
                description = rest
                amount_str = None

                # Look ahead for continuation or amount
                j = i + 1
                while j < len(lines) and j < i + 6:  # Look up to 5 lines ahead
                    next_line = lines[j].strip()

                    # If next line starts with date, stop
                    if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}\s+', next_line):
                        break

                    # If next line is empty, stop
                    if not next_line:
                        break

                    # If next line is a section header, stop
                    if any(x in next_line.lower() for x in ['total ', 'continued', 'service fee', 'page ']):
                        break

                    # Check if line is ONLY an amount (standalone amount line)
                    standalone_amount = re.match(r'^(-?[\d,]+\.\d{2})\s*$', next_line)
                    if standalone_amount:
                        amount_str = standalone_amount.group(1)
                        j += 1
                        break

                    # Check for amount at end of line
                    amount_match = re.search(r'(-?[\d,]+\.\d{2})\s*$', next_line)
                    if amount_match:
                        amount_str = amount_match.group(1)
                        # Add text before amount to description
                        prefix = next_line[:amount_match.start()].strip()
                        if prefix:
                            description += ' ' + prefix
                        j += 1
                        break
                    else:
                        # Continuation of description
                        description += ' ' + next_line
                        j += 1

            # Parse date
            date_val = parse_date(date_str)
            if not date_val:
                i += 1
                continue

            # Parse amount
            if amount_str:
                amount = parse_amount(amount_str)
                if amount is not None and amount != 0:
                    # Determine if this is a debit based on section or sign
                    is_debit = False

                    if amount < 0:
                        is_debit = True
                        amount = abs(amount)
                    elif in_withdrawals:
                        is_debit = True
                        amount = abs(amount)

                    if is_debit:
                        # Clean description
                        clean_desc = clean_description(description)

                        if clean_desc:
                            transactions.append(ParsedTransaction(
                                date=date_val,
                                description=clean_desc,
                                amount=amount,
                                original_description=description[:200]
                            ))

        i += 1

    return transactions


def extract_section_text(text: str, section_name: str) -> str:
    """Extract text from a specific section of the statement"""
    # Common section patterns
    patterns = [
        rf'{section_name}\s*\n',
        rf'{section_name}\s*-\s*continued',
    ]

    section_text = ""
    in_section = False

    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower().strip()

        # Check if entering section
        if section_name.lower() in line_lower and ('withdrawal' in line_lower or 'subtraction' in line_lower):
            in_section = True
            continue

        # Check if leaving section
        if in_section:
            if any(x in line_lower for x in ['total withdrawal', 'total subtraction', 'service fee', 'deposits and other', 'checks', 'account summary']):
                if 'total' in line_lower:
                    section_text += line + '\n'
                break
            section_text += line + '\n'

    return section_text


def extract_all_text_from_pdf(content: bytes) -> str:
    """Extract all text from a PDF"""
    text_parts = []

    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        raise PDFParseError(f"Failed to extract text from PDF: {str(e)}")

    return "\n".join(text_parts)


def extract_tables_from_pdf(content: bytes) -> List[List[List[str]]]:
    """Extract all tables from a PDF"""
    all_tables = []

    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if table and len(table) > 1:
                            all_tables.append(table)
    except Exception as e:
        raise PDFParseError(f"Failed to extract tables from PDF: {str(e)}")

    return all_tables


async def extract_transactions_with_llm(text: str) -> Tuple[List[ParsedTransaction], List[str]]:
    """Use LLM to extract transactions from unstructured PDF text"""
    warnings = []

    if not text or len(text.strip()) < 50:
        return [], ["PDF text too short to contain transactions"]

    # Truncate very long text to avoid token limits
    max_chars = 15000
    if len(text) > max_chars:
        text = text[:max_chars]
        warnings.append("PDF text was truncated due to length")

    prompt = PDF_TEXT_EXTRACTION_PROMPT.format(statement_text=text)

    try:
        response = await call_claude(prompt)
        raw_results = extract_json_from_response(response)

        transactions = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue

            date_val = parse_date(str(item.get('date', '')))
            if not date_val:
                continue

            description = str(item.get('description', '')).strip()
            if not description:
                continue

            amount = parse_amount(str(item.get('amount', '')))
            if not amount or amount <= 0:
                continue

            transactions.append(ParsedTransaction(
                date=date_val,
                description=description,
                amount=abs(amount),
                original_description=description
            ))

        if not transactions:
            warnings.append("LLM could not extract transactions from PDF text")

        return transactions, warnings

    except ClaudeError as e:
        return [], [f"LLM extraction failed: {str(e)}"]


async def parse_pdf(content: bytes) -> Tuple[List[ParsedTransaction], List[str]]:
    """
    Parse PDF content and extract transactions.

    Uses a layered approach:
    1. Try regex-based text extraction (fast, works for Bank of America style)
    2. Try table extraction
    3. Fall back to LLM parsing

    Returns:
        Tuple of (transactions, warnings)
    """
    warnings = []
    all_transactions = []

    if not content:
        raise PDFParseError("PDF file is empty")

    # Check if PDF can be opened
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            page_count = len(pdf.pages)
            # Try to access first page to verify it's readable
            if page_count > 0:
                _ = pdf.pages[0].extract_text()
    except Exception as e:
        error_msg = str(e).lower()
        if 'encrypt' in error_msg or 'password' in error_msg:
            raise PDFParseError(
                "PDF is encrypted. Please export an unencrypted version from your bank."
            )
        raise PDFParseError(f"Failed to open PDF: {str(e)}")

    if page_count == 0:
        raise PDFParseError("PDF contains no pages")

    # Extract all text first
    try:
        full_text = extract_all_text_from_pdf(content)
    except PDFParseError:
        raise
    except Exception as e:
        raise PDFParseError(f"Failed to extract text: {str(e)}")

    if not full_text or len(full_text.strip()) < 50:
        raise PDFParseError(
            "Could not extract text from PDF. "
            "The file may be scanned or image-based. "
            "Try exporting as CSV from your bank instead."
        )

    # Layer 1: Try regex-based extraction from text
    try:
        transactions = extract_transactions_from_text_regex(full_text)
        if transactions:
            all_transactions.extend(transactions)
            warnings.append(f"Extracted {len(transactions)} transactions using text parsing")
    except Exception as e:
        warnings.append(f"Text regex extraction failed: {str(e)}")

    # If we got transactions, return them
    if all_transactions:
        all_transactions.sort(key=lambda t: t.date)
        return all_transactions, warnings

    # Layer 2: Try table extraction
    try:
        tables = extract_tables_from_pdf(content)
        if tables:
            warnings.append("Attempting table extraction...")
            for table in tables:
                # Try to find transaction-like rows
                for row in table:
                    if not row or len(row) < 2:
                        continue

                    # Look for date in first column
                    date_val = parse_date(str(row[0] or ''))
                    if not date_val:
                        continue

                    # Get description and amount
                    desc = str(row[1] or '').strip() if len(row) > 1 else ''
                    amount_str = str(row[-1] or '').strip() if row[-1] else ''

                    amount = parse_amount(amount_str)
                    if amount and amount < 0:  # Debit
                        all_transactions.append(ParsedTransaction(
                            date=date_val,
                            description=clean_description(desc),
                            amount=abs(amount),
                            original_description=desc
                        ))
    except Exception as e:
        warnings.append(f"Table extraction failed: {str(e)}")

    if all_transactions:
        all_transactions.sort(key=lambda t: t.date)
        return all_transactions, warnings

    # Layer 3: Fall back to LLM extraction
    warnings.append("Using AI to extract transactions from PDF text")

    try:
        txs, llm_warnings = await extract_transactions_with_llm(full_text)
        all_transactions.extend(txs)
        warnings.extend(llm_warnings)
    except Exception as e:
        warnings.append(f"LLM extraction error: {str(e)}")

    if not all_transactions:
        raise PDFParseError(
            "No transactions found in PDF. "
            "Try exporting as CSV from your bank for better results."
        )

    # Sort by date
    all_transactions.sort(key=lambda t: t.date)

    return all_transactions, warnings
