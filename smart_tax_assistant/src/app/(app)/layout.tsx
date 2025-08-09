// app/(app)/layout.tsx
export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Layout นี้จะไม่มี Navbar และ Footer ส่วนกลาง
  // เพื่อให้แต่ละหน้าใน (app) จัดการ Navigation ของตัวเองได้
  return <>{children}</>;
}