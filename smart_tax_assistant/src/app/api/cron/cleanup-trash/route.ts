// src/app/api/cron/cleanup-trash/route.ts

import { NextResponse } from 'next/server';
import { cleanupExpiredTrash } from '@/lib/cron/cleanup-trash';

export async function GET(req: Request) {
  try {
    // Verify request comes from authorized source (e.g., cron service)
    const authHeader = req.headers.get('authorization');

    // Optional: Add authentication check
    // Example: if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    //   return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    // }

    const result = await cleanupExpiredTrash();

    if (result.success) {
      return NextResponse.json({
        ok: true,
        message: 'Trash cleanup completed',
        deletedFiles: result.deletedFiles,
        deletedFolders: result.deletedFolders,
      });
    } else {
      return NextResponse.json(
        { error: 'Cleanup failed', details: result.error },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Error in cleanup cron endpoint:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export const dynamic = 'force-dynamic';
