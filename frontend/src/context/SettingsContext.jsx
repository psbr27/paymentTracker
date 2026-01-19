import { createContext, useContext, useState, useEffect } from 'react';
import { getSettings } from '../services/settings';
import { useAuth } from './AuthContext';

const SettingsContext = createContext(null);

export const SettingsProvider = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [settings, setSettings] = useState({
    default_currency: 'USD',
    display_currency: 'USD',
    exchange_rates: [],
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadSettings();
    }
  }, [isAuthenticated]);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await getSettings();
      setSettings({
        ...data,
        display_currency: data.default_currency,
      });
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
    setLoading(false);
  };

  const setDisplayCurrency = (currency) => {
    setSettings((prev) => ({ ...prev, display_currency: currency }));
  };

  const value = {
    settings,
    loading,
    setDisplayCurrency,
    refreshSettings: loadSettings,
  };

  return (
    <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};
