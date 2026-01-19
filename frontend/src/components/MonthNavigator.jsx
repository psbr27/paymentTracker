import Button from './ui/Button';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const MonthNavigator = ({ year, month, onPrev, onNext, onYearClick }) => {
  return (
    <div className="flex items-center justify-center gap-4 mb-4">
      <Button variant="ghost" onClick={onPrev}>
        &lt;
      </Button>
      <h2
        className="text-xl font-semibold min-w-[200px] text-center cursor-pointer hover:text-blue-600"
        onClick={onYearClick}
      >
        {MONTH_NAMES[month - 1]} {year}
      </h2>
      <Button variant="ghost" onClick={onNext}>
        &gt;
      </Button>
    </div>
  );
};

export default MonthNavigator;
