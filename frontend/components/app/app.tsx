'use client';

import { useMemo } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { GeolocationProvider, useGeolocationContext } from '@/contexts/GeolocationContext';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { getSandboxTokenSource } from '@/lib/utils';

interface AppProps {
  appConfig: AppConfig;
}

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function getSandboxTokenSourceWithGeo(appConfig: AppConfig, coordinates: { latitude: number; longitude: number } | null) {
  return TokenSource.custom(async () => {
    const url = new URL(process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT!, window.location.origin);
    const sandboxId = appConfig.sandboxId ?? '';
    const roomConfig = appConfig.agentName
      ? {
          agents: [
            {
              agent_name: appConfig.agentName,
              ...(coordinates && {
                latitude: coordinates.latitude,
                longitude: coordinates.longitude,
              }),
            },
          ],
        }
      : undefined;

    try {
      const res = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Sandbox-Id': sandboxId,
        },
        body: JSON.stringify({ room_config: roomConfig }),
      });
      if (!res.ok) throw new Error(`Failed to get token: ${res.statusText}`);
      return await res.json();
    } catch (error) {
      console.error('Failed to get connection details:', error);
      throw error;
    }
  });
}

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

export function App({ appConfig }: AppProps) {
  return (
    <GeolocationProvider>
      <AppInner appConfig={appConfig} />
    </GeolocationProvider>
  );
}

function AppInner({ appConfig }: AppProps) {
  const { coordinates } = useGeolocationContext();

  const tokenSource = useMemo(() => {
    if (typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string') {
      return getSandboxTokenSourceWithGeo(appConfig, coordinates);
    }
    
    // Create a token source that includes geolocation
    return TokenSource.custom(async () => {
      const response = await fetch('/api/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...(coordinates && {
            latitude: coordinates.latitude,
            longitude: coordinates.longitude,
          }),
        }),
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(`Token request failed: ${error.error || response.statusText}`);
      }
      
      return response.json();
    });
  }, [appConfig, coordinates]);

  const session = useSession(
    tokenSource,
    appConfig.agentName ? { agentName: appConfig.agentName } : undefined
  );

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />
      <main className="relative min-h-svh w-full overflow-hidden">
        <ViewController appConfig={appConfig} />
      </main>
      <StartAudioButton label="Start Audio" />
      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}
