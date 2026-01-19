import json
import re
from typing import List, Dict, Any, Optional
from decimal import Decimal
import httpx

from app.config import get_settings


class OllamaError(Exception):
    """Exception raised when Ollama API call fails"""
    pass


class OllamaUnavailableError(OllamaError):
    """Exception raised when Ollama service is not reachable"""
    pass


ANALYSIS_PROMPT = """You are a financial transaction analyzer. Analyze these bank transactions and identify recurring bills and subscriptions.

CATEGORIES (use exactly these values):
- LOAN: Mortgages, car payments, personal loans, EMI payments
- SUBSCRIPTION: Netflix, Spotify, gym memberships, software subscriptions
- INVESTMENT: SIP, mutual funds, stock purchases, 401k
- INSURANCE: Health, life, auto, home insurance premiums
- UTILITY: Electric, gas, water, internet, phone bills
- OTHER: Anything that doesn't fit above categories

RECURRENCE TYPES (use exactly these values):
- MONTHLY: Occurs once per month (most common for bills)
- WEEKLY: Occurs every week
- BIWEEKLY: Occurs every two weeks
- QUARTERLY: Occurs every 3 months
- ANNUAL: Occurs once per year
- ONETIME: Single occurrence, not recurring

TRANSACTIONS TO ANALYZE:
{transactions_json}

For each unique merchant/payee that appears to be a recurring bill, provide:
1. original_descriptions: Array of matching transaction descriptions
2. suggested_name: Clean, human-readable name (e.g., "Netflix Subscription")
3. category: One of the categories above
4. recurrence: One of the recurrence types above
5. confidence: 0.0 to 1.0 based on how confident you are
6. day_of_month: If monthly/quarterly/annual, the typical day (1-31), null otherwise
7. day_of_week: If weekly/biweekly, the day (0=Monday, 6=Sunday), null otherwise
8. average_amount: Average amount across occurrences

Respond ONLY with valid JSON array. No explanations, just JSON.
Example format:
[
  {{
    "original_descriptions": ["NETFLIX.COM", "NETFLIX MEMBERSHIP"],
    "suggested_name": "Netflix Subscription",
    "category": "SUBSCRIPTION",
    "recurrence": "MONTHLY",
    "confidence": 0.95,
    "day_of_month": 15,
    "day_of_week": null,
    "average_amount": 15.99
  }}
]

Only include transactions that appear to be recurring bills (2+ occurrences or recognizable subscription/bill merchants).
Exclude: one-time purchases, groceries, restaurants, ATM withdrawals, and transfers.

JSON OUTPUT:"""


MARKDOWN_EXTRACTION_PROMPT = """Extract all WITHDRAWAL transactions from this bank statement markdown.

The markdown contains tables with | delimiters and structured sections.

For each withdrawal, return:
- date: YYYY-MM-DD format
- description: Merchant/payee name (cleaned)
- amount: Positive number

BANK STATEMENT:
{markdown}

Return JSON array only:"""


async def call_ollama(prompt: str, model: Optional[str] = None,
                      use_json_format: bool = False) -> str:
    """Call Ollama API and return the response text"""
    settings = get_settings()
    ollama_url = settings.ollama_base_url
    ollama_model = model or settings.ollama_model
    timeout = settings.ollama_timeout

    request_body = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4000
        }
    }

    if use_json_format:
        request_body["format"] = "json"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ollama_url}/api/generate",
                json=request_body,
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
    except httpx.ConnectError:
        raise OllamaUnavailableError("Cannot connect to Ollama. Is it running?")
    except httpx.TimeoutException:
        raise OllamaUnavailableError("Ollama request timed out")
    except httpx.HTTPStatusError as e:
        raise OllamaError(f"Ollama API error: {e.response.status_code}")
    except Exception as e:
        raise OllamaError(f"Ollama error: {str(e)}")


