'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  useAgent,
  useLocalParticipant,
  useSessionContext,
  useSessionMessages,
  useVoiceAssistant,
  type ReceivedMessage,
  type TrackReferenceOrPlaceholder,
} from '@livekit/components-react';
import type { LocalAudioTrack, RemoteAudioTrack } from 'livekit-client';
import { FarmBackground } from './FarmBackground';
import { KisanHeader } from './KisanHeader';
import { ConversationPanel } from './ConversationPanel';
import { MicrophoneError } from './MicrophoneError';
import { KisanVoiceCard } from './KisanVoiceCard';
import { WeatherAlertButton } from './WeatherAlertButton';
import { getPersistentUserId } from '@/lib/userIdGenerator';

export type KisanVoiceState =
  | 'ready'
  | 'connecting'
  | 'listening'
  | 'speaking'
  | 'ended'
  | 'error';

type AnyAudioTrackish =
  | LocalAudioTrack
  | RemoteAudioTrack
  | TrackReferenceOrPlaceholder
  | undefined
  | null;

/**
 * Resolve the actual LocalAudioTrack / RemoteAudioTrack from a TrackReference.
 * Returns null if no track is available yet.
 */
function resolveTrack(track: AnyAudioTrackish): LocalAudioTrack | RemoteAudioTrack | null {
  if (!track) return null;
  // Direct track: has `mediaStream`
  const asDirect = track as LocalAudioTrack | RemoteAudioTrack;
  if (typeof (asDirect as any).mediaStream !== 'undefined') return asDirect;
  // TrackReference: has `publication`
  const asRef = track as TrackReferenceOrPlaceholder;
  if (asRef.publication) {
    const tk = asRef.publication.track as LocalAudioTrack | RemoteAudioTrack | undefined;
    if (tk) return tk;
  }
  return null;
}

/**
 * Extract a 0-1 audio level from a LiveKit audio track using Web Audio.
 * Returns the current audio level number. Useful for visualizer sensitivity.
 */
function useAgentAudioLevel(audioTrack: AnyAudioTrackish) {
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const frameRef = useRef<number | null>(null);
  const [level, setLevel] = useState(0.45);

  useEffect(() => {
    // Clean previous
    if (frameRef.current) cancelAnimationFrame(frameRef.current);
    if (sourceRef.current) {
      try {
        sourceRef.current.disconnect();
      } catch {
        /* noop */
      }
    }
    if (ctxRef.current) {
      ctxRef.current.close().catch(() => null);
    }
    analyserRef.current = null;
    sourceRef.current = null;
    ctxRef.current = null;

    const resolved = resolveTrack(audioTrack);
    const stream: MediaStream | undefined = (resolved as any)?.mediaStream;
    if (!stream) {
      setLevel(0.45);
      return;
    }

    try {
      const AudioCtx =
        (window as any).AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      const source = ctx.createMediaStreamSource(stream);
      source.connect(analyser);

      ctxRef.current = ctx;
      analyserRef.current = analyser;
      sourceRef.current = source;

      const buffer = new Uint8Array(analyser.frequencyBinCount);
      const animate = () => {
        analyser.getByteFrequencyData(buffer);
        let sum = 0;
        for (let i = 0; i < buffer.length; i++) sum += buffer[i];
        const avg = sum / buffer.length / 255;
        setLevel(Math.max(0.2, Math.min(1, avg * 2.4)));
        frameRef.current = requestAnimationFrame(animate);
      };
      frameRef.current = requestAnimationFrame(animate);
    } catch {
      setLevel(0.45);
    }

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      if (sourceRef.current) {
        try {
          sourceRef.current.disconnect();
        } catch {
          /* noop */
        }
      }
      if (ctxRef.current) {
        ctxRef.current.close().catch(() => null);
      }
    };
  }, [audioTrack]);

  return level;
}

