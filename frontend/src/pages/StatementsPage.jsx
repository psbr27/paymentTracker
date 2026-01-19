import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';
import { getStatements, analyzeStatement, deleteStatement } from '../services/statements';

const StatementsPage = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [statements, setStatements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);

  useEffect(() => {
    loadStatements();
  }, []);

  const loadStatements = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getStatements();
      setStatements(data.statements || []);
    } catch (err) {
      console.error('Failed to load statements:', err);
      setError('Failed to load statements');
    }
    setLoading(false);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported');
      return;
    }

    setUploading(true);
    setUploadProgress('Uploading and analyzing statement...');
    setError(null);

    try {
      const result = await analyzeStatement(file);
      setUploadProgress(null);
      // Navigate to the newly created statement
      navigate(`/statements/${result.statement_id}`);
    } catch (err) {
      console.error('Failed to analyze statement:', err);
      setError(err.response?.data?.detail || 'Failed to analyze statement');
      setUploadProgress(null);
    }
    setUploading(false);
    // Reset file input
    e.target.value = '';
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this statement?')) return;

    try {
      await deleteStatement(id);
      loadStatements();
    } catch (err) {
      console.error('Failed to delete statement:', err);
      setError('Failed to delete statement');
    }
  };

  // Group statements by year and month
  const groupedStatements = statements.reduce((acc, stmt) => {
    const date = new Date(stmt.period_start);
    const year = date.getFullYear();
    const month = date.toLocaleString('default', { month: 'long' });
    const key = `${year}`;
    const monthKey = `${year}-${date.getMonth()}`;

    if (!acc[key]) acc[key] = {};
    if (!acc[key][monthKey]) acc[key][monthKey] = { month, statements: [] };
    acc[key][monthKey].statements.push(stmt);

    return acc;
  }, {});

  const sortedYears = Object.keys(groupedStatements).sort((a, b) => b - a);

  const formatCurrency = (amount) => {
    if (amount == null) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Bank Statements</h2>
            <p className="text-gray-600">Upload and analyze your bank statements</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => navigate('/')}>Back to Calendar</Button>
            <Button variant="primary" onClick={handleUploadClick} disabled={uploading}>
              {uploading ? 'Analyzing...' : 'Upload Statement'}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {uploadProgress && (
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-3">
              <Spinner size="sm" />
              <span className="text-blue-700">{uploadProgress}</span>
            </div>
            <p className="text-sm text-blue-600 mt-2">
              This may take a moment as AI analyzes your statement...
            </p>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : statements.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-lg border">
            <div className="text-gray-400 text-5xl mb-4">📄</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No statements yet</h3>
            <p className="text-gray-600 mb-4">Upload a bank statement PDF to get started</p>
            <Button variant="primary" onClick={handleUploadClick}>
              Upload Your First Statement
            </Button>
          </div>
        ) : (
          <div className="space-y-8">
            {sortedYears.map((year) => (
              <div key={year}>
                <h3 className="text-xl font-bold text-gray-800 mb-4 border-b pb-2">{year}</h3>
                <div className="space-y-6">
                  {Object.entries(groupedStatements[year])
                    .sort(([a], [b]) => b.localeCompare(a))
                    .map(([monthKey, { month, statements: monthStatements }]) => (
                      <div key={monthKey}>
                        <h4 className="text-lg font-semibold text-gray-700 mb-3">{month}</h4>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                          {monthStatements.map((stmt) => (
                            <div
                              key={stmt.id}
                              onClick={() => navigate(`/statements/${stmt.id}`)}
                              className="bg-white rounded-lg border shadow-sm p-4 cursor-pointer hover:shadow-md transition-shadow"
                            >
                              <div className="flex justify-between items-start mb-2">
                                <h5 className="font-medium text-gray-900">{stmt.bank_name}</h5>
                                <button
                                  onClick={(e) => handleDelete(stmt.id, e)}
                                  className="text-gray-400 hover:text-red-500 p-1"
                                  title="Delete"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                </button>
                              </div>
                              <p className="text-sm text-gray-500 mb-3">
                                {new Date(stmt.period_start).toLocaleDateString()} - {new Date(stmt.period_end).toLocaleDateString()}
                              </p>
                              <div className="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                  <span className="text-gray-500">Credits:</span>
                                  <span className="ml-1 text-green-600 font-medium">
                                    {formatCurrency(stmt.total_credits)}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-gray-500">Debits:</span>
                                  <span className="ml-1 text-red-600 font-medium">
                                    {formatCurrency(stmt.total_debits)}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default StatementsPage;
