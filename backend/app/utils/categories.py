from enum import Enum


class Category(str, Enum):
    LOAN = "LOAN"
    SUBSCRIPTION = "SUBSCRIPTION"
    INVESTMENT = "INVESTMENT"
    INSURANCE = "INSURANCE"
    UTILITY = "UTILITY"
    OTHER = "OTHER"


CATEGORY_COLORS = {
    Category.LOAN: "#EF4444",
    Category.SUBSCRIPTION: "#3B82F6",
    Category.INVESTMENT: "#22C55E",
    Category.INSURANCE: "#F97316",
    Category.UTILITY: "#A855F7",
    Category.OTHER: "#6B7280",
}

CATEGORY_NAMES = {
    Category.LOAN: "Loans/EMI",
    Category.SUBSCRIPTION: "Subscriptions",
    Category.INVESTMENT: "Investments",
    Category.INSURANCE: "Insurance",
    Category.UTILITY: "Utilities",
    Category.OTHER: "Other",
}


class Currency(str, Enum):
    USD = "USD"
    INR = "INR"


class Recurrence(str, Enum):
    MONTHLY = "MONTHLY"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"
    ONETIME = "ONETIME"
