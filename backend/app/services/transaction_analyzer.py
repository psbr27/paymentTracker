import re
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple, Optional

from app.schemas.import_statement import (
    ParsedTransaction,
    AnalyzedTransaction,
    DateRange
)
from app.services.claude_service import (
    analyze_transactions_with_llm,
    ClaudeUnavailableError,
    ClaudeError,
    AIUsageStats
)


# Keyword patterns for fallback categorization
CATEGORY_KEYWORDS = {
    'LOAN': [
        r'loan', r'mortgage', r'emi', r'finance', r'lending', r'credit.*payment',
        r'car.*payment', r'auto.*loan', r'home.*loan', r'personal.*loan'
    ],
    'SUBSCRIPTION': [
        r'netflix', r'spotify', r'hulu', r'disney', r'hbo', r'amazon.*prime',
        r'apple.*music', r'youtube.*premium', r'gym', r'fitness', r'membership',
        r'subscription', r'adobe', r'microsoft.*365', r'dropbox', r'icloud'
    ],
    'INVESTMENT': [
        r'sip', r'mutual.*fund', r'invest', r'401k', r'etrade', r'fidelity',
        r'vanguard', r'schwab', r'robinhood', r'zerodha', r'groww'
    ],
    'INSURANCE': [
        r'insurance', r'geico', r'state.*farm', r'allstate', r'progressive',
        r'liberty.*mutual', r'lic', r'policy.*premium', r'health.*plan'
    ],
    'UTILITY': [
        r'electric', r'water', r'gas', r'internet', r'comcast', r'verizon',
        r'at&t', r'at.t', r't-mobile', r'tmobile', r'spectrum', r'xfinity',
        r'utility', r'power', r'energy', r'broadband', r'wifi', r'phone.*bill'
    ]
}

# Patterns to exclude (not bills)
EXCLUDE_PATTERNS = [
    r'atm', r'withdrawal', r'transfer', r'payment.*received', r'deposit',
    r'grocery', r'groceries', r'supermarket', r'walmart', r'target',
    r'restaurant', r'cafe', r'coffee', r'starbucks', r'mcdonald',
    r'gas.*station', r'fuel', r'petrol', r'uber', r'lyft', r'taxi',
    r'amazon(?!.*prime)', r'ebay', r'paypal.*transfer', r'venmo', r'zelle'
]


def normalize_description(desc: str) -> str:
    """Normalize a transaction description for grouping"""
    # Convert to lowercase
    normalized = desc.lower().strip()
    # Remove common suffixes like transaction IDs
    normalized = re.sub(r'\s*#?\d{4,}$', '', normalized)
    # Remove dates
    normalized = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', normalized)
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def clean_merchant_name(desc: str) -> str:
    """Clean up a merchant description into a readable name"""
    # Start with the description
    name = desc.strip()

    # Remove common prefixes
    name = re.sub(r'^(pos|ach|wire|check|card|debit|credit)\s+', '', name, flags=re.IGNORECASE)

    # Remove transaction IDs and reference numbers
    name = re.sub(r'\s*#?\d{6,}.*$', '', name)
    name = re.sub(r'\s+ref.*$', '', name, flags=re.IGNORECASE)

    # Remove dates
    name = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', name)

    # Clean up whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    # Title case
    if name:
        name = name.title()

    return name[:100] if name else desc[:100]


def categorize_by_keywords(description: str) -> str:
    """Categorize a transaction based on keywords"""
    desc_lower = description.lower()

    # Check exclusions first
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, desc_lower):
            return ''  # Empty means exclude

    # Check category keywords
    for category, patterns in CATEGORY_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, desc_lower):
                return category

    return 'OTHER'


def detect_recurrence(dates: List[date]) -> Tuple[str, Optional[int], Optional[int]]:
    """
    Detect recurrence pattern from a list of dates.

    Returns:
        (recurrence_type, day_of_month, day_of_week)
    """
    if len(dates) < 2:
        return 'ONETIME', None, None

    dates = sorted(dates)

    # Calculate intervals between consecutive dates
    intervals = []
    for i in range(1, len(dates)):
        delta = (dates[i] - dates[i-1]).days
        intervals.append(delta)

    if not intervals:
        return 'ONETIME', None, None

    avg_interval = sum(intervals) / len(intervals)

    # Determine recurrence based on average interval
    if 5 <= avg_interval <= 9:
        # Weekly
        day_of_week = max(set([d.weekday() for d in dates]), key=[d.weekday() for d in dates].count)
        return 'WEEKLY', None, day_of_week
    elif 12 <= avg_interval <= 16:
        # Biweekly
        day_of_week = max(set([d.weekday() for d in dates]), key=[d.weekday() for d in dates].count)
        return 'BIWEEKLY', None, day_of_week
    elif 25 <= avg_interval <= 35:
        # Monthly
        day_of_month = max(set([d.day for d in dates]), key=[d.day for d in dates].count)
        return 'MONTHLY', day_of_month, None
    elif 85 <= avg_interval <= 100:
        # Quarterly
        day_of_month = max(set([d.day for d in dates]), key=[d.day for d in dates].count)
        return 'QUARTERLY', day_of_month, None
    elif 350 <= avg_interval <= 380:
        # Annual
        day_of_month = dates[0].day
        return 'ANNUAL', day_of_month, None
    else:
        # Default to monthly if unclear
        day_of_month = max(set([d.day for d in dates]), key=[d.day for d in dates].count)
        return 'MONTHLY', day_of_month, None


