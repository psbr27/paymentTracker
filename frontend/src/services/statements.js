import api from './api';

export const getStatements = async (params = {}) => {
  const response = await api.get('/api/statements', { params });
  return response.data;
};

export const getStatement = async (id) => {
  const response = await api.get(`/api/statements/${id}`);
  return response.data;
};

export const analyzeStatement = async (file, bankName = null) => {
  const formData = new FormData();
  formData.append('file', file);

  const params = bankName ? `?bank_name=${encodeURIComponent(bankName)}` : '';

  const response = await api.post(`/api/statements/analyze${params}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const deleteStatement = async (id) => {
  await api.delete(`/api/statements/${id}`);
};
