'use client';

import { createContext, useContext, useState, useRef, ReactNode } from 'react';

interface LoadingContextType {
  isLoading: boolean;
  loadingText: string;
  loadingSubtext: string;
  setLoading: (loading: boolean, text?: string, subtext?: string) => void;
  startLoading: (text?: string, subtext?: string) => void;
  stopLoading: () => void;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

const MINIMUM_LOADING_TIME = 1500; // 1.5 seconds

export function LoadingProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('กำลังโหลด...');
  const [loadingSubtext, setLoadingSubtext] = useState('โปรดรอสักครู่');
  const loadingStartTime = useRef<number | null>(null);
  const pendingTimeout = useRef<NodeJS.Timeout | null>(null);

  const setLoading = (
    loading: boolean,
    text: string = 'กำลังโหลด...',
    subtext: string = 'โปรดรอสักครู่'
  ) => {
    if (loading) {
      // Starting to load
      loadingStartTime.current = Date.now();
      setIsLoading(true);
      setLoadingText(text);
      setLoadingSubtext(subtext);
    } else {
      // Stopping load - ensure minimum time
      const elapsedTime = loadingStartTime.current
        ? Date.now() - loadingStartTime.current
        : MINIMUM_LOADING_TIME;

      const remainingTime = Math.max(0, MINIMUM_LOADING_TIME - elapsedTime);

      // Clear any pending timeout
      if (pendingTimeout.current) {
        clearTimeout(pendingTimeout.current);
      }

      // Wait remaining time before hiding
      pendingTimeout.current = setTimeout(() => {
        setIsLoading(false);
        loadingStartTime.current = null;
      }, remainingTime);
    }
  };

  const startLoading = (
    text: string = 'กำลังโหลด...',
    subtext: string = 'โปรดรอสักครู่'
  ) => {
    setLoading(true, text, subtext);
  };

  const stopLoading = () => {
    setLoading(false);
  };

  return (
    <LoadingContext.Provider
      value={{
        isLoading,
        loadingText,
        loadingSubtext,
        setLoading,
        startLoading,
        stopLoading,
      }}
    >
      {children}
    </LoadingContext.Provider>
  );
}

export function useLoading() {
  const context = useContext(LoadingContext);
  if (context === undefined) {
    throw new Error('useLoading must be used within a LoadingProvider');
  }
  return context;
}
