'use client';

import React from 'react';
import type { KisanVoiceState } from './KisanMainView';
import { Mic, PhoneOff } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

interface VoiceButtonProps {
  voiceState: KisanVoiceState;
  canUseButton: boolean;
  onStartCall: () => void;
  onEndCall: () => void;
}

export function VoiceButton({
  voiceState,
  canUseButton,
  onStartCall,
  onEndCall,
}: VoiceButtonProps) {
  const { t } = useLanguage();

  const isActive =
    voiceState === 'connecting' ||
    voiceState === 'listening' ||
    voiceState === 'speaking';

  if (isActive) {
    return (
      <button
        type="button"
        onClick={onEndCall}
        disabled={!canUseButton}
        className="group flex items-center justify-center gap-2
          w-full max-w-[280px] h-[52px] sm:h-[56px]
          rounded-full
          bg-white/85 hover:bg-white
          border border-red-100 hover:border-red-200
          shadow-[0_10px_28px_-10px_rgba(198,40,40,0.25),0_2px_6px_-2px_rgba(198,40,40,0.1)]
          text-[#C62828]
          font-bold
          transition-all duration-150
          active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed
          cursor-pointer animate-soft-in"
      >
        <PhoneOff className="w-5 h-5 stroke-[1.9]" />
        <span className="text-[14px] sm:text-[15px]">{t.endCall}</span>
      </button>
    );
  }

  const label =
    voiceState === 'ended' || voiceState === 'error' ? t.startAgain : t.startTalking;

  return (
    <button
      type="button"
      onClick={onStartCall}
      disabled={!canUseButton}
      className="group flex items-center justify-center gap-2.5
        w-full max-w-[320px] h-[56px] sm:h-[60px]
        rounded-full
        bg-gradient-to-b from-[#388E3C] to-[#2E7D32]
        hover:from-[#2E7D32] hover:to-[#1B5E20]
        active:from-[#1B5E20] active:to-[#1B5E20]
        text-white
        font-bold tracking-[0.01em]
        shadow-[0_16px_38px_-12px_rgba(27,94,32,0.45),0_3px_8px_-2px_rgba(27,94,32,0.25),inset_0_1px_0_rgba(255,255,255,0.22)]
        ring-1 ring-[#1B5E20]/15
        transition-all duration-150
        active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed
        cursor-pointer animate-soft-in"
    >
      <Mic className="w-5 h-5 stroke-[1.9]" />
      <span className="text-[14.5px] sm:text-[15.5px]">{label}</span>
    </button>
  );
}
