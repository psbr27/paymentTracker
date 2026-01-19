import { getCategoryColor } from '../utils/categories';
import { formatCurrency } from '../utils/currency';

const PaymentTooltip = ({ day, payments, total, position = 'right' }) => {
  if (!payments || payments.length === 0) return null;

  const positionClasses = position === 'right'
    ? 'left-full ml-2'
    : 'right-full mr-2';

  return (
    <div
      className={`
        absolute top-0 ${positionClasses} z-40
        w-56 bg-white rounded-lg shadow-lg border border-gray-200
        pointer-events-none
      `}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-gray-100 bg-gray-50 rounded-t-lg">
        <span className="text-sm font-medium text-gray-700">
          {payments.length} payment{payments.length !== 1 ? 's' : ''} on day {day}
        </span>
      </div>

      {/* Payment List */}
      <div className="px-3 py-2 max-h-48 overflow-y-auto">
        {payments.map((payment) => (
          <div
            key={payment.id}
            className="flex items-center justify-between py-1.5"
          >
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: getCategoryColor(payment.category) }}
              />
              <span className="text-sm text-gray-700 truncate">
                {payment.name}
              </span>
            </div>
            <span className="text-sm font-medium text-gray-900 ml-2 flex-shrink-0">
              {formatCurrency(payment.amount, payment.currency)}
            </span>
          </div>
        ))}
      </div>

      {/* Footer with Total */}
      <div className="px-3 py-2 border-t border-gray-100 bg-gray-50 rounded-b-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-600">Total</span>
          <span className="text-sm font-semibold text-gray-900">
            {formatCurrency(total)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default PaymentTooltip;
