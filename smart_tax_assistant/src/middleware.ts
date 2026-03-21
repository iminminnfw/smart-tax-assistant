export { default } from 'next-auth/middleware';

export const config = {
  matcher: [
    /*
     * protect ทุก route ยกเว้น:
     * - / (landing page)
     * - /auth/* (login, verify-email)
     * - /api/auth/* (NextAuth endpoints)
     * - /api/cron/* (cron jobs — เรียกจาก backend)
     * - /privacy, /terms
     * - static files (_next, favicon, images)
     */
    '/((?!$|auth|api/auth|api/cron|privacy|terms|_next/static|_next/image|favicon.ico).*)',
  ],
};
