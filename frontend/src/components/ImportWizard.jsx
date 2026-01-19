import { useState, useRef } from 'react';
import Modal from './ui/Modal';
import Button from './ui/Button';
import Spinner from './ui/Spinner';
import ImportPreviewTable from './ImportPreviewTable';
import { uploadBankStatement, confirmImport } from '../services/import';

const STAGES = {
  UPLOAD: 'upload',
  PROCESSING: 'processing',
  REVIEW: 'review',
  CONFIRMING: 'confirming',
  SUCCESS: 'success',
};

const ImportWizard = ({ isOpen, onClose, onComplete }) => {
  const [stage, setStage] = useState(STAGES.UPLOAD);
  const [error, setError] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [previewData, setPreviewData] = useState(null);
  const [selectedTransactions, setSelectedTransactions] = useState({});
  const [importResult, setImportResult] = useState(null);
  const fileInputRef = useRef(null);

  const resetState = () => {
    setStage(STAGES.UPLOAD);
    setError(null);
    setWarnings([]);
    setPreviewData(null);
    setSelectedTransactions({});
    setImportResult(null);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const filename = file.name.toLowerCase();
    if (!filename.endsWith('.csv') && !filename.endsWith('.pdf')) {
      setError('Please select a CSV or PDF file');
      return;
    }

    setStage(STAGES.PROCESSING);
    setError(null);

    try {
      const result = await uploadBankStatement(file);

      if (result.analyzed_bills.length === 0) {
        setError('No recurring bills detected in this statement. Try uploading a statement with more transaction history.');
        setStage(STAGES.UPLOAD);
        return;
      }

      if (result.parsing_warnings?.length > 0) {
        setWarnings(result.parsing_warnings);
      }

      if (result.used_fallback) {
        setWarnings((prev) => [...prev, 'AI analysis unavailable. Using rule-based detection.']);
      }

      setPreviewData(result);

      // Pre-select high confidence transactions
      const initialSelected = {};
      result.analyzed_bills.forEach((tx) => {
        if (tx.confidence >= 0.7) {
          initialSelected[tx.id] = tx;
        }
      });
      setSelectedTransactions(initialSelected);

      setStage(STAGES.REVIEW);
    } catch (err) {
      console.error('Upload error:', err);
      if (err.response?.status === 400) {
        setError(err.response.data.detail || 'Failed to parse the file');
      } else if (err.response?.status === 503) {
        setError('Analysis service temporarily unavailable. Please try again.');
      } else {
        setError('Failed to process file. Please check the format and try again.');
      }
      setStage(STAGES.UPLOAD);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleToggleSelect = (id, transaction) => {
    setSelectedTransactions((prev) => {
      const newSelected = { ...prev };
      if (newSelected[id]) {
        delete newSelected[id];
      } else {
        newSelected[id] = transaction;
      }
      return newSelected;
    });
  };

  const handleUpdateTransaction = (id, updates) => {
    setSelectedTransactions((prev) => {
      if (!prev[id]) return prev;
      return {
        ...prev,
        [id]: { ...prev[id], ...updates },
      };
    });
  };

  const handleConfirmImport = async () => {
    const transactionsToImport = Object.values(selectedTransactions).map((tx) => ({
      id: tx.id,
      name: tx.suggested_name,
      amount: tx.average_amount,
      currency: tx.currency,
      category: tx.category,
      recurrence: tx.recurrence,
      day_of_month: tx.day_of_month,
      day_of_week: tx.day_of_week,
      start_date: tx.date_range?.first || new Date().toISOString().split('T')[0],
      notes: null,
    }));

    if (transactionsToImport.length === 0) {
      setError('Please select at least one transaction to import');
      return;
    }

    setStage(STAGES.CONFIRMING);
    setError(null);

    try {
      const result = await confirmImport(transactionsToImport);
      setImportResult(result);
      setStage(STAGES.SUCCESS);
    } catch (err) {
      console.error('Import error:', err);
      setError(err.response?.data?.detail || 'Failed to import transactions');
      setStage(STAGES.REVIEW);
    }
  };

  const handleFinish = () => {
    handleClose();
    onComplete?.();
  };

  const selectedCount = Object.keys(selectedTransactions).length;

  const renderContent = () => {
    switch (stage) {
      case STAGES.UPLOAD:
        return (
          <div className="text-center py-8">
            <div className="mb-6">
              <svg
                className="mx-auto h-16 w-16 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium mb-2">Upload Bank Statement</h3>
            <p className="text-gray-500 mb-6">
              Select a CSV or PDF file exported from your bank.
              <br />
              We'll analyze it to find recurring bills.
            </p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.pdf"
              onChange={handleFileSelect}
              className="hidden"
              id="statement-upload"
            />
            <label
              htmlFor="statement-upload"
              className="inline-block cursor-pointer bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Select File
            </label>

            <p className="mt-4 text-xs text-gray-400">
              Supported formats: CSV and PDF files from most major banks
            </p>
          </div>
        );

      case STAGES.PROCESSING:
        return (
          <div className="text-center py-12">
            <Spinner size="lg" className="mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Analyzing Transactions</h3>
            <p className="text-gray-500">
              Using AI to identify recurring bills and subscriptions...
            </p>
          </div>
        );

      case STAGES.REVIEW:
        return (
          <div>
            <div className="mb-4">
              <h3 className="text-lg font-medium">
                Found {previewData?.analyzed_bills?.length || 0} Potential Bills
              </h3>
              <p className="text-gray-500 text-sm">
                Select the ones you want to import. You can edit details before importing.
              </p>
            </div>

            {previewData?.ai_usage && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 text-sm">
                <div className="flex items-center gap-2 mb-1">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="font-medium">AI Analysis Complete</span>
                </div>
                <div className="text-xs text-blue-600">
                  Model: {previewData.ai_usage.model} |
                  Tokens: {previewData.ai_usage.input_tokens.toLocaleString()} in / {previewData.ai_usage.output_tokens.toLocaleString()} out |
                  Est. cost: ${previewData.ai_usage.cost_estimate.toFixed(4)}
                </div>
              </div>
            )}

            {warnings.length > 0 && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm">
                {warnings.map((w, i) => (
                  <div key={i}>{w}</div>
                ))}
              </div>
            )}

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <ImportPreviewTable
              transactions={previewData?.analyzed_bills || []}
              selectedTransactions={selectedTransactions}
              onToggleSelect={handleToggleSelect}
              onUpdateTransaction={handleUpdateTransaction}
            />

            <div className="mt-6 flex items-center justify-between border-t pt-4">
              <span className="text-sm text-gray-600">
                {selectedCount} payment{selectedCount !== 1 ? 's' : ''} selected
              </span>
              <div className="flex gap-3">
                <Button variant="secondary" onClick={handleClose}>
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirmImport}
                  disabled={selectedCount === 0}
                >
                  Import Selected
                </Button>
              </div>
            </div>
          </div>
        );

      case STAGES.CONFIRMING:
        return (
          <div className="text-center py-12">
            <Spinner size="lg" className="mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Importing Payments</h3>
            <p className="text-gray-500">
              Creating {selectedCount} payment{selectedCount !== 1 ? 's' : ''}...
            </p>
          </div>
        );

      case STAGES.SUCCESS:
        return (
          <div className="text-center py-8">
            <div className="mb-4">
              <svg
                className="mx-auto h-16 w-16 text-green-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium mb-2">Import Complete!</h3>
            <p className="text-gray-500 mb-6">
              Successfully imported {importResult?.imported_count || 0} payment
              {(importResult?.imported_count || 0) !== 1 ? 's' : ''}.
            </p>

            {importResult?.errors?.length > 0 && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm text-left">
                <div className="font-medium mb-1">Some imports failed:</div>
                {importResult.errors.map((e, i) => (
                  <div key={i}>{e}</div>
                ))}
              </div>
            )}

            <Button onClick={handleFinish}>Done</Button>
          </div>
        );

      default:
        return null;
    }
  };

  const getTitle = () => {
    switch (stage) {
      case STAGES.UPLOAD:
        return 'Import Bank Statement';
      case STAGES.PROCESSING:
        return 'Analyzing...';
      case STAGES.REVIEW:
        return 'Review Detected Bills';
      case STAGES.CONFIRMING:
        return 'Importing...';
      case STAGES.SUCCESS:
        return 'Import Complete';
      default:
        return 'Import';
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={stage === STAGES.PROCESSING || stage === STAGES.CONFIRMING ? () => {} : handleClose}
      title={getTitle()}
      size={stage === STAGES.REVIEW ? 'xl' : 'md'}
    >
      {renderContent()}
    </Modal>
  );
};

export default ImportWizard;
