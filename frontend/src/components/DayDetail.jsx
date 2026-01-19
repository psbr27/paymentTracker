import { formatCurrency } from '../utils/currency';
import PaymentCard from './PaymentCard';
import Button from './ui/Button';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const DayDetail = ({ year, month, day, dayData, onEdit, onDelete, onAddPayment }) => {
  const date = new Date(year, month - 1, day);
  const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
  const formattedDate = `${dayName}, ${MONTH_NAMES[month - 1]} ${day}, ${year}`;

  const total = dayData?.total || 0;
  const payments = dayData?.payments || [];

  return (
    <div>
      <div className="mb-4">
        <p className="text-gray-600">{formattedDate}</p>
        <p className="text-xl font-semibold">Total: {formatCurrency(total)}</p>
      </div>

      <div className="mb-4">
        {payments.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No payments on this day
          </p>
        ) : (
          payments.map((payment) => (
            <PaymentCard
              key={payment.id}
              payment={payment}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))
        )}
      </div>

      <Button className="w-full" onClick={onAddPayment}>
        + Add Payment to {MONTH_NAMES[month - 1]} {day}
      </Button>
    </div>
  );
};

export default DayDetail;
