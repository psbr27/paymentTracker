export const CATEGORIES = {
  LOAN: { name: 'Loans/EMI', color: '#EF4444', key: 'LOAN' },
  SUBSCRIPTION: { name: 'Subscriptions', color: '#3B82F6', key: 'SUBSCRIPTION' },
  INVESTMENT: { name: 'Investments', color: '#22C55E', key: 'INVESTMENT' },
  INSURANCE: { name: 'Insurance', color: '#F97316', key: 'INSURANCE' },
  UTILITY: { name: 'Utilities', color: '#A855F7', key: 'UTILITY' },
  OTHER: { name: 'Other', color: '#6B7280', key: 'OTHER' },
};

export const RECURRENCE_TYPES = {
  MONTHLY: { name: 'Monthly', key: 'MONTHLY' },
  WEEKLY: { name: 'Weekly', key: 'WEEKLY' },
  BIWEEKLY: { name: 'Bi-weekly', key: 'BIWEEKLY' },
  QUARTERLY: { name: 'Quarterly', key: 'QUARTERLY' },
  ANNUAL: { name: 'Annual', key: 'ANNUAL' },
  ONETIME: { name: 'One-time', key: 'ONETIME' },
};

export const getCategoryColor = (category) => {
  return CATEGORIES[category]?.color || CATEGORIES.OTHER.color;
};

export const getCategoryName = (category) => {
  return CATEGORIES[category]?.name || 'Other';
};
