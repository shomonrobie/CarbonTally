import React from 'react';

const Analytics = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">📊 Analytics</h1>
        <p className="text-gray-600">View platform performance metrics and insights</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-body text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">📈</div>
            <p>Performance analytics coming soon</p>
          </div>
        </div>

        <div className="card">
          <div className="card-body text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">📊</div>
            <p>Reports and metrics coming soon</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;