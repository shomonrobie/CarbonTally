import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const ReviewStatusChart = ({ stats }) => {
  const data = [
    { name: 'Pending', value: stats.pending || 0, color: '#f59e0b' },
    { name: 'In Progress', value: stats.inProgress || 0, color: '#3b82f6' },
    { name: 'Completed', value: stats.completed || 0, color: '#22c55e' },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold text-gray-900">📊 Review Status Distribution</h3>
        <p className="text-sm text-gray-500">Current queue breakdown</p>
      </div>
      <div className="card-body">
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={5}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default ReviewStatusChart;