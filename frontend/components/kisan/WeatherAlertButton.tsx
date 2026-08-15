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
    <div className="w-full max-w-[600px] space-y-2">
      {/* Call Button - green pill matching reference design */}
      <button
        onClick={triggerCall}
        disabled={isDisabled()}
        className={`
          w-full px-6 py-4 rounded-full font-semibold text-white text-[16px]
          transition-all duration-200 transform
          disabled:opacity-60 disabled:cursor-not-allowed
          ${statusDisplay.color}
          ${!isDisabled() ? 'hover:scale-[1.02] active:scale-[0.98]' : ''}
          shadow-[0_12px_24px_-18px_rgba(27,94,32,0.45)]
          flex items-center justify-center gap-3
        `}
      >
        <span className="text-[20px]">☁️</span>
        <span>{statusDisplay.text}</span>
        <span className="text-[20px]">→</span>
      </button>

      {/* Help Text */}
      {status === 'IDLE' && (
        <div className="text-xs text-gray-600 text-center">
          <p>Get a weather update on your phone via Linphone</p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <span className="text-red-600 text-sm">⚠️</span>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* SIP Connection Info */}
      {(status === 'CONNECTING' || status === 'RINGING') && (
        <div className="text-xs text-center p-2 bg-blue-50 rounded text-blue-700">
          Connecting via SIP to Linphone... Please make sure Linphone is running.
        </div>
      )}
    </div>
  );
}
