import api from './api';

export const getPayments = async () => {
  const response = await api.get('/api/payments');
  return response.data;
};

export const getPayment = async (id) => {
  const response = await api.get(`/api/payments/${id}`);
  return response.data;
};

export const createPayment = async (paymentData) => {
  const response = await api.post('/api/payments', paymentData);
  return response.data;
};

export const updatePayment = async (id, paymentData) => {
  const response = await api.put(`/api/payments/${id}`, paymentData);
  return response.data;
};

export const deletePayment = async (id) => {
  await api.delete(`/api/payments/${id}`);
};
