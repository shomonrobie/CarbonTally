// frontend/src/context/ReferenceDataContext.jsx
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabaseClient';

const ReferenceDataContext = createContext();

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const ReferenceDataProvider = ({ children }) => {
  const [fuelTypes, setFuelTypes] = useState([]);
  const [units, setUnits] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetched, setLastFetched] = useState(null);
  const [organizationId, setOrganizationId] = useState(null);

  // Cache expiration: 1 hour
  const CACHE_EXPIRY = 60 * 60 * 1000;

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  const fetchReferenceData = useCallback(async (forceRefresh = false, orgId = null) => {
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
      // Fetch fuel types and units (no org ID needed)
      const promises = [
        fetch(`${API_URL}/api/reference/fuel-types`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/reference/units`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ];

      // ✅ If organization ID is provided, fetch facilities too
      const effectiveOrgId = orgId || organizationId;
      if (effectiveOrgId) {
        promises.push(
          fetch(`${API_URL}/api/organizations/${effectiveOrgId}/facilities?limit=1000`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
        );
      }

      const responses = await Promise.all(promises);
      
      // Process fuel types response
      if (responses[0].ok) {
        const data = await responses[0].json();
        setFuelTypes(data.fuel_types || []);
        console.log('✅ Fuel types cached:', data.fuel_types?.length || 0);
      } else {
        console.warn('⚠️ Fuel types fetch failed:', responses[0].status);
      }

      // Process units response
      if (responses[1].ok) {
        const data = await responses[1].json();
        setUnits(data.units || []);
        console.log('✅ Units cached:', data.units?.length || 0);
      } else {
        console.warn('⚠️ Units fetch failed:', responses[1].status);
      }

      // Process facilities response (if it exists)
      if (responses.length > 2 && responses[2].ok) {
        const data = await responses[2].json();
        setFacilities(data.facilities || []);
        console.log('✅ Facilities cached:', data.facilities?.length || 0);
      } else if (responses.length > 2) {
        console.warn('⚠️ Facilities fetch failed:', responses[2].status);
      }

      setLastFetched(Date.now());
    } catch (error) {
      console.error('❌ Error fetching reference data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [lastFetched, organizationId]);

  // Fetch on first mount
  useEffect(() => {
    fetchReferenceData();
  }, []);

  // Fetch facilities when organization ID changes
  useEffect(() => {
    if (organizationId) {
      // Only fetch facilities, use cached fuel types and units
      const fetchFacilitiesOnly = async () => {
        const token = await getToken();
        if (!token) return;

        try {
          const response = await fetch(
            `${API_URL}/api/organizations/${organizationId}/facilities?limit=1000`,
            {
              headers: { 'Authorization': `Bearer ${token}` }
            }
          );
          
          if (response.ok) {
            const data = await response.json();
            setFacilities(data.facilities || []);
            console.log('✅ Facilities loaded for org:', data.facilities?.length || 0);
          }
        } catch (error) {
          console.error('Error fetching facilities:', error);
        }
      };

      fetchFacilitiesOnly();
    }
  }, [organizationId]);

  // Force refresh function
  const refreshData = (orgId = null) => {
    console.log('🔄 Forcing refresh of reference data...');
    return fetchReferenceData(true, orgId);
  };

  // Set organization ID to trigger facility fetch
  const setOrganization = (orgId) => {
    setOrganizationId(orgId);
  };

  // Helper functions
  const getFacilityById = (id) => {
    return facilities.find(f => f.id === id);
  };

  const getFacilitiesByOrganization = (orgId) => {
    return facilities.filter(f => f.organization_id === orgId);
  };

  const getFuelTypeByName = (name) => {
    return fuelTypes.find(f => f.name === name || f.fuel_type === name);
  };

  const getUnitByName = (name) => {
    return units.find(u => u.name === name || u.unit === name);
  };

  const value = {
    fuelTypes,
    units,
    facilities,
    loading,
    error,
    refreshData,
    lastFetched,
    setOrganization,
    getFacilityById,
    getFacilitiesByOrganization,
    getFuelTypeByName,
    getUnitByName,
    organizationId
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