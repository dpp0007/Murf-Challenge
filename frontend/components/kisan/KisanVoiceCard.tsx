'use client';

import React from 'react';
import { Loader2, Mic, MicOff, PhoneOff, Volume2 } from 'lucide-react';
import type { KisanVoiceState } from './KisanMainView';
import { useLanguage } from '@/contexts/LanguageContext';

interface KisanVoiceCardProps {
  voiceState: KisanVoiceState;
  audioLevel: number;
  isMuted: boolean;
  canUseButton: boolean;
  isConnected: boolean;
  onStartCall: () => void;
  onEndCall: () => void;
  onToggleMic: () => void;
}

export function KisanVoiceCard({
  voiceState,
  audioLevel,
  isMuted,
  canUseButton,
  isConnected,
  onStartCall,
  onEndCall,
  onToggleMic,
}: KisanVoiceCardProps) {
  const { t } = useLanguage();
  const isActive = voiceState === 'connecting' || voiceState === 'listening' || voiceState === 'speaking';
  const isReady = voiceState === 'ready';
  const isEnded = voiceState === 'ended';
  const isRestartable = isEnded || voiceState === 'error';
  const isSpeaking = voiceState === 'speaking';
  const isListening = voiceState === 'listening';
  const isConnecting = voiceState === 'connecting';
  const orbSizeClasses = 'h-[96px] w-[96px] sm:h-[100px] sm:w-[100px]';

  const status = (() => {
    switch (voiceState) {
      case 'connecting':
        return {
          title: t.connecting,
          subtitle: t.connectingSubtitle,
          dot: 'bg-[#F9A825]',
          icon: <Loader2 className="h-5 w-5 animate-spin text-[#2E7D32]" strokeWidth={2.1} />,
        };
      case 'listening':
        return {
          title: t.listening,
          subtitle: t.listeningSubtitle,
          dot: 'bg-[#2E7D32]',
          icon: <Mic className="h-5 w-5 text-[#2E7D32]" strokeWidth={2} />,
        };
      case 'speaking':
        return {
          title: t.speaking,
          subtitle: null,
          dot: 'bg-[#2E7D32]',
          icon: <Volume2 className="h-5 w-5 text-[#1B5E20]" strokeWidth={2} />,
        };
      case 'ended':
        return {
          title: t.ended,
          subtitle: null,
          dot: 'bg-[#90A4AE]',
          icon: <Mic className="h-5 w-5 text-[#546E7A]" strokeWidth={2} />,
        };
      case 'error':
        return {
          title: t.micErrorTitle,
          subtitle: t.micErrorBody,
          dot: 'bg-[#E53935]',
          icon: <MicOff className="h-5 w-5 text-[#C62828]" strokeWidth={2} />,
        };
      case 'ready':
      default:
        return {
          title: t.ready,
          subtitle: t.readySubtitle,
          dot: 'bg-[#66BB6A]',
          icon: <Mic className="h-5 w-5 text-[#2E7D32]" strokeWidth={2} />,
        };
    }
  })();

  return (
    <section
      aria-label="Voice interaction panel"
      className="w-full
        rounded-[26px] border border-white/55 bg-white/35 px-6 py-6
        shadow-[0_18px_50px_-28px_rgba(27,94,32,0.28)] backdrop-blur-[20px]
        text-[#263238] flex flex-col h-[520px]"
    >
      <div className="flex flex-col h-full items-center justify-between gap-4">
        {/* Top section */}
        <div className="flex w-full flex-col items-center text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/35 px-3 py-1 text-[12px] font-semibold text-[#1B5E20] shadow-[0_1px_0_rgba(255,255,255,0.55)]">
            <span className={`h-2 w-2 rounded-full ${status.dot}`} />
            <span>Kisan Mitra</span>
          </div>

          {/* Concentric circles microphone visualization */}
          <div className="mt-6 relative flex h-[120px] w-[120px] flex-none items-center justify-center">
            {/* Outer circle animation */}
            <div className="absolute inset-0 rounded-full border-2 border-green-200/40 animate-pulse" />
            {/* Middle circle */}
            <div className="absolute inset-4 rounded-full border-2 border-green-200/60" />
            {/* Inner circle with microphone */}
            <div className={`relative flex h-20 w-20 flex-none items-center justify-center rounded-full border-2 border-green-300/80 bg-gradient-to-br from-white to-green-50 shadow-[0_4px_12px_rgba(46,125,50,0.2)]`}>
              {status.icon}
            </div>
          </div>

          <div className="mt-5 flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${status.dot}`} />
            <h2 className="text-[20px] font-semibold leading-tight text-[#1B5E20]">
              {status.title}
            </h2>
          </div>

          {status.subtitle && (
            <p className="mt-2 max-w-[280px] text-[13.5px] leading-snug text-[#546E7A]">
              {status.subtitle}
            </p>
          )}

          {isSpeaking && <MiniWaveform audioLevel={audioLevel} />}
          {isListening && <MiniListeningWaveform />}
        </div>

        {/* Bottom section - buttons */}
        <div className="w-full space-y-3">
          {/* Main action button */}
          {isReady && (
            <button
              type="button"
              onClick={onStartCall}
              disabled={!canUseButton}
              className="flex h-[52px] w-full items-center justify-center gap-2 rounded-full bg-[#2E7D32] text-[15px] font-semibold text-white shadow-[0_12px_24px_-18px_rgba(27,94,32,0.45)] transition-all duration-150 hover:bg-[#1B5E20] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Mic className="h-5 w-5" strokeWidth={2} />
              <span>{t.startTalking}</span>
            </button>
          )}

          {isRestartable && (
            <button
              type="button"
              onClick={onStartCall}
              disabled={!canUseButton}
              className="flex h-[52px] w-full items-center justify-center gap-2 rounded-full bg-[#2E7D32] text-[15px] font-semibold text-white shadow-[0_12px_24px_-18px_rgba(27,94,32,0.45)] transition-all duration-150 hover:bg-[#1B5E20] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Mic className="h-5 w-5" strokeWidth={2} />
              <span>{t.startAgain}</span>
            </button>
          )}

          {/* Status indicator buttons - shown during ready state or when active */}
          {(isReady || isActive) && (
            <div className="grid grid-cols-4 gap-2 mt-2">
              {/* Ready button */}
              <button
                type="button"
                disabled
                className="flex flex-col items-center justify-center gap-1 py-2 px-1 rounded-lg bg-white/40 border border-white/60 disabled:opacity-60"
              >
                <Mic className="h-4 w-4 text-[#2E7D32]" strokeWidth={2} />
                <span className="text-[10px] font-medium text-[#1B5E20]">Ready</span>
              </button>

              {/* Listening button */}
              <button
                type="button"
                disabled
                className="flex flex-col items-center justify-center gap-1 py-2 px-1 rounded-lg bg-white/40 border border-white/60 disabled:opacity-60"
              >
                <Volume2 className="h-4 w-4 text-[#2E7D32]" strokeWidth={2} />
                <span className="text-[10px] font-medium text-[#1B5E20]">Listening</span>
              </button>

              {/* Thinking button */}
              <button
                type="button"
                disabled
                className="flex flex-col items-center justify-center gap-1 py-2 px-1 rounded-lg bg-white/40 border border-white/60 disabled:opacity-60"
              >
                <span className="h-4 w-4 flex items-center justify-center text-[11px]">💭</span>
                <span className="text-[10px] font-medium text-[#1B5E20]">Thinking</span>
              </button>

              {/* Speaking button */}
              <button
                type="button"
                disabled
                className="flex flex-col items-center justify-center gap-1 py-2 px-1 rounded-lg bg-white/40 border border-white/60 disabled:opacity-60"
              >
                <span className="h-4 w-4 flex items-center justify-center text-[11px]">🔊</span>
                <span className="text-[10px] font-medium text-[#1B5E20]">Speaking</span>
              </button>
            </div>
          )}

          {/* Control buttons when active */}
          {isActive && (
            <div className="grid grid-cols-2 gap-3 mt-2">
              <button
                type="button"
                onClick={onToggleMic}
                disabled={!isConnected}
                aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
                className="flex h-[44px] items-center justify-center gap-1.5 rounded-full border border-white/50 bg-white/30 px-3 text-[12px] font-medium text-[#1B5E20] shadow-[0_10px_24px_-20px_rgba(27,94,32,0.32)] backdrop-blur-md transition-all duration-150 hover:bg-white/40 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-55"
              >
                {isMuted ? (
                  <MicOff className="h-4 w-4 text-[#C62828]" strokeWidth={2} />
                ) : (
                  <Mic className="h-4 w-4 text-[#2E7D32]" strokeWidth={2} />
                )}
                <span>{isMuted ? 'Unmute' : 'Mute'}</span>
              </button>

              <button
                type="button"
                onClick={onEndCall}
                disabled={!canUseButton}
                className="flex h-[44px] items-center justify-center gap-1.5 rounded-full border border-red-200/50 bg-red-50/30 px-3 text-[12px] font-medium text-[#C62828] shadow-[0_12px_24px_-18px_rgba(198,40,40,0.28)] transition-all duration-150 hover:bg-red-100/40 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
              >
                <PhoneOff className="h-4 w-4" strokeWidth={2} />
                <span>End Call</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function MiniWaveform({ audioLevel }: { audioLevel: number }) {
  const bars = [0.42, 0.62, 0.86, 0.68, 0.48, 0.58, 0.78, 0.52];
  const level = Math.max(0.25, Math.min(1, audioLevel || 0.45));

  return (
    <div className="mt-4 flex h-8 items-end justify-center gap-1.5" aria-hidden="true">
      {bars.map((base, index) => {
        const height = Math.max(8, Math.round(18 * (0.35 + base * level)));
        return (
          <span
            key={index}
            className="w-1 rounded-full bg-[#2E7D32]"
            style={{ height: `${height}px`, opacity: 0.55 + index * 0.05 }}
          />
        );
      })}
    </div>
  );
}

function MiniListeningWaveform() {
  const bars = [8, 12, 16, 12, 9, 11, 14, 10];

  return (
    <div className="mt-4 flex h-8 items-end justify-center gap-1.5" aria-hidden="true">
      {bars.map((height, index) => (
        <span
          key={index}
          className="w-1 rounded-full bg-[#2E7D32]/70 animate-pulse"
          style={{ height: `${height}px`, animationDelay: `${index * 0.12}s` }}
        />
      ))}
    </div>
  );
}