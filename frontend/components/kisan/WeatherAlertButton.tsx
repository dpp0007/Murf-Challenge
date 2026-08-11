'use client';

import { useState, useEffect } from 'react';

type CallStatus = 
  | 'IDLE' 
  | 'PREPARING' 
  | 'CONNECTING'
  | 'RINGING' 
  | 'SPEAKING' 
  | 'COMPLETED' 
  | 'FAILED'
  | 'TIMEOUT';

interface WeatherData {
  district: string;
  temperature: number;
  condition: string;
  precipitation: number;
  humidity?: number;
}

/**
 * Weather Alert Button Component
 * 
 * Allows users to request an outbound weather alert call via Linphone SIP.
 * Displays real-time call status and weather information.
 */
export function WeatherAlertButton() {
  const [status, setStatus] = useState<CallStatus>('IDLE');
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [callId, setCallId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      setIsPolling(false);
    };
  }, []);

  const triggerCall = async () => {
    try {
      setStatus('PREPARING');
      setError(null);
      setWeather(null);

      // Import userId generator
      const { getPersistentUserId } = await import('@/lib/userIdGenerator');
      const userId = getPersistentUserId();

      const response = await fetch('/api/weather-alert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          action: 'initiate_weather_alert',
          userId: userId,  // Include user ID for personalization
        }),
      });

      const data = await response.json();

      if (data.success) {
        setStatus(data.status === 'initiated' ? 'CONNECTING' : (data.status as CallStatus));
        setCallId(data.call_id);
        
        // Set weather preview if available
        if (data.weather) {
          setWeather(data.weather);
        }
        
        // Start polling for status updates
        if (data.call_id) {
          pollStatus(data.call_id);
        }
      } else {
        setStatus('FAILED');
        setError(data.message || 'Call failed. Please try again.');
      }
    } catch (err) {
      console.error('Call trigger error:', err);
      setStatus('FAILED');
      setError('Failed to initiate call. Please check your connection.');
    }
  };

  const pollStatus = (targetCallId: string) => {
    setIsPolling(true);
    
    const poll = async () => {
      try {
        const response = await fetch(`/api/weather-alert?call_id=${targetCallId}`);
        const data = await response.json();
        
        if (data.success && data.status) {
          // Map backend status to UI status
          const statusMap: { [key: string]: CallStatus } = {
            'initiated': 'CONNECTING',
            'connecting': 'CONNECTING',
            'ringing': 'RINGING',
            'connected': 'SPEAKING',
            'speaking': 'SPEAKING',
            'completed': 'COMPLETED',
            'failed': 'FAILED',
            'timeout': 'TIMEOUT',
          };
          
          const uiStatus = statusMap[data.status] || (data.status as CallStatus);
          setStatus(uiStatus);
          
          // Stop polling on terminal states
          const terminalStates: CallStatus[] = ['COMPLETED', 'FAILED', 'TIMEOUT'];
          if (terminalStates.includes(uiStatus)) {
            setIsPolling(false);
            return false;
          }
        }
        
        return true; // Continue polling
      } catch (err) {
        console.error('Status poll error:', err);
        return true; // Continue polling despite errors
      }
    };

    // Poll every 2 seconds
    let pollCount = 0;
    const maxPolls = 30; // Stop after 60 seconds (30 * 2s)
    
    const interval = setInterval(async () => {
      pollCount++;
      
      if (pollCount >= maxPolls || !isPolling) {
        clearInterval(interval);
        setIsPolling(false);
        return;
      }
      
      const shouldContinue = await poll();
      if (!shouldContinue) {
        clearInterval(interval);
        setIsPolling(false);
      }
    }, 2000);
  };

  const getStatusDisplay = (): { text: string; color: string; icon: string } => {
    switch (status) {
      case 'IDLE':
        return { text: 'Call Me Weather Alert', color: 'bg-green-600 hover:bg-green-700', icon: '🌦️' };
      case 'PREPARING':
        return { text: 'Preparing weather alert...', color: 'bg-blue-500', icon: '⏳' };
      case 'CONNECTING':
        return { text: 'Starting Linphone call...', color: 'bg-blue-500', icon: '📞' };
      case 'RINGING':
        return { text: 'Your Linphone is ringing...', color: 'bg-blue-500', icon: '📱' };
      case 'SPEAKING':
        return { text: '✓ Kisan Mitra speaking...', color: 'bg-green-600', icon: '🗣️' };
      case 'COMPLETED':
        return { text: '✓ Weather alert call completed', color: 'bg-green-700', icon: '✓' };
      case 'FAILED':
        return { text: 'Call failed — Try again', color: 'bg-red-600 hover:bg-red-700', icon: '✗' };
      case 'TIMEOUT':
        return { text: 'Call timeout — Try again', color: 'bg-orange-600 hover:bg-orange-700', icon: '⏱️' };
      default:
        return { text: 'Call Me Weather Alert', color: 'bg-green-600 hover:bg-green-700', icon: '🌦️' };
    }
  };

  const isDisabled = () => {
    const activeStates: CallStatus[] = ['PREPARING', 'CONNECTING', 'RINGING', 'SPEAKING'];
    return activeStates.includes(status);
  };

  const statusDisplay = getStatusDisplay();

  return (
    <div className="space-y-4 w-full max-w-md">
      {/* Weather Preview */}
      {weather && (
        <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl border border-blue-200 dark:border-blue-700 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold text-blue-900 dark:text-blue-100">
              Weather Alert
            </div>
            <div className="text-2xl">🌤️</div>
          </div>
          
          <div className="space-y-1 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-blue-700 dark:text-blue-300">{weather.district}</span>
              <span className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                {weather.temperature}°C
              </span>
            </div>
            
            <div className="text-blue-600 dark:text-blue-400">
              {weather.condition}
            </div>
            
            {weather.precipitation !== undefined && (
              <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                <span>💧 Rain chance:</span>
                <span className="font-semibold">{weather.precipitation}%</span>
              </div>
            )}
            
            {weather.humidity !== undefined && (
              <div className="text-xs text-blue-500 dark:text-blue-500">
                Humidity: {weather.humidity}%
              </div>
            )}
          </div>
        </div>
      )}

      {/* Call Button */}
      <button
        onClick={triggerCall}
        disabled={isDisabled()}
        className={`
          w-full px-6 py-4 rounded-xl font-medium text-white
          transition-all duration-200 transform
          disabled:opacity-60 disabled:cursor-not-allowed
          ${statusDisplay.color}
          ${!isDisabled() ? 'hover:scale-[1.02] active:scale-[0.98]' : ''}
          shadow-lg
        `}
      >
        <div className="flex items-center justify-center gap-3">
          <span className="text-2xl">{statusDisplay.icon}</span>
          <span>{statusDisplay.text}</span>
        </div>
      </button>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
          <div className="flex items-start gap-2">
            <span className="text-red-600 dark:text-red-400 text-sm">⚠️</span>
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        </div>
      )}

      {/* Help Text */}
      {status === 'IDLE' && (
        <div className="text-xs text-gray-500 dark:text-gray-400 text-center space-y-1">
          <p>Click to receive a weather alert via Linphone</p>
          <p className="text-gray-400 dark:text-gray-500">Make sure Linphone is open and logged in</p>
        </div>
      )}

      {/* SIP Connection Info */}
      {(status === 'CONNECTING' || status === 'RINGING') && (
        <div className="text-xs text-blue-600 dark:text-blue-400 text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
          Connecting via SIP to Linphone... Please make sure Linphone is running.
        </div>
      )}
    </div>
  );
}
