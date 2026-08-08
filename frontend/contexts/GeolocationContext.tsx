'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

export interface GeolocationCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

interface GeolocationContextType {
  coordinates: GeolocationCoordinates | null;
  loading: boolean;
  error: string | null;
}

const GeolocationContext = createContext<GeolocationContextType | undefined>(undefined);

export function GeolocationProvider({ children }: { children: React.ReactNode }) {
  const [coordinates, setCoordinates] = useState<GeolocationCoordinates | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError('Geolocation not supported');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        setCoordinates({ latitude, longitude, accuracy });
        setLoading(false);
      },
      (err) => {
        let msg = 'Location unavailable';
        if (err.code === err.PERMISSION_DENIED) {
          msg = 'Enable location permission for weather data';
        }
        setError(msg);
        setLoading(false);

        // Try cached location
        try {
          const cached = localStorage.getItem('user_coordinates');
          if (cached) {
            const parsed = JSON.parse(cached);
            setCoordinates(parsed);
          }
        } catch {
          // ignore
        }
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
    );
  }, []);

  return (
    <GeolocationContext.Provider value={{ coordinates, loading, error }}>
      {children}
    </GeolocationContext.Provider>
  );
}

export function useGeolocationContext() {
  const context = useContext(GeolocationContext);
  if (!context) {
    throw new Error('useGeolocationContext must be used within GeolocationProvider');
  }
  return context;
}
