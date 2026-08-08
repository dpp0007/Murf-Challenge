'use client';

import React from 'react';
import type { KisanVoiceState } from './KisanMainView';
import { useLanguage } from '@/contexts/LanguageContext';

interface VoiceStatusProps {
  voiceState: KisanVoiceState;
}

export function VoiceStatus({ voiceState }: VoiceStatusProps) {
  const { t } = useLanguage();

  const content = React.useMemo(() => {
    switch (voiceState) {
      case 'connecting':
        return {
          title: t.connecting,
          subtitle: t.connectingSubtitle,
          tone: 'text-[#546E7A]',
          dot: 'bg-[#F9A825]',
        };
      case 'listening':
        return {
          title: t.listening,
          subtitle: t.listeningSubtitle,
          tone: 'text-[#1B5E20]',
          dot: 'bg-[#2E7D32] animate-pulse',
        };
      case 'speaking':
        return {
          title: t.speaking,
          subtitle: null,
          tone: 'text-[#1B5E20]',
          dot: 'bg-[#2E7D32]',
        };
      case 'ended':
        return {
          title: t.ended,
          subtitle: null,
          tone: 'text-[#546E7A]',
          dot: 'bg-[#90A4AE]',
        };
      case 'error':
        return {
          title: t.micErrorTitle,
          subtitle: null,
          tone: 'text-[#C62828]',
          dot: 'bg-[#E53935]',
        };
      case 'ready':
      default:
        return {
          title: t.ready,
          subtitle: t.readySubtitle,
          tone: 'text-[#37474F]',
          dot: 'bg-[#66BB6A]',
        };
    }
  }, [voiceState, t]);

  return (
    <div className="flex flex-col items-center gap-1 text-center animate-soft-in mt-2">
      <div className="flex items-center gap-2">
        <span className={`w-1.5 h-1.5 rounded-full ${content.dot}`} />
        <span className={`text-[15px] sm:text-[16px] font-semibold leading-none ${content.tone}`}>
          {content.title}
        </span>
      </div>
      {content.subtitle && (
        <p className="text-[12.5px] sm:text-[13px] text-[#546E7A] max-w-xs sm:max-w-sm">
          {content.subtitle}
        </p>
      )}
    </div>
  );
}
