import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';
import { getYearSummary } from '../services/calendar';
import { formatCurrency, convertCurrency } from '../utils/currency';
import { useSettings } from '../context/SettingsContext';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const MonthCard = ({ month, total, intensity, onClick }) => {
  const barWidth = Math.max(intensity * 100, 5);

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition-shadow"
    >
      <h3 className="font-medium text-gray-700">{MONTH_NAMES[month - 1]}</h3>
      <p className="text-lg font-semibold mt-1">{formatCurrency(total)}</p>
      <div className="mt-2 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all"
          style={{ width: `${barWidth}%` }}
        />
      </div>
    </div>
  );
};

const YearOverviewPage = () => {
  const navigate = useNavigate();
  const { year: yearParam } = useParams();
  const [year, setYear] = useState(parseInt(yearParam) || new Date().getFullYear());
  const [yearData, setYearData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { settings } = useSettings();

  useEffect(() => {
    loadYearData();
  }, [year]);

  const loadYearData = async () => {
    setLoading(true);
    try {
      const data = await getYearSummary(year);
      setYearData(data);
    } catch (error) {
      console.error('Failed to load year data:', error);
    }
    setLoading(false);
  };

  const handlePrevYear = () => {
    const newYear = year - 1;
    setYear(newYear);
    navigate(`/year/${newYear}`);
  };

  const handleNextYear = () => {
    const newYear = year + 1;
    setYear(newYear);
    navigate(`/year/${newYear}`);
  };

  const handleMonthClick = (month) => {
    navigate(`/?year=${year}&month=${month}`);
  };

  const handleBackToMonth = () => {
    navigate('/');
  };

  const annualTotal = yearData?.annual_total || 0;
  const displayCurrency = settings.display_currency;
  const exchangeRates = settings.exchange_rates || [];

  const convertedTotal = convertCurrency(
    annualTotal,
    'USD',
    displayCurrency === 'USD' ? 'INR' : 'USD',
    exchangeRates
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Year Navigation */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={handlePrevYear}>
                &lt;
              </Button>
              <h1 className="text-2xl font-bold">{year}</h1>
              <Button variant="ghost" onClick={handleNextYear}>
                &gt;
              </Button>
            </div>
            {!loading && (
              <p className="text-lg text-gray-600 mt-2">
                Annual Total: {formatCurrency(annualTotal)}
                <span className="text-sm ml-2">
                  ({formatCurrency(convertedTotal, displayCurrency === 'USD' ? 'INR' : 'USD')})
                </span>
              </p>
            )}
          </div>
          <Button variant="secondary" onClick={handleBackToMonth}>
            Back to Month
          </Button>
        </div>

        {/* Months Grid */}
        {loading ? (
          <div className="flex justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {yearData?.months?.map((monthData) => (
              <MonthCard
                key={monthData.month}
                month={monthData.month}
                total={monthData.total}
                intensity={monthData.intensity}
                onClick={() => handleMonthClick(monthData.month)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default YearOverviewPage;
