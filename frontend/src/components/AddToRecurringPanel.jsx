import { useState, useEffect } from 'react';
import SlidePanel from './SlidePanel';
import Button from './ui/Button';
import Input from './ui/Input';
import Select from './ui/Select';
import { CATEGORIES, RECURRENCE_TYPES } from '../utils/categories';
import { createPayment } from '../services/payments';

const AddToRecurringPanel = ({ isOpen, onClose, transaction, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    amount: '',
    currency: 'USD',
    category: 'OTHER',
    recurrence: 'MONTHLY',
    day_of_month: 1,
    day_of_week: 0,
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    notes: '',
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Map statement categories to payment categories
  const mapCategory = (statementCategory) => {
    const categoryMap = {
      'Mortgage_Rent': 'LOAN',
      'Loans': 'LOAN',
      'Credit_Cards': 'LOAN',
      'Utilities': 'UTILITY',
      'Insurance': 'INSURANCE',
      'Investments': 'INVESTMENT',
      'Subscriptions': 'SUBSCRIPTION',
      'Income_Payroll': 'OTHER',
      'Shopping': 'OTHER',
      'Travel_Entertainment': 'OTHER',
      'Transfers_In': 'OTHER',
      'Transfers_Out': 'OTHER',
      'Cash_Withdrawal': 'OTHER',
      'Fees': 'OTHER',
      'Other': 'OTHER',
    };
    return categoryMap[statementCategory] || 'OTHER';
  };

  useEffect(() => {
    if (transaction && isOpen) {
      const txDate = transaction.date ? new Date(transaction.date) : new Date();
      setFormData({
        name: transaction.description || transaction.payee || '',
        amount: Math.abs(transaction.amount || 0).toString(),
        currency: 'USD',
        category: mapCategory(transaction.category),
        recurrence: transaction.isRecurring ? 'MONTHLY' : 'MONTHLY',
        day_of_month: txDate.getDate() || 1,
        day_of_week: txDate.getDay() || 0,
        start_date: transaction.date || new Date().toISOString().split('T')[0],
        end_date: '',
        notes: `Added from bank statement: ${transaction.memo || ''}`.trim(),
      });
      setErrors({});
      setSuccessMessage('');
    }
  }, [transaction, isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: '' }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      newErrors.amount = 'Valid amount is required';
    }
    if (!formData.start_date) newErrors.start_date = 'Start date is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    setSuccessMessage('');

    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount),
        day_of_month: parseInt(formData.day_of_month),
        day_of_week: parseInt(formData.day_of_week),
        end_date: formData.end_date || null,
      };

      await createPayment(data);
      setSuccessMessage('Payment added to recurring!');

      setTimeout(() => {
        onSuccess?.();
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Failed to create payment:', error);
      setErrors({ submit: error.response?.data?.detail || 'Failed to add payment' });
    } finally {
      setSaving(false);
    }
  };

  const showDayOfMonth = ['MONTHLY', 'QUARTERLY', 'ANNUAL'].includes(formData.recurrence);
  const showDayOfWeek = ['WEEKLY', 'BIWEEKLY'].includes(formData.recurrence);

  const categoryOptions = Object.values(CATEGORIES).map((cat) => ({
    value: cat.key,
    label: cat.name,
  }));

  const recurrenceOptions = Object.values(RECURRENCE_TYPES).map((rec) => ({
    value: rec.key,
    label: rec.name,
  }));

  const currencyOptions = [
    { value: 'USD', label: 'USD ($)' },
    { value: 'INR', label: 'INR (Rs.)' },
  ];

  const dayOfMonthOptions = Array.from({ length: 31 }, (_, i) => ({
    value: i + 1,
    label: String(i + 1),
  }));

  const dayOfWeekOptions = [
    { value: 0, label: 'Monday' },
    { value: 1, label: 'Tuesday' },
    { value: 2, label: 'Wednesday' },
    { value: 3, label: 'Thursday' },
    { value: 4, label: 'Friday' },
    { value: 5, label: 'Saturday' },
    { value: 6, label: 'Sunday' },
  ];

  return (
    <SlidePanel isOpen={isOpen} onClose={onClose} title="Add to Recurring Payments">
      <form onSubmit={handleSubmit} className="space-y-4">
        {successMessage && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            {successMessage}
          </div>
        )}

        {errors.submit && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {errors.submit}
          </div>
        )}

        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm">
          <p className="font-medium text-blue-800">Adding transaction as recurring payment</p>
          <p className="text-blue-600 mt-1">
            Configure the recurrence settings below and save to track this payment.
          </p>
        </div>

        <Input
          label="Payment Name *"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="e.g., Netflix, Home Loan EMI"
          error={errors.name}
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Amount *"
            name="amount"
            type="number"
            step="0.01"
            value={formData.amount}
            onChange={handleChange}
            placeholder="0.00"
            error={errors.amount}
          />
          <Select
            label="Currency *"
            name="currency"
            value={formData.currency}
            onChange={handleChange}
            options={currencyOptions}
          />
        </div>

        <Select
          label="Category *"
          name="category"
          value={formData.category}
          onChange={handleChange}
          options={categoryOptions}
        />

        <Select
          label="Recurrence *"
          name="recurrence"
          value={formData.recurrence}
          onChange={handleChange}
          options={recurrenceOptions}
        />

        {showDayOfMonth && (
          <Select
            label="Day of Month *"
            name="day_of_month"
            value={formData.day_of_month}
            onChange={handleChange}
            options={dayOfMonthOptions}
          />
        )}

        {showDayOfWeek && (
          <Select
            label="Day of Week *"
            name="day_of_week"
            value={formData.day_of_week}
            onChange={handleChange}
            options={dayOfWeekOptions}
          />
        )}

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Start Date *"
            name="start_date"
            type="date"
            value={formData.start_date}
            onChange={handleChange}
            error={errors.start_date}
          />
          <Input
            label="End Date"
            name="end_date"
            type="date"
            value={formData.end_date}
            onChange={handleChange}
          />
        </div>

        <Input
          label="Notes"
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          placeholder="Optional notes..."
        />

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="secondary" type="button" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? 'Adding...' : 'Add to Recurring'}
          </Button>
        </div>
      </form>
    </SlidePanel>
  );
};

export default AddToRecurringPanel;
