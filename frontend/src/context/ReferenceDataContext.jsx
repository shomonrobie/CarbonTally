// frontend/src/context/ReferenceDataContext.jsx
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabaseClient';

const ReferenceDataContext = createContext();

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const ReferenceDataProvider = ({ children }) => {
  const [fuelTypes, setFuelTypes] = useState([]);
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetched, setLastFetched] = useState(null);

  // Cache expiration: 1 hour
  const CACHE_EXPIRY = 60 * 60 * 1000;

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  const fetchReferenceData = useCallback(async (forceRefresh = false) => {
    // Check if cache is still valid
    if (!forceRefresh && lastFetched && (Date.now() - lastFetched) < CACHE_EXPIRY) {
      console.log('📦 Using cached reference data');
      return;
    }

    console.log('📡 Fetching fresh reference data...');
    setLoading(true);
    setError(null);

    const token = await getToken();
    if (!token) {
      setError('No authentication token available');
      setLoading(false);
      return;
    }

    try {
      // Fetch all data in parallel
      const [fuelResponse, unitResponse] = await Promise.all([
        fetch(`${API_URL}/api/reference/fuel-types`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/reference/units`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (fuelResponse.ok) {
        const data = await fuelResponse.json();
        setFuelTypes(data.fuel_types || []);
        console.log('✅ Fuel types cached:', data.fuel_types?.length || 0);
      } else {
        console.warn('⚠️ Fuel types fetch failed:', fuelResponse.status);
      }

      if (unitResponse.ok) {
        const data = await unitResponse.json();
        setUnits(data.units || []);
        console.log('✅ Units cached:', data.units?.length || 0);
      } else {
        console.warn('⚠️ Units fetch failed:', unitResponse.status);
      }

      setLastFetched(Date.now());
    } catch (error) {
      console.error('❌ Error fetching reference data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [lastFetched]);

  // Fetch on first mount
  useEffect(() => {
    fetchReferenceData();
  }, []);

  // Force refresh function
  const refreshData = () => {
    console.log('🔄 Forcing refresh of reference data...');
    return fetchReferenceData(true);
  };

  const value = {
    fuelTypes,
    units,
    loading,
    error,
    refreshData,
    lastFetched
  };

  return (
    <ReferenceDataContext.Provider value={value}>
      {children}
    </ReferenceDataContext.Provider>
  );
};

export const useReferenceData = () => {
  const context = useContext(ReferenceDataContext);
  if (!context) {
    throw new Error('useReferenceData must be used within a ReferenceDataProvider');
  }
  return context;
};