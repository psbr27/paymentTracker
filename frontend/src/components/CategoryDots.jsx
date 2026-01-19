import { getCategoryColor } from '../utils/categories';

const CategoryDots = ({ categories }) => {
  if (!categories || categories.length === 0) return null;

  // Show unique categories only
  const uniqueCategories = [...new Set(categories)];

  return (
    <div className="flex gap-1 flex-wrap">
      {uniqueCategories.map((category) => (
        <div
          key={category}
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: getCategoryColor(category) }}
          title={category}
        />
      ))}
    </div>
  );
};

export default CategoryDots;
