'use client';

import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { useLoading } from '@/contexts/LoadingContext';

export default function RouteChangeListener() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { stopLoading } = useLoading();

  useEffect(() => {
    // Stop loading when route changes
    stopLoading();
  }, [pathname, searchParams, stopLoading]);

  return null;
}
