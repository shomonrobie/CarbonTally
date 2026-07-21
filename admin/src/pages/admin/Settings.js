import React from 'react';

const Settings = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">⚙️ Settings</h1>
        <p className="text-gray-600">Configure system settings and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-gray-900">General Settings</h3>
          </div>
          <div className="card-body space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">System Name</label>
              <input type="text" value="CarbonTally Admin" className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
              <select className="input-field">
                <option>Europe/London</option>
                <option>Europe/Paris</option>
                <option>America/New_York</option>
              </select>
            </div>
            <button className="btn-primary">Save Settings</button>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-gray-900">🔒 GDPR Compliance</h3>
          </div>
          <div className="card-body space-y-4">
            <label className="flex items-center gap-3">
              <input type="checkbox" checked className="w-4 h-4 text-primary-600" />
              <span className="text-sm text-gray-700">Anonymize user data in analytics</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" checked className="w-4 h-4 text-primary-600" />
              <span className="text-sm text-gray-700">Require consent for data processing</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" checked className="w-4 h-4 text-primary-600" />
              <span className="text-sm text-gray-700">Enable data export for users</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" checked className="w-4 h-4 text-primary-600" />
              <span className="text-sm text-gray-700">Enable data deletion (Right to be Forgotten)</span>
            </label>
            <button className="btn-primary">Save GDPR Settings</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;