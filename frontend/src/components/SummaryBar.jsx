import Button from './ui/Button';
import { formatCurrency, convertCurrency } from '../utils/currency';
import { useSettings } from '../context/SettingsContext';

const SummaryBar = ({ calendarData, onAddPayment, onExport, onImport }) => {
  const { settings } = useSettings();

  const monthlyTotal = calendarData?.monthly_total || 0;
  const weeklyTotals = calendarData?.weekly_totals || {};

  const displayCurrency = settings.display_currency;
  const exchangeRates = settings.exchange_rates || [];

  const convertedTotal = convertCurrency(
    monthlyTotal,
    'USD',
    displayCurrency === 'USD' ? 'INR' : 'USD',
    exchangeRates
  );

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-lg font-semibold">
            Monthly Total: {formatCurrency(monthlyTotal, 'USD')}
            <span className="text-gray-500 text-sm ml-2">
              ({formatCurrency(convertedTotal, displayCurrency === 'USD' ? 'INR' : 'USD')})
            </span>
          </div>
          <div className="text-sm text-gray-600 mt-1">
            Week 1: {formatCurrency(weeklyTotals.week1 || 0)} |
            Week 2: {formatCurrency(weeklyTotals.week2 || 0)} |
            Week 3: {formatCurrency(weeklyTotals.week3 || 0)} |
            Week 4: {formatCurrency(weeklyTotals.week4 || 0)}
          </div>
        </div>

        <div className="flex gap-2">
          <Button onClick={onAddPayment}>+ Add Payment</Button>
          <Button variant="secondary" onClick={onImport}>
            Import
          </Button>
          <Button variant="secondary" onClick={onExport}>
            Export
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SummaryBar;