def extract_json_from_response(response: str) -> List[Dict[str, Any]]:
    """Extract JSON array from LLM response, handling markdown code blocks"""
    # Remove markdown code blocks if present
    response = re.sub(r'```json\s*', '', response)
    response = re.sub(r'```\s*', '', response)
    response = response.strip()

    # Try to find JSON array in response
    start_idx = response.find('[')
    end_idx = response.rfind(']')

    if start_idx == -1 or end_idx == -1:
        return []

    json_str = response[start_idx:end_idx + 1]

    try:
        result = json.loads(json_str)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        return []


def validate_analyzed_transaction(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate and normalize an analyzed transaction from LLM"""
    valid_categories = {'LOAN', 'SUBSCRIPTION', 'INVESTMENT', 'INSURANCE', 'UTILITY', 'OTHER'}
    valid_recurrences = {'MONTHLY', 'WEEKLY', 'BIWEEKLY', 'QUARTERLY', 'ANNUAL', 'ONETIME'}

    try:
        # Validate required fields
        if 'suggested_name' not in item or not item['suggested_name']:
            return None
        if 'average_amount' not in item:
            return None

        # Normalize category
        category = str(item.get('category', 'OTHER')).upper()
        if category not in valid_categories:
            category = 'OTHER'

        # Normalize recurrence
        recurrence = str(item.get('recurrence', 'MONTHLY')).upper()
        if recurrence not in valid_recurrences:
            recurrence = 'MONTHLY'

        # Parse amount
        try:
            amount = Decimal(str(item['average_amount']))
            if amount <= 0:
                return None
        except:
            return None

        # Parse confidence
        try:
            confidence = float(item.get('confidence', 0.5))
            confidence = max(0.0, min(1.0, confidence))
        except:
            confidence = 0.5

        # Parse day fields
        day_of_month = None
        day_of_week = None

        if recurrence in ('MONTHLY', 'QUARTERLY', 'ANNUAL'):
            try:
                dom = item.get('day_of_month')
                if dom is not None:
                    day_of_month = int(dom)
                    day_of_month = max(1, min(31, day_of_month))
            except:
                pass
        elif recurrence in ('WEEKLY', 'BIWEEKLY'):
            try:
                dow = item.get('day_of_week')
                if dow is not None:
                    day_of_week = int(dow)
                    day_of_week = max(0, min(6, day_of_week))
            except:
                pass

        # Get original descriptions
        original_descriptions = item.get('original_descriptions', [])
        if isinstance(original_descriptions, str):
            original_descriptions = [original_descriptions]
        elif not isinstance(original_descriptions, list):
            original_descriptions = []

        return {
            'original_descriptions': original_descriptions,
            'suggested_name': str(item['suggested_name'])[:100],
            'category': category,
            'recurrence': recurrence,
            'average_amount': amount,
            'confidence': confidence,
            'day_of_month': day_of_month,
            'day_of_week': day_of_week
        }
    except Exception:
        return None


async def analyze_transactions_with_llm(
    transactions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Use Ollama LLM to analyze transactions and identify recurring bills.

    Args:
        transactions: List of dicts with 'date', 'description', 'amount'

    Returns:
        List of analyzed/categorized transactions
    """
    if not transactions:
        return []

    # Prepare transaction data for prompt
    # Group by description and include counts
    tx_summary = []
    for tx in transactions[:500]:  # Limit to avoid token overflow
        tx_summary.append({
            'date': str(tx.get('date', '')),
            'description': tx.get('description', ''),
            'amount': float(tx.get('amount', 0))
        })

    transactions_json = json.dumps(tx_summary, indent=2)
    prompt = ANALYSIS_PROMPT.format(transactions_json=transactions_json)

    response = await call_ollama(prompt)
    raw_results = extract_json_from_response(response)

    # Validate and normalize results
    validated = []
    for item in raw_results:
        valid = validate_analyzed_transaction(item)
        if valid:
            validated.append(valid)

    return validated


async def extract_transactions_from_markdown(markdown: str) -> List[Dict[str, Any]]:
    """Extract transactions from docling markdown using LLM"""
    prompt = MARKDOWN_EXTRACTION_PROMPT.format(markdown=markdown)
    response = await call_ollama(prompt, use_json_format=True)
    return extract_json_from_response(response)
