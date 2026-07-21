import React from 'react';

const StatCard = ({ title, value, change, icon: Icon, color, bgColor }) => {
  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <span className={`text-xs font-medium ${
              change.startsWith('+') ? 'text-green-600' : 'text-red-600'
            }`}>
              {change}
            </span>
          )}
        </div>
        <div className={`${bgColor} ${color} stat-icon`}>
          <Icon />
        </div>
      </div>
    </div>
  );
};

export default StatCard;