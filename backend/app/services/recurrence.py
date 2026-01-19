from datetime import date
from calendar import monthrange
from typing import List
from app.models.payment import Payment


def get_last_day_of_month(year: int, month: int) -> int:
    """Get the last day of a given month."""
    return monthrange(year, month)[1]


def payment_occurs_on_date(payment: Payment, check_date: date) -> bool:
    """Check if a payment occurs on a specific date."""
    # Check if date is within payment's active period
    if check_date < payment.start_date:
        return False
    if payment.end_date and check_date > payment.end_date:
        return False

    recurrence = payment.recurrence

    if recurrence == "ONETIME":
        return check_date == payment.start_date

    elif recurrence == "MONTHLY":
        day_of_month = payment.day_of_month or payment.start_date.day
        last_day = get_last_day_of_month(check_date.year, check_date.month)
        # Handle 31st on months with fewer days
        target_day = min(day_of_month, last_day)
        return check_date.day == target_day

    elif recurrence == "WEEKLY":
        day_of_week = payment.day_of_week if payment.day_of_week is not None else payment.start_date.weekday()
        return check_date.weekday() == day_of_week

    elif recurrence == "BIWEEKLY":
        day_of_week = payment.day_of_week if payment.day_of_week is not None else payment.start_date.weekday()
        if check_date.weekday() != day_of_week:
            return False
        # Check if it's been an even number of weeks since start
        days_diff = (check_date - payment.start_date).days
        weeks_diff = days_diff // 7
        return weeks_diff >= 0 and weeks_diff % 2 == 0

    elif recurrence == "QUARTERLY":
        day_of_month = payment.day_of_month or payment.start_date.day
        last_day = get_last_day_of_month(check_date.year, check_date.month)
        target_day = min(day_of_month, last_day)
        if check_date.day != target_day:
            return False
        # Check if it's a quarter month from start
        start_month = payment.start_date.month
        check_month = check_date.month
        month_diff = (check_date.year - payment.start_date.year) * 12 + (check_month - start_month)
        return month_diff >= 0 and month_diff % 3 == 0

    elif recurrence == "ANNUAL":
        day_of_month = payment.day_of_month or payment.start_date.day
        # Handle Feb 29 for leap years
        if payment.start_date.month == 2 and day_of_month == 29:
            last_day = get_last_day_of_month(check_date.year, 2)
            if check_date.month == 2 and check_date.day == last_day:
                return True
            return False
        last_day = get_last_day_of_month(check_date.year, payment.start_date.month)
        target_day = min(day_of_month, last_day)
        return check_date.month == payment.start_date.month and check_date.day == target_day

    return False


def get_payments_for_date(payments: List[Payment], check_date: date) -> List[Payment]:
    """Get all payments that occur on a specific date."""
    return [p for p in payments if payment_occurs_on_date(p, check_date)]
