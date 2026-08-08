'use client';

import { useEffect, useState, useCallback } from 'react';

export interface GeolocationCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  altitude?: number | null;
  altitudeAccuracy?: number | null;
  heading?: number | null;
  speed?: number | null;
}

export interface UseGeolocationReturn {
  coordinates: GeolocationCoordinates | null;
  loading: boolean;
  error: string | null;
  requestPermission: () => void;
  clearLocation: () => void;
}

/**
 * Hook to get user's geolocation for weather queries.
 * Requests permission when component mounts, with manual retry option.
 */
export function useGeolocation(): UseGeolocationReturn {
  const [coordinates, setCoordinates] = useState<GeolocationCoordinates | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const requestGeolocation = useCallback(() => {
    setLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy, altitude, altitudeAccuracy, heading, speed } =
          position.coords;
        setCoordinates({
          latitude,
          longitude,
          accuracy,
          altitude,
          altitudeAccuracy,
          heading,
          speed,
        });
        setLoading(false);
        localStorage.setItem(
          'user_coordinates',
          JSON.stringify({
            latitude,
            longitude,
            timestamp: new Date().toISOString(),
          })
        );
      },
      (err) => {
        let errorMessage = 'Unable to retrieve location';
        switch (err.code) {
          case err.PERMISSION_DENIED:
            errorMessage = 'Location permission denied. Enable it to get weather data.';
            break;
          case err.POSITION_UNAVAILABLE:
            errorMessage = 'Location information is unavailable.';
            break;
          case err.TIMEOUT:
            errorMessage = 'Location request timed out.';
            break;
        }
        setError(errorMessage);
        setLoading(false);

        // Try to use cached location if available
        try {
          const cached = localStorage.getItem('user_coordinates');
          if (cached) {
            const parsed = JSON.parse(cached);
            setCoordinates({
              latitude: parsed.latitude,
              longitude: parsed.longitude,
            });
            setError('Using cached location. Please enable location permission for current data.');
          }
        } catch {
          // Ignore parsing errors
        }
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000, // 5 minutes cache
      }
    );
  }, []);

  const clearLocation = useCallback(() => {
    setCoordinates(null);
    localStorage.removeItem('user_coordinates');
  }, []);

  // Request geolocation on mount
  useEffect(() => {
    requestGeolocation();
  }, [requestGeolocation]);

  return {
    coordinates,
    loading,
    error,
    requestPermission: requestGeolocation,
    clearLocation,
  };
}
