// src/app/api/document/[id]/signed-url/route.ts
/**
 * Generate signed URL for private S3 file access
 * For security: Only allows access to files owned by authenticated user
 */

import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { getSignedUrlFromUrl } from "@/lib/s3";

export const runtime = "nodejs";

type ParamsType = { params: Promise<{ id: string }> };

/**
 * GET /api/document/[id]/signed-url
 * Generate temporary signed URL for file access (expires in 1 hour)
 */
export async function GET(req: NextRequest, { params }: ParamsType) {
  const { id } = await params;

  // Get query parameter to check if download mode
  const searchParams = req.nextUrl.searchParams;
  const downloadMode = searchParams.get('download') === 'true';

  // 1️⃣ Check authentication
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // 2️⃣ Extract userId with fallback
  let userId = (session.user as any).id as string | undefined;
  if (!userId && session.user.email) {
    const u = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });
    userId = u?.id;
  }

  // 3️⃣ Final validation
  if (!userId) {
    return NextResponse.json({ error: "No user id in session" }, { status: 401 });
  }

  try {
    // 4️⃣ Verify ownership - user can only access their own files
    const file = await prisma.documentFile.findFirst({
      where: { id, userId },
    });

    if (!file) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    // Check if fileUrl exists
    if (!file.fileUrl) {
      return NextResponse.json({ error: "File URL is missing" }, { status: 404 });
    }

    // 5️⃣ Generate signed URL
    const fileNameForDownload = file.name || file.fileName || 'download';
    const inline = !downloadMode; // If download mode, use attachment; otherwise inline

    const signedUrl = await getSignedUrlFromUrl(
      file.fileUrl,
      3600,
      fileNameForDownload,
      inline // true = preview (inline), false = download (attachment)
    ); // 1 hour expiration

    // 6️⃣ Return signed URL
    return NextResponse.json({
      ok: true,
      url: signedUrl,
      expiresIn: 3600, // seconds
    });
  } catch (err: any) {
    console.error("SIGNED_URL_ERROR", err);
    return NextResponse.json({ error: err?.message || "Failed to generate URL" }, { status: 500 });
  }
}
