// src/components/SafeImage/SafeImage.tsx
'use client';
import React from 'react';

type Props = {
  src?: string | null;
  alt: string;
  className?: string;
};

export default function SafeImage({ src, alt, className }: Props) {
  const [error, setError] = React.useState(false);

  if (!src || error) {
    return (
      <div className={`flex items-center justify-center p-8 rounded-2xl border-2 border-dashed border-gray-300 bg-gray-50 text-gray-500 ${className ?? ''}`}>
        <div className="text-center">
          <div className="text-4xl mb-2">📷</div>
          <p>ไม่สามารถแสดงรูปภาพได้</p>
        </div>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setError(true)}
    />
  );
}