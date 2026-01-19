import DayTile from './DayTile';

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const CalendarGrid = ({ year, month, calendarData, onDayClick }) => {
  const firstDay = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();

  const days = [];

  // Empty cells for days before the first day of month
  for (let i = 0; i < firstDay; i++) {
    days.push(<div key={`empty-${i}`} className="p-2" />);
  }

  // Days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    const dayData = calendarData?.days?.[String(day)] || {
      total: 0,
      payments: [],
      categories: [],
    };

    const isToday =
      new Date().getDate() === day &&
      new Date().getMonth() + 1 === month &&
      new Date().getFullYear() === year;

    // Calculate column index (0-6) for tooltip positioning
    const dayIndex = (firstDay + day - 1) % 7;

    days.push(
      <DayTile
        key={day}
        day={day}
        total={dayData.total}
        categories={dayData.categories}
        payments={dayData.payments}
        dayIndex={dayIndex}
        isToday={isToday}
        hasPayments={dayData.payments.length > 0}
        onClick={() => onDayClick(day, dayData)}
      />
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="grid grid-cols-7 border-b">
        {DAYS_OF_WEEK.map((day) => (
          <div
            key={day}
            className="p-3 text-center text-sm font-medium text-gray-600"
          >
            {day}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">{days}</div>
    </div>
  );
};

export default CalendarGrid;
