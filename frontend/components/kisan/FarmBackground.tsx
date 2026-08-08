'use client';

import React from 'react';

export function FarmBackground() {
  return (
    <div
      className="fixed inset-0 z-0 select-none pointer-events-none overflow-hidden"
      aria-hidden="true"
    >
      {/* Sky gradient — fills whole viewport, more cyan-blue */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#BFE3F2] via-[#D7EEF3] to-[#EAF6F7]" />

      {/*
        Farm Landscape SVG (square).
        We render it 120vw wide, then shift its BOTTOM to 84% of screen height.
        This puts the horizon around 35–40% from the top, leaving the sky spacious.
      */}
      <div
        className="absolute left-1/2 pointer-events-none"
        style={{
          width: '125vw',
          transform: 'translate(-50%, 0)',
          // Shift landscape down so horizon sits lower (~200px)
          bottom: 'calc(-16% - 220px)',
        }}
      >
        <img
          src="/illustration/Background.svg"
          alt=""
          draggable={false}
          style={{
            width: '100%',
            height: 'auto',
            display: 'block',
          }}
        />
      </div>

      {/* Floating clouds — upper sky region, constrained to top 55% */}
      <div
        className="absolute left-0 right-0 pointer-events-none"
        style={{ top: 0, height: '55%' }}
      >
        {/* Cloud 1 — large, slow, top-left */}
        <div
          className="absolute animate-cloud-slow"
          style={{ top: '8%', left: '-18%', width: 'clamp(100px, 16vw, 220px)', animationDelay: '-18s' }}
        >
          <img
            src="/illustration/cloud01.svg"
            alt=""
            className="w-full h-auto opacity-95"
            draggable={false}
          />
        </div>

        {/* Cloud 2 — medium speed, center-right */}
        <div
          className="absolute animate-cloud-medium"
          style={{ top: '18%', left: '42%', width: 'clamp(75px, 12vw, 170px)', animationDelay: '-42s' }}
        >
          <img
            src="/illustration/cloud02.svg"
            alt=""
            className="w-full h-auto opacity-85"
            draggable={false}
          />
        </div>

        {/* Cloud 3 — faster, smaller, top-right */}
        <div
          className="absolute animate-cloud-fast"
          style={{ top: '6%', left: '62%', width: 'clamp(85px, 13vw, 180px)', animationDelay: '-64s' }}
        >
          <img
            src="/illustration/cloud03.svg"
            alt=""
            className="w-full h-auto opacity-80"
            draggable={false}
          />
        </div>

        {/* Extra tiny cloud for depth */}
        <div
          className="absolute animate-cloud-fast opacity-70"
          style={{ top: '34%', left: '-28%', width: 'clamp(50px, 8vw, 110px)', animationDuration: '180s', animationDelay: '-96s' }}
        >
          <img
            src="/illustration/cloud03.svg"
            alt=""
            className="w-full h-auto"
            draggable={false}
          />
        </div>
      </div>
    </div>
  );
}
