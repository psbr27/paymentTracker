import api from './api';

export const uploadBankStatement = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/import/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const confirmImport = async (transactions) => {
  const response = await api.post('/api/import/confirm', { transactions });
  return response.data;
};
