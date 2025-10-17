'use client';

import styled, { keyframes } from 'styled-components';

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const fadeIn = keyframes`
  from { opacity: 0; }
  to { opacity: 1; }
`;

const LoaderOverlay = styled.div<{ $isVisible: boolean }>`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  opacity: ${props => props.$isVisible ? 1 : 0};
  pointer-events: ${props => props.$isVisible ? 'all' : 'none'};
  transition: opacity 0.3s ease-in-out;
  animation: ${fadeIn} 0.3s ease-in-out;
`;

const SpinnerContainer = styled.div`
  position: relative;
  width: 80px;
  height: 80px;
`;

const Spinner = styled.div`
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid transparent;
  border-top-color: #3b82f6;
  border-right-color: #8b5cf6;
  border-radius: 50%;
  animation: ${spin} 1s cubic-bezier(0.5, 0, 0.5, 1) infinite;
`;

const SpinnerInner = styled.div`
  position: absolute;
  width: 60px;
  height: 60px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 4px solid transparent;
  border-bottom-color: #ec4899;
  border-left-color: #f59e0b;
  border-radius: 50%;
  animation: ${spin} 0.75s cubic-bezier(0.5, 0, 0.5, 1) infinite reverse;
`;

const LoadingText = styled.div`
  margin-top: 24px;
  font-size: 16px;
  font-weight: 600;
  color: #4b5563;
  letter-spacing: 0.5px;
`;

const LoadingSubtext = styled.div`
  margin-top: 8px;
  font-size: 14px;
  color: #9ca3af;
`;

interface GlobalLoaderProps {
  isLoading: boolean;
  text?: string;
  subtext?: string;
}

export default function GlobalLoader({
  isLoading,
  text = 'กำลังโหลด...',
  subtext = 'โปรดรอสักครู่'
}: GlobalLoaderProps) {
  return (
    <LoaderOverlay $isVisible={isLoading}>
      <SpinnerContainer>
        <Spinner />
        <SpinnerInner />
      </SpinnerContainer>
      <LoadingText>{text}</LoadingText>
      <LoadingSubtext>{subtext}</LoadingSubtext>
    </LoaderOverlay>
  );
}