def group_transactions(
    transactions: List[ParsedTransaction]
) -> Dict[str, List[ParsedTransaction]]:
    """Group transactions by normalized description"""
    groups = defaultdict(list)

    for tx in transactions:
        key = normalize_description(tx.description)
        if key:
            groups[key].append(tx)

    return dict(groups)


def analyze_with_rules(
    transactions: List[ParsedTransaction],
    currency: str = "USD"
) -> List[AnalyzedTransaction]:
    """
    Analyze transactions using rule-based categorization.
    Used as fallback when LLM is unavailable.
    """
    groups = group_transactions(transactions)
    results = []

    for key, txs in groups.items():
        if len(txs) < 1:
            continue

        # Get representative description
        sample_desc = txs[0].description

        # Categorize
        category = categorize_by_keywords(sample_desc)
        if not category:
            # Excluded transaction type
            continue

        # Only include if appears multiple times or is a known bill type
        if len(txs) < 2 and category == 'OTHER':
            continue

        # Detect recurrence
        dates = [tx.date for tx in txs]
        recurrence, day_of_month, day_of_week = detect_recurrence(dates)

        # Calculate average amount
        amounts = [tx.amount for tx in txs]
        avg_amount = sum(amounts) / len(amounts)

        # Get date range
        sorted_dates = sorted(dates)
        date_range = DateRange(first=sorted_dates[0], last=sorted_dates[-1])

        # Confidence based on number of occurrences
        confidence = min(0.9, 0.5 + (len(txs) * 0.1))

        results.append(AnalyzedTransaction(
            id=str(uuid.uuid4())[:8],
            original_descriptions=list(set([tx.original_description for tx in txs])),
            suggested_name=clean_merchant_name(sample_desc),
            category=category,
            recurrence=recurrence,
            day_of_month=day_of_month,
            day_of_week=day_of_week,
            average_amount=Decimal(str(round(avg_amount, 2))),
            currency=currency,
            confidence=confidence,
            occurrence_count=len(txs),
            date_range=date_range
        ))

    # Sort by confidence descending
    results.sort(key=lambda x: x.confidence, reverse=True)

    return results


async def analyze_transactions(
    transactions: List[ParsedTransaction],
    currency: str = "USD"
) -> Tuple[List[AnalyzedTransaction], bool, Optional[AIUsageStats]]:
    """
    Analyze transactions using LLM with fallback to rules.

    Returns:
        Tuple of (analyzed_transactions, used_fallback, ai_usage_stats)
    """
    if not transactions:
        return [], False, None

    # First, group transactions to get metadata
    groups = group_transactions(transactions)

    try:
        # Prepare data for LLM
        tx_dicts = [
            {
                'date': tx.date.isoformat(),
                'description': tx.description,
                'amount': float(tx.amount)
            }
            for tx in transactions
        ]

        llm_results, usage = await analyze_transactions_with_llm(tx_dicts)

        if not llm_results:
            # LLM returned no results, use fallback
            return analyze_with_rules(transactions, currency), True, usage

        # Convert LLM results to AnalyzedTransaction objects
        analyzed = []
        for item in llm_results:
            # Find matching transactions to get occurrence count and date range
            matching_txs = []
            for orig_desc in item.get('original_descriptions', []):
                key = normalize_description(orig_desc)
                if key in groups:
                    matching_txs.extend(groups[key])

            if not matching_txs:
                # Try fuzzy matching
                for key, txs in groups.items():
                    if any(normalize_description(d) in key or key in normalize_description(d)
                           for d in item.get('original_descriptions', [])):
                        matching_txs.extend(txs)

            if not matching_txs:
                matching_txs = transactions[:1]  # Fallback

            dates = sorted([tx.date for tx in matching_txs])
            date_range = DateRange(first=dates[0], last=dates[-1])

            analyzed.append(AnalyzedTransaction(
                id=str(uuid.uuid4())[:8],
                original_descriptions=item.get('original_descriptions', []),
                suggested_name=item['suggested_name'],
                category=item['category'],
                recurrence=item['recurrence'],
                day_of_month=item.get('day_of_month'),
                day_of_week=item.get('day_of_week'),
                average_amount=item['average_amount'],
                currency=currency,
                confidence=item['confidence'],
                occurrence_count=len(matching_txs),
                date_range=date_range
            ))

        return analyzed, False, usage

    except (ClaudeUnavailableError, ClaudeError):
        # Fall back to rule-based analysis
        return analyze_with_rules(transactions, currency), True, None