export function KisanMainView() {
  const session = useSessionContext();
  const { state: agentState } = useAgent();
  const { messages: rawMessages, send } = useSessionMessages(session);
  const messages = (rawMessages ?? []) as ReceivedMessage[];
  const { audioTrack } = useVoiceAssistant();
  const { localParticipant } = useLocalParticipant();
  const audioLevel = useAgentAudioLevel(audioTrack);

  const [hasStartedOnce, setHasStartedOnce] = useState(false);
  const [micError, setMicError] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const isConnected = session.isConnected;
  const isMuted = localParticipant?.isMicrophoneEnabled === false;
  const canUseButton = typeof session.start === 'function' && typeof session.end === 'function';

  // Set hasStartedOnce only when actually connected
  useEffect(() => {
    if (isConnected) {
      setHasStartedOnce(true);
      // Clear connecting state once we're truly connected and agent is ready
      if (agentState && agentState !== 'initializing') {
        setIsConnecting(false);
      }
    } else {
      setIsConnecting(false);
    }
  }, [isConnected, agentState]);

  // Derive Kisan voice state from LiveKit session - SIMPLIFIED AND FIXED
  let voiceState: KisanVoiceState = 'ready';
  
  if (micError) {
    // Error state takes highest priority
    voiceState = 'error';
  } else if (isConnecting) {
    // User clicked start, we're connecting
    voiceState = 'connecting';
  } else if (!isConnected) {
    // Not connected: either ready to start or call ended
    voiceState = hasStartedOnce ? 'ended' : 'ready';
  } else {
    // Connected - determine state based on agent activity
    if (!agentState || agentState === 'initializing') {
      // Agent is connecting/initializing
      voiceState = 'connecting';
    } else if (agentState === 'speaking') {
      // Agent is speaking
      voiceState = 'speaking';
    } else {
      // Any other state (listening, thinking, idle) = listening
      voiceState = 'listening';
    }
  }
  
  // Debug logging (only in development)
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('[KisanMainView] State:', { 
        voiceState, 
        isConnected,
        isConnecting,
        agentState, 
        hasStartedOnce,
        micError 
      });
    }
  }, [voiceState, isConnected, isConnecting, agentState, hasStartedOnce, micError]);

  useEffect(() => {
    if (agentState === 'failed') setMicError(true);
  }, [agentState]);

  const handleStartCall = async () => {
    setMicError(false);
    setIsConnecting(true); // Set connecting state immediately
    // Don't set hasStartedOnce here - let the useEffect handle it when connected
    try {
      if (session.start) await session.start();
    } catch (err) {
      console.error('Session start error:', err);
      setIsConnecting(false); // Clear connecting state on error
      const errStr = String(err).toLowerCase();
      if (errStr.includes('permission') || errStr.includes('notallowed')) {
        setMicError(true);
      }
    }
  };

  const handleDisconnect = () => {
    if (session.end) session.end();
  };

  const handleToggleMic = async () => {
    if (!localParticipant?.setMicrophoneEnabled) return;
    try {
      await localParticipant.setMicrophoneEnabled(isMuted);
    } catch (err) {
      console.error('Microphone toggle error:', err);
      setMicError(true);
    }
  };

  // Ensure messages usage so TS keeps the import (used by ConversationPanel)
  const handleSendMessage = async (message: string) => {
    try {
      await send(message);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  return (
    <div className="relative h-svh w-full overflow-hidden flex flex-col select-none">
      {/* Layer 0: Farm background scene */}
      <FarmBackground />

      {/* Layer 1: Compact floating header */}
      <KisanHeader />

      {/* Layer 2: Main content */}
      <main
        className="relative z-10 flex-1 w-full h-full overflow-hidden
          pt-[68px] sm:pt-[84px] pb-3 sm:pb-5 px-3 sm:px-5 lg:px-6"
      >
        <div
          className="relative h-full w-full max-w-[1280px] mx-auto flex flex-col items-center gap-4 sm:gap-5 xl:block"
        >
          
          {/* Column 1 — Conversation (translucent, left side) */}
          <div className="order-2 w-full flex justify-center xl:absolute xl:left-[5.5vw] xl:top-1/2 xl:w-[380px] xl:-translate-y-1/2 xl:justify-start xl:order-1">
            <ConversationPanel messages={messages} canSend={isConnected} onSendMessage={handleSendMessage} />
          </div>

          {/* Column 2 — Voice control (center/right) */}
          <div className="order-1 flex w-full justify-center xl:absolute xl:right-[8vw] xl:top-1/2 xl:w-[380px] xl:-translate-y-1/2 xl:order-2">
            <div className="flex flex-col gap-4 w-full max-w-[380px]">
              <KisanVoiceCard
                voiceState={voiceState}
                audioLevel={audioLevel}
                isMuted={isMuted}
                canUseButton={canUseButton}
                isConnected={isConnected}
                onStartCall={handleStartCall}
                onEndCall={handleDisconnect}
                onToggleMic={handleToggleMic}
              />
              
              {/* Weather Alert Button - only show when not in active call */}
              {!isConnected && !isConnecting && (
                <div className="mt-2">
                  <WeatherAlertButton />
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Microphone error overlay */}
      {micError && (
        <MicrophoneError
          onRetry={handleStartCall}
          onDismiss={() => setMicError(false)}
        />
      )}
    </div>
  );
}
