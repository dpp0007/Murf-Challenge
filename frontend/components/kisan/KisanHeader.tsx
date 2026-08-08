'use client';

import React from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { LanguageSelector } from '@/components/app/LanguageSelector';

export function KisanHeader() {
  const { t } = useLanguage();

  return (
    <header className="fixed left-0 right-0 top-0 z-30 flex items-start justify-between px-4 py-4 sm:px-6 pointer-events-none">
      {/* Top Left — brand mark */}
      <div className="pointer-events-auto max-w-[250px] rounded-2xl bg-transparent px-0 py-0 text-[#1B5E20]">
        <div className="flex items-center gap-2 text-[15px] font-semibold leading-tight sm:text-[16px]">
          <span className="text-[18px] leading-none">🌾</span>
          <span>{t.appName}</span>
        </div>
        <div className="mt-0.5 text-[11px] font-medium leading-tight text-[#546E7A]">
          {t.tagline}
        </div>
      </div>

      {/* Top Right — language selector */}
      <div className="pointer-events-auto">
        <LanguageSelector />
      </div>
    </header>
  );
}
