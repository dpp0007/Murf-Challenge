'use client';

import type { AppConfig } from '@/app-config';
import { KisanMainView } from '@/components/kisan/KisanMainView';

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig: _appConfig }: ViewControllerProps) {
  return <KisanMainView />;
}

