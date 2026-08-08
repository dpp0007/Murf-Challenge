'use client';

import React from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { MicOff, X } from 'lucide-react';

interface MicrophoneErrorProps {
  onRetry: () => void;
  onDismiss?: () => void;
}

export function MicrophoneError({ onRetry, onDismiss }: MicrophoneErrorProps) {
  const { t } = useLanguage();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/35 backdrop-blur-sm animate-soft-in">
      <div className="glass-panel max-w-md w-full rounded-3xl p-6 sm:p-7 space-y-4 text-center">
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="absolute top-3 right-3 text-[#546E7A] hover:text-[#263238] transition-colors p-2 rounded-full hover:bg-white/60"
            aria-label="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        )}

        <div className="relative mx-auto w-14 h-14 rounded-full bg-[#FFEBEE] text-[#D32F2F] flex items-center justify-center shadow-sm border border-white/70">
          <MicOff className="w-7 h-7" strokeWidth={1.8} />
        </div>

        <div>
          <h3 className="text-lg sm:text-xl font-bold text-[#263238]">
            {t.micErrorTitle}
          </h3>

          <p className="text-[13.5px] leading-relaxed text-[#546E7A] mt-1.5">
            {t.micErrorBody}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <button
            onClick={onRetry}
            className="flex-1 py-3 px-6 rounded-full
              bg-gradient-to-b from-[#388E3C] to-[#2E7D32]
              hover:from-[#2E7D32] hover:to-[#1B5E20]
              text-white font-bold text-sm
              shadow-[0_8px_20px_-8px_rgba(27,94,32,0.5)]
              transition-all active:scale-[0.98] cursor-pointer"
          >
            {t.retry}
          </button>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="py-3 px-5 rounded-full
                bg-white/70 hover:bg-white
                border border-[#C8E6C9]/80
                text-[#263238] font-semibold text-sm
                transition-all cursor-pointer"
            >
              {t.dismiss}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
