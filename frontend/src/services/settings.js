import api from './api';

export const getSettings = async () => {
  const response = await api.get('/api/settings');
  return response.data;
};

export const updateSettings = async (settingsData) => {
  const response = await api.put('/api/settings', settingsData);
  return response.data;
};

export const updateExchangeRate = async (fromCurrency, toCurrency, rate) => {
  const response = await api.put(
    `/api/settings/exchange-rate/${fromCurrency}/${toCurrency}`,
    { rate }
  );
  return response.data;
};

export const exportPayments = async (params) => {
  const queryParams = new URLSearchParams();
  if (params.year) queryParams.append('year', params.year);
  if (params.month) queryParams.append('month', params.month);
  if (params.start_date) queryParams.append('start_date', params.start_date);
  if (params.end_date) queryParams.append('end_date', params.end_date);
  if (params.category) queryParams.append('category', params.category);

  const response = await api.get(`/api/export?${queryParams.toString()}`, {
    responseType: 'blob',
  });
  return response.data;
};
