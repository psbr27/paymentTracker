export const CURRENCIES = {
  USD: { symbol: '$', name: 'US Dollar', code: 'USD' },
  INR: { symbol: '₹', name: 'Indian Rupee', code: 'INR' },
};

export const formatCurrency = (amount, currency = 'USD') => {
  const currencyInfo = CURRENCIES[currency] || CURRENCIES.USD;
  const formattedAmount = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
  return `${currencyInfo.symbol}${formattedAmount}`;
};

export const convertCurrency = (amount, fromCurrency, toCurrency, exchangeRates) => {
  if (fromCurrency === toCurrency) return amount;

  const rate = exchangeRates.find(
    (r) => r.from_currency === fromCurrency && r.to_currency === toCurrency
  );

  if (rate) {
    return amount * parseFloat(rate.rate);
  }

  return amount;
};
