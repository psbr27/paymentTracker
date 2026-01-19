import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import CalendarGrid from '../components/CalendarGrid';
import MonthNavigator from '../components/MonthNavigator';
import CategoryLegend from '../components/CategoryLegend';
import SummaryBar from '../components/SummaryBar';
import SlidePanel from '../components/SlidePanel';
import DayDetail from '../components/DayDetail';
import PaymentForm from '../components/PaymentForm';
import ImportWizard from '../components/ImportWizard';
import Modal from '../components/ui/Modal';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';
import { getCalendarData } from '../services/calendar';
import { createPayment, updatePayment, deletePayment } from '../services/payments';
import { exportPayments } from '../services/settings';

const CalendarPage = () => {
  const navigate = useNavigate();
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [calendarData, setCalendarData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Slide panel state
  const [selectedDay, setSelectedDay] = useState(null);
  const [selectedDayData, setSelectedDayData] = useState(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // Payment form state
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingPayment, setEditingPayment] = useState(null);
  const [defaultDate, setDefaultDate] = useState(null);

  // Delete confirmation state
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  // Import wizard state
  const [isImportOpen, setIsImportOpen] = useState(false);

  useEffect(() => {
    loadCalendarData();
  }, [year, month]);

  const loadCalendarData = async () => {
    setLoading(true);
    try {
      const data = await getCalendarData(year, month);
      setCalendarData(data);
    } catch (error) {
      console.error('Failed to load calendar data:', error);
    }
    setLoading(false);
  };

  const handlePrevMonth = () => {
    if (month === 1) {
      setMonth(12);
      setYear(year - 1);
    } else {
      setMonth(month - 1);
    }
  };

  const handleNextMonth = () => {
    if (month === 12) {
      setMonth(1);
      setYear(year + 1);
    } else {
      setMonth(month + 1);
    }
  };

  const handleDayClick = (day, dayData) => {
    setSelectedDay(day);
    setSelectedDayData(dayData);
    setIsPanelOpen(true);
  };

  const handleAddPayment = () => {
    setEditingPayment(null);
    setDefaultDate(null);
    setIsFormOpen(true);
  };

  const handleAddPaymentToDay = () => {
    setEditingPayment(null);
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(selectedDay).padStart(2, '0')}`;
    setDefaultDate(dateStr);
    setIsFormOpen(true);
  };

  const handleEditPayment = (payment) => {
    setEditingPayment(payment);
    setDefaultDate(null);
    setIsFormOpen(true);
  };

  const handleDeletePayment = (payment) => {
    setDeleteConfirm(payment);
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;
    try {
      await deletePayment(deleteConfirm.id);
      setDeleteConfirm(null);
      await loadCalendarData();
      // Update slide panel data if open
      if (isPanelOpen && selectedDay) {
        const newData = calendarData?.days?.[String(selectedDay)];
        setSelectedDayData(newData);
      }
    } catch (error) {
      console.error('Failed to delete payment:', error);
    }
  };

  const handleFormSubmit = async (data) => {
    try {
      if (editingPayment) {
        await updatePayment(editingPayment.id, data);
      } else {
        await createPayment(data);
      }
      setIsFormOpen(false);
      await loadCalendarData();
    } catch (error) {
      console.error('Failed to save payment:', error);
    }
  };

  const handleExport = async () => {
    try {
      const blob = await exportPayments({ year, month });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `payments-${year}-${month}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to export:', error);
    }
  };

  const handleImport = () => {
    setIsImportOpen(true);
  };

  const handleImportComplete = () => {
    setIsImportOpen(false);
    loadCalendarData();
  };

  const handleYearClick = () => {
    navigate(`/year/${year}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onYearClick={handleYearClick} currentYear={year} />

      <main className="max-w-7xl mx-auto px-4 py-6">
        <SummaryBar
          calendarData={calendarData}
          onAddPayment={handleAddPayment}
          onImport={handleImport}
          onExport={handleExport}
        />

        <MonthNavigator
          year={year}
          month={month}
          onPrev={handlePrevMonth}
          onNext={handleNextMonth}
          onYearClick={handleYearClick}
        />

        {loading ? (
          <div className="flex justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : (
          <CalendarGrid
            year={year}
            month={month}
            calendarData={calendarData}
            onDayClick={handleDayClick}
          />
        )}

        <CategoryLegend />
      </main>

      {/* Day Detail Slide Panel */}
      <SlidePanel
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
        title="Day Details"
      >
        {selectedDay && (
          <DayDetail
            year={year}
            month={month}
            day={selectedDay}
            dayData={selectedDayData}
            onEdit={handleEditPayment}
            onDelete={handleDeletePayment}
            onAddPayment={handleAddPaymentToDay}
          />
        )}
      </SlidePanel>

      {/* Payment Form Modal */}
      <PaymentForm
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        payment={editingPayment}
        defaultDate={defaultDate}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        title="Delete Payment"
        size="sm"
      >
        <p className="mb-4">
          Are you sure you want to delete "{deleteConfirm?.name}"?
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setDeleteConfirm(null)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Delete
          </Button>
        </div>
      </Modal>

      {/* Import Wizard */}
      <ImportWizard
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        onComplete={handleImportComplete}
      />
    </div>
  );
};

export default CalendarPage;
