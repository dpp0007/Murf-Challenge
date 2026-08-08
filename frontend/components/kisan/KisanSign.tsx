'use client';

import React from 'react';

export function KisanSign() {
  return (
    <div className="relative inline-flex flex-col items-center justify-center p-3 sm:p-4 rounded-2xl bg-[#8D6E63]/90 border-2 border-[#5D4037] shadow-xl backdrop-blur-xs text-white">
      {/* Wooden Signboard texture container */}
      <div className="flex items-center gap-2 text-xl sm:text-2xl font-bold tracking-wide text-[#FFF8E7] drop-shadow-sm">
        <span className="text-2xl sm:text-3xl">🌾</span>
        <span>Kisan Mitra</span>
      </div>
      <div className="text-xs sm:text-sm font-semibold text-[#F4C95D] mt-0.5 tracking-wider font-sans">
        किसान मित्र
      </div>
    </div>
  );
}
