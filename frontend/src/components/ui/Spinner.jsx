const sizes = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-10 h-10',
};

const Spinner = ({ size = 'md', className = '' }) => {
  return (
    <div
      className={`
        ${sizes[size]}
        border-2 border-gray-200 border-t-blue-500
        rounded-full animate-spin
        ${className}
      `}
    />
  );
};

export default Spinner;
