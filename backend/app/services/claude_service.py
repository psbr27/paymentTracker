import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from decimal import Decimal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from app.config import get_settings

logger = logging.getLogger(__name__)


class ClaudeError(Exception):
    """Exception raised when Claude API call fails"""
    pass


class ClaudeUnavailableError(ClaudeError):
    """Exception raised when Claude service is not reachable"""
    pass


@dataclass
class AIUsageStats:
    """Statistics from AI API call"""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_estimate": round(self.cost_estimate, 6)
        }


# Pricing per 1M tokens (as of 2024)
CLAUDE_PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.0},
    "default": {"input": 3.0, "output": 15.0}
}


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


STATEMENT_ANALYSIS_PROMPT = """Analyze this bank statement and return comprehensive JSON with this structure:

{{
  "metadata": {{
    "statementPeriod": {{
      "start": "YYYY-MM-DD",
      "end": "YYYY-MM-DD"
    }},
    "accountHolder": "",
    "accountNumber": "",
    "bankName": "",
    "generatedAt": "ISO timestamp"
  }},
  "summary": {{
    "openingBalance": 0,
    "closingBalance": 0,
    "totalCredits": 0,
    "totalDebits": 0,
    "totalFees": 0,
    "netChange": 0
  }},
  "credits": {{
    "byCategory": [
      {{
        "category": "",
        "total": 0,
        "count": 0,
        "transactions": [
          {{
            "id": "unique-id",
            "date": "YYYY-MM-DD",
            "description": "",
            "amount": 0,
            "memo": "",
            "payee": "",
            "method": "ACH|Zelle|Wire|Check|Cash"
          }}
        ]
      }}
    ]
  }},
  "debits": {{
    "byCategory": [
      {{
        "category": "",
        "total": 0,
        "count": 0,
        "transactions": [
          {{
            "id": "unique-id",
            "date": "YYYY-MM-DD",
            "description": "",
            "amount": 0,
            "memo": "",
            "payee": "",
            "method": "ACH|Card|ATM|Check|Zelle",
            "isRecurring": true
          }}
        ]
      }}
    ]
  }},
  "analytics": {{
    "topCategories": [
      {{"category": "", "amount": 0, "percentage": 0}}
    ],
    "recurringPayments": [
      {{"payee": "", "amount": 0, "frequency": "monthly|weekly", "category": ""}}
    ],
    "averageDailyBalance": 0,
    "largestTransaction": {{
      "type": "credit|debit",
      "description": "",
      "amount": 0,
      "date": ""
    }}
  }},
  "flags": {{
    "overdraftEvents": [],
    "unusualActivity": [],
    "fees": []
  }}
}}

**Instructions:**
1. Return ONLY valid, parseable JSON
2. No markdown code blocks or extra text
3. Use consistent date format: YYYY-MM-DD
4. Amounts as numbers (not strings)
5. Identify recurring payments by matching payee names
6. Flag any fees or unusual large transactions
7. Generate unique IDs for each transaction (e.g., "txn-001", "txn-002")

**Categories to use:**
- Income_Payroll
- Mortgage_Rent
- Credit_Cards
- Utilities
- Insurance
- Investments
- Subscriptions
- Shopping
- Travel_Entertainment
- Loans
- Transfers_In
- Transfers_Out
- Cash_Withdrawal
- Fees
- Other

BANK STATEMENT TEXT:
{statement_text}

JSON OUTPUT:"""


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost based on token usage"""
    pricing = CLAUDE_PRICING.get(model, CLAUDE_PRICING["default"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


async def call_claude(prompt: str, use_json_format: bool = False) -> tuple[str, AIUsageStats]:
    """Call Claude API via LangChain and return the response text and usage stats"""
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise ClaudeUnavailableError("ANTHROPIC_API_KEY is not configured")

    try:
        llm = ChatAnthropic(
            model=settings.claude_model,
            api_key=settings.anthropic_api_key,
            max_tokens=settings.claude_max_tokens,
            temperature=settings.claude_temperature,
            timeout=settings.claude_timeout,
        )

        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)

        # Extract token usage from response metadata
        usage = AIUsageStats(model=settings.claude_model)
        if hasattr(response, 'response_metadata') and response.response_metadata:
            metadata = response.response_metadata
            if 'usage' in metadata:
                usage.input_tokens = metadata['usage'].get('input_tokens', 0)
                usage.output_tokens = metadata['usage'].get('output_tokens', 0)
                usage.total_tokens = usage.input_tokens + usage.output_tokens
                usage.cost_estimate = _calculate_cost(
                    settings.claude_model, usage.input_tokens, usage.output_tokens
                )

        # Handle response content - could be string or list of content blocks
        content = response.content
        if isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict) and 'text' in block:
                    text_parts.append(block['text'])
            content = ''.join(text_parts)

        logger.debug(f"Claude response type: {type(response.content)}, content length: {len(content)}")
        return content, usage
    except Exception as e:
        error_str = str(e).lower()
        if 'api key' in error_str or 'authentication' in error_str or 'unauthorized' in error_str:
            raise ClaudeUnavailableError(f"Claude API authentication failed: {str(e)}")
        elif 'timeout' in error_str:
            raise ClaudeUnavailableError("Claude request timed out")
        elif 'connection' in error_str or 'network' in error_str:
            raise ClaudeUnavailableError(f"Cannot connect to Claude API: {str(e)}")
        else:
            raise ClaudeError(f"Claude API error: {str(e)}")


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
) -> tuple[List[Dict[str, Any]], Optional[AIUsageStats]]:
    """
    Use Claude LLM to analyze transactions and identify recurring bills.

    Args:
        transactions: List of dicts with 'date', 'description', 'amount'

    Returns:
        Tuple of (analyzed/categorized transactions, usage stats)
    """
    if not transactions:
        return [], None

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

    response, usage = await call_claude(prompt)
    raw_results = extract_json_from_response(response)

    # Validate and normalize results
    validated = []
    for item in raw_results:
        valid = validate_analyzed_transaction(item)
        if valid:
            validated.append(valid)

    return validated, usage


async def extract_transactions_from_markdown(markdown: str) -> tuple[List[Dict[str, Any]], Optional[AIUsageStats]]:
    """Extract transactions from markdown text using LLM"""
    prompt = MARKDOWN_EXTRACTION_PROMPT.format(markdown=markdown)
    response, usage = await call_claude(prompt)
    return extract_json_from_response(response), usage


def extract_json_object_from_response(response: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from LLM response, handling markdown code blocks"""
    # Remove markdown code blocks if present
    cleaned = re.sub(r'```json\s*', '', response)
    cleaned = re.sub(r'```\s*', '', cleaned)
    cleaned = cleaned.strip()

    # Try to find JSON object in response
    start_idx = cleaned.find('{')
    end_idx = cleaned.rfind('}')

    if start_idx == -1 or end_idx == -1:
        logger.error(f"No JSON object found in response. Response preview: {response[:500]}")
        return None

    json_str = cleaned[start_idx:end_idx + 1]

    try:
        result = json.loads(json_str)
        if isinstance(result, dict):
            return result
        logger.error(f"Parsed JSON is not a dict: {type(result)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}. JSON preview: {json_str[:500]}")
        return None


async def analyze_statement_comprehensive(
    statement_text: str
) -> tuple[Optional[Dict[str, Any]], Optional[AIUsageStats]]:
    """
    Perform comprehensive analysis of a bank statement.

    Args:
        statement_text: Raw text extracted from bank statement PDF/CSV

    Returns:
        Tuple of (analysis_result, usage_stats)
    """
    if not statement_text or len(statement_text.strip()) < 100:
        return None, None

    # Truncate very long text to avoid token limits
    max_chars = 30000
    if len(statement_text) > max_chars:
        statement_text = statement_text[:max_chars]

    prompt = STATEMENT_ANALYSIS_PROMPT.format(statement_text=statement_text)

    response, usage = await call_claude(prompt)
    logger.info(f"Claude response length: {len(response)} chars")
    logger.debug(f"Claude response preview: {response[:1000]}")

    analysis = extract_json_object_from_response(response)

    if analysis:
        logger.info(f"Successfully parsed analysis with keys: {list(analysis.keys())}")
    else:
        logger.error("Failed to parse analysis from Claude response")

    return analysis, usage
