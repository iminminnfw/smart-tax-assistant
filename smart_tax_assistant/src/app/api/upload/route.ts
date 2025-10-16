// src/app/api/upload/route.ts
import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { mkdir, writeFile } from "fs/promises";
import path from "path";
import prisma from "@/lib/prisma";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let userId = (session.user as any).id as string | undefined;
  if (!userId && session.user.email) {
    const u = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });
    userId = u?.id;
  }
  if (!userId) {
    return NextResponse.json({ error: "No user id in session" }, { status: 401 });
  }

  try {
    const form = await req.formData();
    const file = form.get("file") as File | null;
    if (!file) return NextResponse.json({ error: "Missing file" }, { status: 400 });

    const type = String(form.get("type") ?? "OTHER");
    let tags: string[] = [];
    try { tags = JSON.parse(String(form.get("tags") ?? "[]")); } catch {}

    const folderId = (form.get("folderId") as string) || null;

    console.log('File info:', {
      name: file.name,
      type: file.type,
      size: file.size
    }); // Debug log

    const bytes = Buffer.from(await file.arrayBuffer());
    const uploadDir = path.join(process.cwd(), "public", "uploads", userId);
    await mkdir(uploadDir, { recursive: true });
    const safe = file.name.replace(/[^\w.\-]+/g, "_");
    const filename = `${Date.now()}_${safe}`;
    await writeFile(path.join(uploadDir, filename), bytes);
    const publicUrl = `/uploads/${userId}/${filename}`;

    // ⭐ ใช้ mimeType จาก file.type แต่ถ้าไม่มีก็เดาจากนามสกุล
    let mimeType = file.type;
    if (!mimeType) {
      const ext = file.name.split('.').pop()?.toLowerCase();
      switch (ext) {
        case 'png': mimeType = 'image/png'; break;
        case 'jpg':
        case 'jpeg': mimeType = 'image/jpeg'; break;
        case 'gif': mimeType = 'image/gif'; break;
        case 'webp': mimeType = 'image/webp'; break;
        case 'pdf': mimeType = 'application/pdf'; break;
        case 'mp4': mimeType = 'video/mp4'; break;
        case 'mp3': mimeType = 'audio/mpeg'; break;
        case 'txt': mimeType = 'text/plain'; break;
        default: mimeType = 'application/octet-stream';
      }
    }

    console.log('Final mimeType:', mimeType); // Debug log

    const doc = await prisma.documentFile.create({
      data: {
        userId,
        folderId,
        name: file.name,
        type,
        tags,
        fileUrl: publicUrl,
        fileName: file.name,
        fileSize: file.size,
        mimeType: file.type || 'application/octet-stream',
        isUploaded: true,
      },
    });

    console.log('Saved document:', doc); // Debug log

    return NextResponse.json({ 
      ok: true, 
      id: doc.id, 
      url: publicUrl, 
      document: doc
    });
  } catch (err: any) {
    console.error("UPLOAD_ERROR", err);
    return NextResponse.json({ error: err?.message || "Upload failed" }, { status: 500 });
  }
}