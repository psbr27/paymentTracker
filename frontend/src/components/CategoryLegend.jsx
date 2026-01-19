import { CATEGORIES } from '../utils/categories';

const CategoryLegend = () => {
  return (
    <div className="flex flex-wrap gap-4 justify-center mt-4 text-sm">
      {Object.values(CATEGORIES).map((category) => (
        <div key={category.key} className="flex items-center gap-1">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: category.color }}
          />
          <span className="text-gray-600">{category.name}</span>
        </div>
      ))}
    </div>
  );
};

export default CategoryLegend;
