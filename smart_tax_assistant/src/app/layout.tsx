// app/layout.tsx

import '../styles/globals.css'; // ✅ แก้ path ให้ถูกต้อง

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
