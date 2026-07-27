// src/Settings.jsx

import React, { useState, useEffect } from 'react';
import { supabase } from '../../supabaseClient';
import toast from 'react-hot-toast';
import { FaSave, FaSpinner, FaDatabase, FaUpload, FaShieldAlt, FaClock } from 'react-icons/fa';

const Settings = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    // General Settings
    system_name: 'CarbonTally Admin',
    timezone: 'Europe/London',
    
    // File Upload Settings
    max_file_size_mb: 50,
    allowed_file_types: ['pdf', 'csv', 'xlsx', 'jpg', 'jpeg', 'png'],
    enable_auto_repair: true,
    max_batch_files: 20,
    max_total_batch_size_mb: 200,
    
    // GDPR Settings
    anonymize_analytics: true,
    require_consent: true,
    enable_data_export: true,
    enable_data_deletion: true,
    data_retention_days: 365,
    
    // Security Settings
    require_2fa: false,
    session_timeout_minutes: 60,
    max_login_attempts: 5,
    
    // Performance Settings
    enable_caching: true,
    cache_duration_minutes: 15,
    enable_async_processing: true,
    max_concurrent_jobs: 10,
    
    // Notification Settings
    email_notifications: true,
    email_alerts: true,
    weekly_reports: true
  });

  const [availableTimezones] = useState([
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'America/New_York',
    'America/Los_Angeles',
    'Asia/Dubai',
    'Asia/Singapore',
    'Australia/Sydney'
  ]);

  // Load settings from database on mount
  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      
      // First, try to get settings from system_settings table
      const { data, error } = await supabase
        .from('system_settings')
        .select('*')
        .single();

      if (error) {
        if (error.code === 'PGRST116') {
          // No settings found, create default settings
          console.log('📝 No settings found, creating defaults...');
          await createDefaultSettings();
        } else {
          console.error('❌ Error fetching settings:', error);
          toast.error('Failed to load settings');
        }
        return;
      }

      if (data) {
        console.log('✅ Settings loaded:', data);
        // Parse settings JSON if stored as JSON
        if (data.settings_json) {
          setSettings(prev => ({
            ...prev,
            ...data.settings_json
          }));
        } else {
          // Fallback: use individual columns
          setSettings(prev => ({
            ...prev,
            max_file_size_mb: data.max_file_size_mb || 50,
            allowed_file_types: data.allowed_file_types || ['pdf', 'csv', 'xlsx', 'jpg', 'jpeg', 'png'],
            enable_auto_repair: data.enable_auto_repair !== false,
            max_batch_files: data.max_batch_files || 20,
            max_total_batch_size_mb: data.max_total_batch_size_mb || 200,
            data_retention_days: data.data_retention_days || 365,
            require_2fa: data.require_2fa || false,
            session_timeout_minutes: data.session_timeout_minutes || 60,
            max_login_attempts: data.max_login_attempts || 5
          }));
        }
      }
    } catch (error) {
      console.error('❌ Error loading settings:', error);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const createDefaultSettings = async () => {
    try {
      const { data, error } = await supabase
        .from('system_settings')
        .insert({
          settings_json: settings,
          max_file_size_mb: settings.max_file_size_mb,
          allowed_file_types: settings.allowed_file_types,
          enable_auto_repair: settings.enable_auto_repair,
          data_retention_days: settings.data_retention_days,
          updated_at: new Date().toISOString(),
          updated_by: (await supabase.auth.getUser()).data.user?.id
        })
        .select()
        .single();

      if (error) throw error;
      console.log('✅ Default settings created:', data);
    } catch (error) {
      console.error('❌ Error creating default settings:', error);
      toast.error('Failed to create default settings');
    }
  };

  const handleInputChange = (section, field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCheckboxChange = (section, field) => {
    setSettings(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      
      // Get current user
      const { data: { user } } = await supabase.auth.getUser();
      
      // Update settings in database
      const { data, error } = await supabase
        .from('system_settings')
        .upsert({
          settings_json: settings,
          max_file_size_mb: settings.max_file_size_mb,
          allowed_file_types: settings.allowed_file_types,
          enable_auto_repair: settings.enable_auto_repair,
          max_batch_files: settings.max_batch_files,
          max_total_batch_size_mb: settings.max_total_batch_size_mb,
          data_retention_days: settings.data_retention_days,
          require_2fa: settings.require_2fa,
          session_timeout_minutes: settings.session_timeout_minutes,
          max_login_attempts: settings.max_login_attempts,
          updated_at: new Date().toISOString(),
          updated_by: user?.id
        }, {
          onConflict: 'id'
        })
        .select()
        .single();

      if (error) throw error;
      
      toast.success('✅ Settings saved successfully!');
      console.log('✅ Settings saved:', data);
    } catch (error) {
      console.error('❌ Error saving settings:', error);
      toast.error('Failed to save settings: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  // Format file size for display
  const formatFileSize = (mb) => {
    if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
    return `${mb} MB`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <FaSpinner className="animate-spin text-primary-600 text-4xl mx-auto mb-4" />
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">⚙️ Settings</h1>
        <p className="text-gray-600">Configure system settings and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* General Settings */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <FaDatabase className="text-primary-600" />
            <h3 className="font-semibold text-gray-900">General Settings</h3>
          </div>
          <div className="card-body space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">System Name</label>
              <input 
                type="text" 
                value={settings.system_name} 
                onChange={(e) => handleInputChange('general', 'system_name', e.target.value)}
                className="input-field w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
              <select 
                value={settings.timezone}
                onChange={(e) => handleInputChange('general', 'timezone', e.target.value)}
                className="input-field w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {availableTimezones.map(tz => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>
            <button 
              onClick={handleSaveSettings}
              disabled={saving}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {saving ? <FaSpinner className="animate-spin" /> : <FaSave />}
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>

        {/* File Upload Settings - NEW */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <FaUpload className="text-primary-600" />
            <h3 className="font-semibold text-gray-900">📤 File Upload Settings</h3>
          </div>
          <div className="card-body space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max File Size: {formatFileSize(settings.max_file_size_mb)}
              </label>
              <input 
                type="range" 
                min="5" 
                max="500" 
                step="5"
                value={settings.max_file_size_mb}
                onChange={(e) => handleInputChange('upload', 'max_file_size_mb', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>5 MB</span>
                <span>500 MB</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Batch Files
              </label>
              <input 
                type="number" 
                min="1" 
                max="100"
                value={settings.max_batch_files}
                onChange={(e) => handleInputChange('upload', 'max_batch_files', parseInt(e.target.value))}
                className="input-field w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Total Batch Size: {formatFileSize(settings.max_total_batch_size_mb)}
              </label>
              <input 
                type="range" 
                min="50" 
                max="1000" 
                step="50"
                value={settings.max_total_batch_size_mb}
                onChange={(e) => handleInputChange('upload', 'max_total_batch_size_mb', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>50 MB</span>
                <span>1 GB</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Allowed File Types</label>
              <div className="flex flex-wrap gap-2">
                {['pdf', 'csv', 'xlsx', 'jpg', 'jpeg', 'png', 'tiff'].map(type => (
                  <label key={type} className="flex items-center gap-2">
                    <input 
                      type="checkbox"
                      checked={settings.allowed_file_types.includes(type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleInputChange('upload', 'allowed_file_types', [...settings.allowed_file_types, type]);
                        } else {
                          handleInputChange('upload', 'allowed_file_types', settings.allowed_file_types.filter(t => t !== type));
                        }
                      }}
                      className="w-4 h-4 text-primary-600"
                    />
                    <span className="text-sm text-gray-700">{type.toUpperCase()}</span>
                  </label>
                ))}
              </div>
            </div>

            <label className="flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={settings.enable_auto_repair}
                onChange={() => handleCheckboxChange('upload', 'enable_auto_repair')}
                className="w-4 h-4 text-primary-600" 
              />
              <span className="text-sm text-gray-700">🔧 Enable auto-repair for corrupted PDFs</span>
            </label>

            <button 
              onClick={handleSaveSettings}
              disabled={saving}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {saving ? <FaSpinner className="animate-spin" /> : <FaSave />}
              {saving ? 'Saving...' : 'Save Upload Settings'}
            </button>
          </div>
        </div>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* GDPR & Security Settings */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <FaShieldAlt className="text-primary-600" />
            <h3 className="font-semibold text-gray-900">🔒 GDPR & Security</h3>
          </div>
          <div className="card-body space-y-4">
            <label className="flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={settings.anonymize_analytics}
                onChange={() => handleCheckboxChange('gdpr', 'anonymize_analytics')}
                className="w-4 h-4 text-primary-600" 
              />
              <span className="text-sm text-gray-700">Anonymize user data in analytics</span>
            </label>
            <label className="flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={settings.require_consent}
                onChange={() => handleCheckboxChange('gdpr', 'require_consent')}
                className="w-4 h-4 text-primary-600" 
              />
              <span className="text-sm text-gray-700">Require consent for data processing</span>
            </label>
            <label className="flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={settings.enable_data_export}
                onChange={() => handleCheckboxChange('gdpr', 'enable_data_export')}
                className="w-4 h-4 text-primary-600" 
              />
              <span className="text-sm text-gray-700">Enable data export for users</span>
            </label>
            <label className="flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={settings.enable_data_deletion}
                onChange={() => handleCheckboxChange('gdpr', 'enable_data_deletion')}
                className="w-4 h-4 text-primary-600" 
              />
              <span className="text-sm text-gray-700">Enable data deletion (Right to be Forgotten)</span>
            </label>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Retention Period (days)
              </label>
              <input 
                type="number" 
                min="30" 
                max="730"
                value={settings.data_retention_days}
                onChange={(e) => handleInputChange('gdpr', 'data_retention_days', parseInt(e.target.value))}
                className="input-field w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <button 
              onClick={handleSaveSettings}
              disabled={saving}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {saving ? <FaSpinner className="animate-spin" /> : <FaSave />}
              {saving ? 'Saving...' : 'Save GDPR Settings'}
            </button>
          </div>
        </div>

        {/* Session & Notification Settings */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <FaClock className="text-primary-600" />
            <h3 className="font-semibold text-gray-900">⏱️ Session & Notifications</h3>
          </div>
          <div className="card-body space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Session Timeout (minutes)
              </label>
              <input 
                type="number" 
                min="5" 
                max="480"
                value={settings.session_timeout_minutes}
                onChange={(e) => handleInputChange('session', 'session_timeout_minutes', parseInt(e.target.value))}
                className="input-field w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Login Attempts
              </label>
              <input 
                type="number" 
                min="3" 
                max="10"
                value={settings.max_login_attempts}
                onChange={(e) => handleInputChange('session', 'max_login_attempts', parseInt(e.target.value))}
                className="input-field w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <label className="flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={settings.require_2fa}
                onChange={() => handleCheckboxChange('security', 'require_2fa')}
                className="w-4 h-4 text-primary-600" 
              />
              <span className="text-sm text-gray-700">Require Two-Factor Authentication</span>
            </label>
            <hr className="border-gray-200" />
            <label className="flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={settings.email_notifications}
                onChange={() => handleCheckboxChange('notifications', 'email_notifications')}
                className="w-4 h-4 text-primary-600" 
              />
              <span className="text-sm text-gray-700">Email Notifications</span>
            </label>
            <label className="flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={settings.email_alerts}
                onChange={() => handleCheckboxChange('notifications', 'email_alerts')}
                className="w-4 h-4 text-primary-600" 
              />
              <span className="text-sm text-gray-700">Email Alerts</span>
            </label>
            <label className="flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={settings.weekly_reports}
                onChange={() => handleCheckboxChange('notifications', 'weekly_reports')}
                className="w-4 h-4 text-primary-600" 
              />
              <span className="text-sm text-gray-700">Weekly Reports</span>
            </label>
            <button 
              onClick={handleSaveSettings}
              disabled={saving}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {saving ? <FaSpinner className="animate-spin" /> : <FaSave />}
              {saving ? 'Saving...' : 'Save Session Settings'}
            </button>
          </div>
        </div>
      </div>

      {/* Settings Summary */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-3">
          <div className="text-blue-600 text-xl">ℹ️</div>
          <div>
            <h4 className="font-medium text-blue-900">Current File Settings</h4>
            <ul className="text-sm text-blue-700 mt-1 space-y-1">
              <li>• Max file size: <strong>{formatFileSize(settings.max_file_size_mb)}</strong></li>
              <li>• Allowed types: <strong>{settings.allowed_file_types.join(', ').toUpperCase()}</strong></li>
              <li>• Auto-repair: <strong>{settings.enable_auto_repair ? 'Enabled' : 'Disabled'}</strong></li>
              <li>• Max batch files: <strong>{settings.max_batch_files}</strong></li>
              <li>• Max total batch size: <strong>{formatFileSize(settings.max_total_batch_size_mb)}</strong></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;