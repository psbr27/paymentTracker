import api from './api';

export const login = async (username, password) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await api.post('/api/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

export const logout = async () => {
  await api.post('/api/auth/logout');
};

export const getCurrentUser = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};
