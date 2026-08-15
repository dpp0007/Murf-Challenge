'use client';

import React from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { LanguageSelector } from '@/components/app/LanguageSelector';

export function KisanHeader() {
  const { t } = useLanguage();

  return (
    <header className="fixed left-0 right-0 top-0 z-30 flex items-center justify-between px-6 py-4 pointer-events-none">
      {/* Top Left — brand mark */}
      <div className="pointer-events-auto flex items-center gap-2">
        {/* Logo */}
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-[#2E7D32] to-[#1B5E20]">
          <span className="text-lg font-bold text-white">🌾</span>
        </div>
        <div className="flex flex-col">
          <div className="text-[16px] font-bold leading-tight text-gray-900">
            {t.appName}
          </div>
          <div className="text-[11px] font-medium leading-tight text-gray-600">
            {t.tagline}
          </div>
        </div>
      </div>

      {/* Top Right — language selector */}
      <div className="pointer-events-auto">
        <LanguageSelector />
      </div>
    </header>
  );
}
