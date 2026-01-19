import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';
import { getStatement } from '../services/statements';

const StatementDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [statement, setStatement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    loadStatement();
  }, [id]);

  const loadStatement = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getStatement(id);
      setStatement(data);
    } catch (err) {
      console.error('Failed to load statement:', err);
      setError('Statement not found');
    }
    setLoading(false);
  };

  const formatCurrency = (amount) => {
    if (amount == null) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex justify-center py-20">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error || !statement) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error || 'Statement not found'}
          </div>
          <Button className="mt-4" onClick={() => navigate('/statements')}>
            Back to Statements
          </Button>
        </div>
      </div>
    );
  }

  const { analysis } = statement;
  const summary = analysis?.summary || {};
  const credits = analysis?.credits?.byCategory || [];
  const debits = analysis?.debits?.byCategory || [];
  const analytics = analysis?.analytics || {};
  const flags = analysis?.flags || {};

  const tabs = [
    { id: 'summary', label: 'Summary' },
    { id: 'credits', label: 'Credits' },
    { id: 'debits', label: 'Debits' },
    { id: 'analytics', label: 'Analytics' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{statement.bank_name}</h2>
            <p className="text-gray-600">
              {formatDate(statement.period_start)} - {formatDate(statement.period_end)}
            </p>
            {statement.account_number_masked && (
              <p className="text-sm text-gray-500">Account: {statement.account_number_masked}</p>
            )}
          </div>
          <Button onClick={() => navigate('/statements')}>Back to Statements</Button>
        </div>

        {/* AI Usage Info */}
        {statement.ai_usage && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm">
            <span className="font-medium text-blue-700">AI Analysis</span>
            <span className="text-blue-600 ml-2">
              Model: {statement.ai_usage.model} |
              Tokens: {statement.ai_usage.tokens_used?.toLocaleString() || 'N/A'} |
              Cost: {statement.ai_usage.cost_estimate || 'N/A'}
            </span>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b mb-6">
          <nav className="flex gap-4">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            {/* Balance Summary */}
            <div className="bg-white rounded-lg border p-6">
              <h3 className="text-lg font-semibold mb-4">Balance Summary</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Opening Balance</p>
                  <p className="text-xl font-bold">{formatCurrency(summary.openingBalance)}</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Closing Balance</p>
                  <p className="text-xl font-bold">{formatCurrency(summary.closingBalance)}</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-600">Total Credits</p>
                  <p className="text-xl font-bold text-green-700">{formatCurrency(summary.totalCredits)}</p>
                </div>
                <div className="p-4 bg-red-50 rounded-lg">
                  <p className="text-sm text-red-600">Total Debits</p>
                  <p className="text-xl font-bold text-red-700">{formatCurrency(summary.totalDebits)}</p>
                </div>
              </div>
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600">Net Change</p>
                <p className={`text-2xl font-bold ${summary.netChange >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatCurrency(summary.netChange)}
                </p>
              </div>
            </div>

            {/* Flags & Alerts */}
            {(flags.overdraftEvents?.length > 0 || flags.fees?.length > 0 || flags.unusualActivity?.length > 0) && (
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold mb-4">Alerts</h3>
                {flags.overdraftEvents?.length > 0 && (
                  <div className="mb-3 p-3 bg-red-50 rounded-lg">
                    <p className="font-medium text-red-700">Overdraft Events: {flags.overdraftEvents.length}</p>
                  </div>
                )}
                {flags.fees?.length > 0 && (
                  <div className="mb-3 p-3 bg-yellow-50 rounded-lg">
                    <p className="font-medium text-yellow-700">Fees: {flags.fees.length}</p>
                    <ul className="mt-2 text-sm text-yellow-600">
                      {flags.fees.map((fee, idx) => (
                        <li key={idx}>{fee.description || fee} - {formatCurrency(fee.amount)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'credits' && (
          <div className="space-y-4">
            {credits.length === 0 ? (
              <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
                No credits found in this statement
              </div>
            ) : (
              credits.map((category, idx) => (
                <div key={idx} className="bg-white rounded-lg border overflow-hidden">
                  <div className="bg-green-50 px-4 py-3 flex justify-between items-center">
                    <h4 className="font-semibold text-green-800">{category.category}</h4>
                    <div className="text-sm">
                      <span className="text-green-600">{category.count} transactions</span>
                      <span className="ml-3 font-bold text-green-700">{formatCurrency(category.total)}</span>
                    </div>
                  </div>
                  <div className="divide-y">
                    {category.transactions?.map((tx, txIdx) => (
                      <div key={txIdx} className="px-4 py-3 flex justify-between items-center hover:bg-gray-50">
                        <div>
                          <p className="font-medium">{tx.description}</p>
                          <p className="text-sm text-gray-500">{formatDate(tx.date)} {tx.method && `- ${tx.method}`}</p>
                        </div>
                        <span className="text-green-600 font-medium">{formatCurrency(tx.amount)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'debits' && (
          <div className="space-y-4">
            {debits.length === 0 ? (
              <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
                No debits found in this statement
              </div>
            ) : (
              debits.map((category, idx) => (
                <div key={idx} className="bg-white rounded-lg border overflow-hidden">
                  <div className="bg-red-50 px-4 py-3 flex justify-between items-center">
                    <h4 className="font-semibold text-red-800">{category.category}</h4>
                    <div className="text-sm">
                      <span className="text-red-600">{category.count} transactions</span>
                      <span className="ml-3 font-bold text-red-700">{formatCurrency(category.total)}</span>
                    </div>
                  </div>
                  <div className="divide-y">
                    {category.transactions?.map((tx, txIdx) => (
                      <div key={txIdx} className="px-4 py-3 flex justify-between items-center hover:bg-gray-50">
                        <div>
                          <p className="font-medium">
                            {tx.description}
                            {tx.isRecurring && (
                              <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">Recurring</span>
                            )}
                          </p>
                          <p className="text-sm text-gray-500">{formatDate(tx.date)} {tx.method && `- ${tx.method}`}</p>
                        </div>
                        <span className="text-red-600 font-medium">{formatCurrency(tx.amount)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {/* Top Categories */}
            {analytics.topCategories?.length > 0 && (
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold mb-4">Top Spending Categories</h3>
                <div className="space-y-3">
                  {analytics.topCategories.map((cat, idx) => (
                    <div key={idx} className="flex items-center gap-4">
                      <div className="w-32 text-sm font-medium">{cat.category}</div>
                      <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                        <div
                          className="bg-blue-500 h-full rounded-full"
                          style={{ width: `${cat.percentage || 0}%` }}
                        />
                      </div>
                      <div className="w-24 text-right text-sm">{formatCurrency(cat.amount)}</div>
                      <div className="w-16 text-right text-sm text-gray-500">{cat.percentage?.toFixed(1)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recurring Payments */}
            {analytics.recurringPayments?.length > 0 && (
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold mb-4">Recurring Payments</h3>
                <div className="divide-y">
                  {analytics.recurringPayments.map((payment, idx) => (
                    <div key={idx} className="py-3 flex justify-between items-center">
                      <div>
                        <p className="font-medium">{payment.payee}</p>
                        <p className="text-sm text-gray-500">{payment.category} - {payment.frequency}</p>
                      </div>
                      <span className="font-medium">{formatCurrency(payment.amount)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Largest Transaction */}
            {analytics.largestTransaction && (
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold mb-4">Largest Transaction</h3>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{analytics.largestTransaction.description}</p>
                      <p className="text-sm text-gray-500">
                        {formatDate(analytics.largestTransaction.date)} - {analytics.largestTransaction.type}
                      </p>
                    </div>
                    <span className={`text-xl font-bold ${
                      analytics.largestTransaction.type === 'credit' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(analytics.largestTransaction.amount)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Average Daily Balance */}
            {analytics.averageDailyBalance != null && (
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold mb-2">Average Daily Balance</h3>
                <p className="text-3xl font-bold text-blue-600">{formatCurrency(analytics.averageDailyBalance)}</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default StatementDetailPage;
