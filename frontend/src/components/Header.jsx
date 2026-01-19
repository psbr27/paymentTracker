import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSettings } from '../context/SettingsContext';
import Dropdown from './ui/Dropdown';
import Button from './ui/Button';

const Header = ({ onYearClick, currentYear }) => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { settings, setDisplayCurrency } = useSettings();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1
            className="text-xl font-bold text-blue-600 cursor-pointer"
            onClick={() => navigate('/')}
          >
            PayTrack
          </h1>
          {currentYear && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onYearClick?.()}
            >
              Year
            </Button>
          )}
        </div>

        <div className="flex items-center gap-4">
          <Dropdown
            trigger={
              <Button variant="ghost" size="sm">
                {settings.display_currency}
              </Button>
            }
            align="right"
          >
            <Dropdown.Item onClick={() => setDisplayCurrency('USD')}>
              USD ($)
            </Dropdown.Item>
            <Dropdown.Item onClick={() => setDisplayCurrency('INR')}>
              INR (Rs.)
            </Dropdown.Item>
          </Dropdown>

          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Logout
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;
