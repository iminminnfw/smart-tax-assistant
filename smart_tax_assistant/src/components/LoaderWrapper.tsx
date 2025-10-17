'use client';

import { useLoading } from '@/contexts/LoadingContext';
import GlobalLoader from '@/components/GlobalLoader';

export default function LoaderWrapper() {
  const { isLoading, loadingText, loadingSubtext } = useLoading();
  return <GlobalLoader isLoading={isLoading} text={loadingText} subtext={loadingSubtext} />;
}
