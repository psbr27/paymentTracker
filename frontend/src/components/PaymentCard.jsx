import { getCategoryColor, getCategoryName, RECURRENCE_TYPES } from '../utils/categories';
import { formatCurrency } from '../utils/currency';
import Button from './ui/Button';

const PaymentCard = ({ payment, onEdit, onDelete }) => {
  return (
    <div className="border rounded-lg p-4 mb-3">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: getCategoryColor(payment.category) }}
          />
          <span className="font-medium">{payment.name}</span>
        </div>
        <span className="font-semibold">
          {formatCurrency(payment.amount, payment.currency)}
        </span>
      </div>

      <div className="text-sm text-gray-600 mt-2">
        <p>{getCategoryName(payment.category)}</p>
        <p>{RECURRENCE_TYPES[payment.recurrence]?.name || payment.recurrence}</p>
        {payment.notes && (
          <p className="text-gray-500 italic mt-1">{payment.notes}</p>
        )}
      </div>

      <div className="flex gap-2 mt-3">
        <Button variant="ghost" size="sm" onClick={() => onEdit(payment)}>
          Edit
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onDelete(payment)}>
          Delete
        </Button>
      </div>
    </div>
  );
};

export default PaymentCard;
