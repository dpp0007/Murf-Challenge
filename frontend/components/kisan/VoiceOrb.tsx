'use client';

import React from 'react';
import type { KisanVoiceState } from './KisanMainView';
import { Mic, Volume2, Loader2 } from 'lucide-react';

interface VoiceOrbProps {
  voiceState: KisanVoiceState;
  audioLevel: number;
}

/**
 * Minimal microphone-centered voice control.
 *
 * States:
 *  ready:       mic icon, calm
 *  connecting:  spinner (small rotate)
 *  listening:   mic + subtle listening pulse
 *  speaking:    speaker + visualizer bars around
 *  ended:       mic, gray-ish
 *  error:       mic, dim
 */
export function VoiceOrb({ voiceState, audioLevel }: VoiceOrbProps) {
  const isListening = voiceState === 'listening';
  const isConnecting = voiceState === 'connecting';
  const isSpeaking = voiceState === 'speaking';

  return (
    <div className="flex flex-col items-center animate-soft-in">
      {/* Visualizer above the mic (speaking state only) */}
      <div
        className="h-8 flex items-end justify-center gap-[3px] mb-2 w-40"
        aria-hidden="true"
      >
        {isSpeaking ? (
          <SpeakVisualizer audioLevel={audioLevel} />
        ) : isListening ? (
          <ListenVisualizer />
        ) : null}
      </div>

      {/* Main circular mic button (decorative; action handled by VoiceButton) */}
      <div
        className={[
          'relative flex items-center justify-center',
          'w-[86px] h-[86px] sm:w-[96px] sm:h-[96px]',
          'rounded-full',
          'bg-white/85',
          'border border-white',
          'shadow-[0_10px_30px_-10px_rgba(27,94,32,0.35),0_2px_6px_-2px_rgba(27,94,32,0.12)]',
          'transition-all duration-300 ease-out',
          isListening ? 'animate-mic-listen ring-2 ring-[#A5D6A7]/80' : '',
          isConnecting ? 'ring-1 ring-[#C8E6C9]/60' : '',
          voiceState === 'ended' || voiceState === 'error' ? 'opacity-80' : '',
        ].join(' ')}
      >
        {isConnecting ? (
          <Loader2 className="w-8 h-8 sm:w-9 sm:h-9 text-[#2E7D32] animate-mic-connect" />
        ) : isSpeaking ? (
          <Volume2 className="w-8 h-8 sm:w-9 sm:h-9 text-[#1B5E20] stroke-[1.8]" />
        ) : (
          <Mic
            className={`w-8 h-8 sm:w-9 sm:h-9 transition-colors ${
              voiceState === 'error' ? 'text-gray-400' : 'text-[#1B5E20]'
            }`}
            strokeWidth={1.8}
          />
        )}

        {/* subtle inner highlight */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 rounded-full
            bg-gradient-to-b from-white/80 to-transparent opacity-70"
        />
      </div>

      {/* Visualizer below the mic (speaking state only) */}
      <div
        className="h-8 flex items-start justify-center gap-[3px] mt-2 w-40 rotate-180"
        aria-hidden="true"
      >
        {isSpeaking ? (
          <SpeakVisualizer audioLevel={audioLevel} />
        ) : null}
      </div>
    </div>
  );
}

function ListenVisualizer() {
  return (
    <>
      {Array.from({ length: 7 }).map((_, i) => (
        <span
          key={i}
          className="viz-bar"
          style={{
            animationDelay: `${i * 0.12}s`,
            opacity: 0.75,
            height: '14px',
          }}
        />
      ))}
    </>
  );
}

function SpeakVisualizer({ audioLevel }: { audioLevel: number }) {
  const safeLevel = Math.max(0.25, Math.min(1, audioLevel || 0.45));
  return (
    <>
      {Array.from({ length: 10 }).map((_, i) => {
        // create slight variability between bars
        const phase = (Math.sin(i * 1.3) + 1) / 2;
        const scale = 0.3 + phase * 0.7 * safeLevel;
        const baseH = 16 + Math.round(16 * scale);
        const delay = (i % 5) * 0.09;
        return (
          <span
            key={i}
            className="viz-bar"
            style={{
              animationDelay: `${delay}s`,
              height: `${baseH}px`,
              transform: `scaleY(${Math.max(0.3, scale)})`,
              opacity: 0.7 + phase * 0.3,
            }}
          />
        );
      })}
    </>
  );
}
