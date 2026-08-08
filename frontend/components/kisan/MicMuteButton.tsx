'use client';

import React from 'react';
import { Mic, MicOff } from 'lucide-react';

interface MicMuteButtonProps {
  isMuted: boolean;
  canToggle: boolean;
  onToggle: () => void;
}

export function MicMuteButton({ isMuted, canToggle, onToggle }: MicMuteButtonProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={!canToggle}
      aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
      className="group inline-flex items-center justify-center gap-2
        w-full max-w-[220px] h-[42px] sm:h-[44px]
        rounded-full
        border border-white/65 bg-white/72 hover:bg-white/86
        text-[#1B5E20]
        shadow-[0_10px_22px_-14px_rgba(27,94,32,0.35)]
        backdrop-blur-md
        transition-all duration-150
        active:scale-[0.98] disabled:opacity-55 disabled:cursor-not-allowed"
    >
      {isMuted ? (
        <MicOff className="w-4.5 h-4.5 stroke-[1.9] text-[#C62828]" />
      ) : (
        <Mic className="w-4.5 h-4.5 stroke-[1.9] text-[#2E7D32]" />
      )}
      <span className="text-[13px] sm:text-[13.5px] font-semibold">
        {isMuted ? 'Unmute Mic' : 'Mute Mic'}
      </span>
    </button>
  );
}