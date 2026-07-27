// frontend/src/hooks/useDocumentLogging.js
import { supabase } from '../supabaseClient';
import { useState, useCallback } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * useDocumentLogging Hook
 * Handles logging of document-related activities for audit trail
 */
export const useDocumentLogging = () => {
  const [logs, setLogs] = useState([]);
  const [isLogging, setIsLogging] = useState(false);

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  /**
   * Log an event to the backend
   */
  const logEvent = useCallback(async (eventData) => {
    try {
      setIsLogging(true);
      const token = await getToken();

      if (!token) {
        console.warn('⚠️ No token available for logging');
        return;
      }

      const payload = {
        action: eventData.action,
        resource_type: eventData.resourceType || 'document',
        resource_id: eventData.resourceId,
        details: eventData.details || {},
        metadata: {
          timestamp: new Date().toISOString(),
          user_agent: navigator.userAgent,
          url: window.location.href,
          ...eventData.metadata
        }
      };

      // Add to local state
      const logEntry = {
        id: Date.now(),
        ...payload,
        created_at: new Date().toISOString()
      };
      setLogs(prev => [logEntry, ...prev]);

      // Send to backend
      const response = await fetch(`${API_URL}/api/logs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        console.warn('⚠️ Failed to log event:', await response.text());
      }

      return logEntry;

    } catch (error) {
      console.error('❌ Error logging event:', error);
      // Don't throw - logging should not break the main flow
    } finally {
      setIsLogging(false);
    }
  }, []);

  /**
   * Log a document upload event
   */
  const logDocumentUpload = useCallback(async (fileData, metadata = {}) => {
    return logEvent({
      action: 'document_upload',
      resourceType: 'document',
      resourceId: fileData.id,
      details: {
        file_name: fileData.name,
        file_size: fileData.size,
        file_type: fileData.type,
        data_type: fileData.data_type,
        ...metadata
      },
      metadata: {
        ...metadata,
        event_category: 'upload'
      }
    });
  }, [logEvent]);

  /**
   * Log a document extraction event
   */
  const logExtraction = useCallback(async (fileId, result, metadata = {}) => {
    return logEvent({
      action: result.success ? 'extraction_success' : 'extraction_failure',
      resourceType: 'document',
      resourceId: fileId,
      details: {
        confidence_score: result.confidence || 0,
        issues: result.issues || [],
        fields_extracted: result.fields_extracted || 0,
        extraction_time_ms: result.duration_ms || 0,
        ...metadata
      },
      metadata: {
        ...metadata,
        event_category: 'extraction'
      }
    });
  }, [logEvent]);

  /**
   * Log a manual entry event
   */
  const logManualEntry = useCallback(async (fileId, data, metadata = {}) => {
    return logEvent({
      action: 'manual_entry',
      resourceType: 'document',
      resourceId: fileId,
      details: {
        fields_entered: Object.keys(data).length,
        ...metadata
      },
      metadata: {
        ...metadata,
        event_category: 'manual_entry'
      }
    });
  }, [logEvent]);

  /**
   * Log a document approval/rejection event
   */
  const logDocumentDecision = useCallback(async (fileId, decision, notes = '', metadata = {}) => {
    return logEvent({
      action: decision === 'approve' ? 'document_approved' : 'document_rejected',
      resourceType: 'document',
      resourceId: fileId,
      details: {
        decision,
        notes,
        ...metadata
      },
      metadata: {
        ...metadata,
        event_category: 'decision'
      }
    });
  }, [logEvent]);

  /**
   * Log an error event
   */
  const logError = useCallback(async (error, context = {}, metadata = {}) => {
    return logEvent({
      action: 'error_occurred',
      resourceType: 'document',
      resourceId: context.fileId,
      details: {
        error_message: error.message || String(error),
        error_stack: error.stack,
        context,
        ...metadata
      },
      metadata: {
        ...metadata,
        event_category: 'error',
        severity: 'error'
      }
    });
  }, [logEvent]);

  /**
   * Log a user action
   */
  const logUserAction = useCallback(async (action, details = {}, metadata = {}) => {
    return logEvent({
      action: `user_${action}`,
      resourceType: 'user',
      details,
      metadata: {
        ...metadata,
        event_category: 'user_action'
      }
    });
  }, [logEvent]);

  /**
   * Get recent logs
   */
  const getRecentLogs = useCallback(async (limit = 50) => {
    try {
      const token = await getToken();
      
      if (!token) {
        console.warn('⚠️ No token available');
        return [];
      }

      const response = await fetch(`${API_URL}/api/logs?limit=${limit}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        return data.logs || [];
      }
      
      return [];
    } catch (error) {
      console.error('❌ Error fetching logs:', error);
      return [];
    }
  }, []);

  return {
    logs,
    isLogging,
    logEvent,
    logDocumentUpload,
    logExtraction,
    logManualEntry,
    logDocumentDecision,
    logError,
    logUserAction,
    getRecentLogs
  };
};

export default useDocumentLogging;