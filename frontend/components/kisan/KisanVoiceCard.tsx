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
      className="glass-panel w-[min(92vw,380px)] sm:w-[380px] xl:w-[380px]
        h-[430px] sm:h-[430px] xl:h-[430px]
        rounded-[30px] border border-white/55 bg-white/35 px-5 py-5 sm:px-6 sm:py-6
        shadow-[0_18px_50px_-28px_rgba(27,94,32,0.28)] backdrop-blur-[20px]
        text-[#263238]"
    >
      <div className="flex h-full flex-col items-center justify-between gap-4">
        <div className="flex w-full flex-col items-center text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/35 px-3 py-1 text-[12px] font-semibold text-[#1B5E20] shadow-[0_1px_0_rgba(255,255,255,0.55)]">
            <span className={`h-2 w-2 rounded-full ${status.dot}`} />
            <span>Kisan Mitra</span>
          </div>

          <div className={`mt-4 flex ${orbSizeClasses} flex-none items-center justify-center rounded-full border border-white/80 bg-[#FFF8E7]/92 shadow-[0_20px_40px_-26px_rgba(27,94,32,0.35)]`}>
            {status.icon}
          </div>

          <div className="mt-3 flex items-center gap-2">
            <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
            <h2 className="text-[18px] font-semibold leading-tight text-[#1B5E20]">
              {status.title}
            </h2>
          </div>

          {status.subtitle && (
            <p className="mt-1 max-w-[250px] text-[13.5px] leading-snug text-[#546E7A]">
              {status.subtitle}
            </p>
          )}

          {isSpeaking && <MiniWaveform audioLevel={audioLevel} />}
          {isListening && <MiniListeningWaveform />}
        </div>

        <div className="w-full space-y-2.5">
          {isReady && (
            <button
              type="button"
              onClick={onStartCall}
              disabled={!canUseButton}
              className="flex h-[48px] w-full items-center justify-center gap-2 rounded-full border border-[#1B5E20]/10 bg-[#FFF8E7]/92 text-[14.5px] font-semibold text-[#2E7D32] shadow-[0_12px_24px_-18px_rgba(27,94,32,0.35)] transition-all duration-150 hover:bg-[#FFFDF6] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Mic className="h-4.5 w-4.5" strokeWidth={2} />
              <span>{t.startTalking}</span>
            </button>
          )}

          {isRestartable && (
            <button
              type="button"
              onClick={onStartCall}
              disabled={!canUseButton}
              className="flex h-[48px] w-full items-center justify-center gap-2 rounded-full border border-[#1B5E20]/10 bg-[#FFF8E7]/92 text-[14.5px] font-semibold text-[#2E7D32] shadow-[0_12px_24px_-18px_rgba(27,94,32,0.35)] transition-all duration-150 hover:bg-[#FFFDF6] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Mic className="h-4.5 w-4.5" strokeWidth={2} />
              <span>{t.startAgain}</span>
            </button>
          )}

          {isActive && (
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={onToggleMic}
                disabled={!isConnected}
                aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
                className="flex h-[48px] min-w-0 items-center justify-center gap-2 rounded-full border border-white/70 bg-white/68 px-3 text-[14px] font-semibold text-[#1B5E20] shadow-[0_10px_24px_-20px_rgba(27,94,32,0.32)] backdrop-blur-md transition-all duration-150 hover:bg-white/82 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-55"
              >
                {isMuted ? (
                  <MicOff className="h-4.5 w-4.5 text-[#C62828]" strokeWidth={2} />
                ) : (
                  <Mic className="h-4.5 w-4.5 text-[#2E7D32]" strokeWidth={2} />
                )}
                <span className="truncate">{isMuted ? t.unmuteMic : t.muteMic}</span>
              </button>

              <button
                type="button"
                onClick={onEndCall}
                disabled={!canUseButton}
                className="flex h-[48px] min-w-0 items-center justify-center gap-2 rounded-full border border-[#E57373]/30 bg-[#FFF8E7]/92 px-3 text-[14.5px] font-semibold text-[#C62828] shadow-[0_12px_24px_-18px_rgba(198,40,40,0.28)] transition-all duration-150 hover:bg-[#FFFDF6] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
              >
                <PhoneOff className="h-4.5 w-4.5" strokeWidth={2} />
                <span className="truncate">End Call</span>
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