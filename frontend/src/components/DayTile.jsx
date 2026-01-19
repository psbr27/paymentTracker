import { useState, useRef } from 'react';
import CategoryDots from './CategoryDots';
import PaymentTooltip from './PaymentTooltip';
import { formatCurrency } from '../utils/currency';

const getAmountBackgroundColor = (total) => {
  if (total >= 3000) return 'bg-red-50';
  if (total >= 1000) return 'bg-orange-50';
  if (total >= 500) return 'bg-yellow-50';
  if (total >= 200) return 'bg-green-50';
  return '';
};

const DayTile = ({ day, total, categories, payments, dayIndex, isToday, hasPayments, onClick }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const hoverTimeoutRef = useRef(null);

  // Show tooltip on left side for tiles in right half of calendar (columns 4-6)
  const tooltipPosition = dayIndex >= 4 ? 'left' : 'right';

  // Get background color based on amount (only if not today)
  const amountBgColor = !isToday && hasPayments ? getAmountBackgroundColor(total) : '';

  const handleMouseEnter = () => {
    if (hasPayments) {
      hoverTimeoutRef.current = setTimeout(() => {
        setShowTooltip(true);
      }, 150);
    }
  };

  const handleMouseLeave = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    setShowTooltip(false);
  };

  const handleClick = () => {
    setShowTooltip(false);
    onClick();
  };

  return (
    <div
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`
        relative p-2 min-h-[80px] border-b border-r cursor-pointer
        transition-colors hover:bg-gray-100
        ${isToday ? 'bg-blue-50' : amountBgColor}
      `}
    >
      <div className="flex flex-col h-full">
        <span
          className={`
            text-sm font-medium
            ${isToday ? 'text-blue-600' : 'text-gray-700'}
          `}
        >
          {day}
        </span>

        {hasPayments && (
          <>
            <span className="text-sm font-semibold text-gray-900 mt-1">
              {formatCurrency(total)}
            </span>
            <div className="mt-auto pt-1">
              <CategoryDots categories={categories} />
            </div>
          </>
        )}
      </div>

      {showTooltip && hasPayments && (
        <PaymentTooltip
          day={day}
          payments={payments}
          total={total}
          position={tooltipPosition}
        />
      )}
    </div>
  );
};

export default DayTile;
