import api from './api';

export const getCalendarData = async (year, month) => {
  const response = await api.get(`/api/calendar/${year}/${month}`);
  return response.data;
};

export const getYearSummary = async (year) => {
  const response = await api.get(`/api/summary/${year}`);
  return response.data;
};
