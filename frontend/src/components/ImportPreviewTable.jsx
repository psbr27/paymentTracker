import { CATEGORIES, RECURRENCE_TYPES, getCategoryColor } from '../utils/categories';
import { useSettings } from '../context/SettingsContext';

const formatCurrency = (amount, currency) => {
  const num = parseFloat(amount);
  if (currency === 'INR') {
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const ConfidenceBadge = ({ confidence }) => {
  const percent = Math.round(confidence * 100);
  let bgColor = 'bg-gray-100 text-gray-600';
  if (percent >= 80) {
    bgColor = 'bg-green-100 text-green-700';
  } else if (percent >= 60) {
    bgColor = 'bg-yellow-100 text-yellow-700';
  }

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${bgColor}`}>
      {percent}%
    </span>
  );
};

const ImportPreviewTable = ({
  transactions,
  selectedTransactions,
  onToggleSelect,
  onUpdateTransaction,
}) => {
  const { settings } = useSettings();
  const displayCurrency = settings?.display_currency || 'USD';

  const categoryOptions = Object.entries(CATEGORIES).map(([key, val]) => ({
    value: key,
    label: val.name,
  }));

  const recurrenceOptions = Object.entries(RECURRENCE_TYPES).map(([key, val]) => ({
    value: key,
    label: val.name,
  }));

  const handleNameChange = (id, newName) => {
    onUpdateTransaction(id, { suggested_name: newName });
  };

  const handleCategoryChange = (id, newCategory) => {
    onUpdateTransaction(id, { category: newCategory });
  };

  const handleRecurrenceChange = (id, newRecurrence) => {
    onUpdateTransaction(id, { recurrence: newRecurrence });
  };

  if (!transactions || transactions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No transactions to display
      </div>
    );
  }

  return (
    <div className="max-h-96 overflow-y-auto border rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            <th className="w-10 px-3 py-2 text-left"></th>
            <th className="px-3 py-2 text-left font-medium text-gray-700">Name</th>
            <th className="px-3 py-2 text-left font-medium text-gray-700 w-28">Amount</th>
            <th className="px-3 py-2 text-left font-medium text-gray-700 w-32">Category</th>
            <th className="px-3 py-2 text-left font-medium text-gray-700 w-28">Recurrence</th>
            <th className="px-3 py-2 text-center font-medium text-gray-700 w-16">Conf.</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {transactions.map((tx) => {
            const isSelected = !!selectedTransactions[tx.id];
            const editableTx = selectedTransactions[tx.id] || tx;

            return (
              <tr
                key={tx.id}
                className={`hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
              >
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => onToggleSelect(tx.id, tx)}
                    className="w-4 h-4 rounded border-gray-300 text-blue-500 focus:ring-blue-500"
                  />
                </td>
                <td className="px-3 py-2">
                  {isSelected ? (
                    <input
                      type="text"
                      value={editableTx.suggested_name}
                      onChange={(e) => handleNameChange(tx.id, e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  ) : (
                    <div>
                      <div className="font-medium">{tx.suggested_name}</div>
                      <div className="text-xs text-gray-400 truncate max-w-xs">
                        {tx.original_descriptions?.[0]}
                      </div>
                    </div>
                  )}
                </td>
                <td className="px-3 py-2 font-medium">
                  {formatCurrency(tx.average_amount, tx.currency || displayCurrency)}
                  {tx.occurrence_count > 1 && (
                    <span className="text-xs text-gray-400 ml-1">
                      ({tx.occurrence_count}x)
                    </span>
                  )}
                </td>
                <td className="px-3 py-2">
                  {isSelected ? (
                    <select
                      value={editableTx.category}
                      onChange={(e) => handleCategoryChange(tx.id, e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      {categoryOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="flex items-center gap-1">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: getCategoryColor(tx.category) }}
                      />
                      {CATEGORIES[tx.category]?.name || tx.category}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2">
                  {isSelected ? (
                    <select
                      value={editableTx.recurrence}
                      onChange={(e) => handleRecurrenceChange(tx.id, e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      {recurrenceOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    RECURRENCE_TYPES[tx.recurrence]?.name || tx.recurrence
                  )}
                </td>
                <td className="px-3 py-2 text-center">
                  <ConfidenceBadge confidence={tx.confidence} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default ImportPreviewTable;
