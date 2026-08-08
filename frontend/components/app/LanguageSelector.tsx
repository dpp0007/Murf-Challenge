'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { ChevronDown } from 'lucide-react';

export function LanguageSelector() {
  const { language, setLanguage, languages } = useLanguage();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const current = languages.find((l) => l.code === language) ?? languages[0];

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={ref} className="relative z-50">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5
          bg-white/80 hover:bg-white/90
          border border-[#C8E6C9]/60 hover:border-[#A5D6A7]
          px-2.5 py-1.5 rounded-full shadow-sm backdrop-blur-md
          text-xs font-semibold text-[#2E7D32] whitespace-nowrap
          transition-all duration-150 active:scale-[0.98]
          cursor-pointer select-none"
        aria-label="Select language"
      >
        <span className="text-sm leading-none">🌐</span>
        <span>{current.label}</span>
        <ChevronDown className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div
          className="absolute right-0 mt-2 w-40
            bg-white/90 backdrop-blur-xl
            border border-[#C8E6C9]/60 rounded-2xl shadow-xl
            overflow-hidden p-1
            animate-in fade-in slide-in-from-top-1 duration-150"
        >
          {languages.map((l) => {
            const active = l.code === language;
            return (
              <button
                key={l.code}
                onClick={() => {
                  setLanguage(l.code);
                  setOpen(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-xl text-sm
                  transition-all duration-100
                  flex items-center gap-2
                  ${active
                    ? 'bg-[#E8F5E9] text-[#1B5E20] font-semibold'
                    : 'text-[#263238] hover:bg-[#F1F8E9]'}`}
              >
                {active && <span className="text-[#2E7D32] text-xs">✓</span>}
                <span className={active ? '' : 'pl-5'}>{l.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
