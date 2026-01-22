// app/api/document/route.ts
import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";         //ต้องเป็นไฟล์เดียวกับที่ [...nextauth] ใช้
import prisma from "@/lib/prisma";                 

export const runtime = "nodejs";

function jsonOk(data: unknown, init?: number) {
  return NextResponse.json(data, { status: init ?? 200 });
}
function jsonErr(message: string, status = 400, extra?: Record<string, unknown>) {
  return NextResponse.json({ error: message, ...(extra ?? {}) }, { status });
}

async function requireUserId() {
  const session = await getServerSession(authOptions);
  if (!session?.user) return { userId: null as string | null, session };

  // บางเคส session.user.id อาจหาย ให้ลองดึงจาก email
  let userId = (session.user as any).id as string | undefined;
  if (!userId && session.user.email) {
    const u = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });
    userId = u?.id;
  }
  return { userId: userId ?? null, session };
}


export async function GET(req: NextRequest) {
  try {
    const { userId } = await requireUserId();
    if (!userId) return jsonErr("Unauthorized", 401);

    const { searchParams } = new URL(req.url);
    const folderId = searchParams.get("folderId");
    const q = searchParams.get("q")?.trim() || "";
    const skip = Math.max(0, Number(searchParams.get("skip") ?? 0) || 0);
    const takeRaw = Number(searchParams.get("take") ?? 20) || 20;
    const take = Math.min(Math.max(takeRaw, 1), 100);

    const where: any = { userId, isDeleted: false };
    if (folderId) where.folderId = folderId;
    if (q) {
      where.OR = [
        { name: { contains: q, mode: "insensitive" } },
        { fileName: { contains: q, mode: "insensitive" } },
        { content: { contains: q, mode: "insensitive" } }, // ถ้าเก็บ OCR/text
        { tags: { has: q } },                               // ถ้า q ตรง tag พอดี
      ];
    }

    const [items, total] = await Promise.all([
      prisma.documentFile.findMany({
        where,
        orderBy: { createdAt: "desc" },
        skip,
        take,
      }),
      prisma.documentFile.count({ where }),
    ]);

    return jsonOk({ items, total, skip, take });
  } catch (err: any) {
    console.error("DOCUMENT_GET_ERROR", err);
    return jsonErr(err?.message || "Failed to fetch documents", 500);
  }
}


export async function POST(req: NextRequest) {
  try {
    const { userId } = await requireUserId();
    if (!userId) return jsonErr("Unauthorized", 401);

    let body: any = null;
    try {
      body = await req.json();
    } catch {
      return jsonErr("Invalid JSON body", 400);
    }

    const {
      name,
      fileUrl = null,
      fileName = null,
      fileSize = null,
      mimeType = null,
      isUploaded,
      type = null,
      tags = [],
      folderId = null,
    } = body ?? {};

    if (!name || typeof name !== "string") {
      return jsonErr("Field 'name' is required (string).", 400);
    }
    if (tags && !Array.isArray(tags)) {
      return jsonErr("Field 'tags' must be string[]", 400);
    }

    // ถ้าสคีมาไม่ได้ตั้ง default ให้ createdAt/updatedAt ให้เติมเอง
    const now = new Date();

    const doc = await prisma.documentFile.create({
      data: {
        userId,                 //ต้องเป็น string แน่ ๆ
        folderId: folderId ?? null,
        name,
        fileUrl,
        fileName,
        fileSize: fileSize ?? null,
        mimeType,
        isUploaded: typeof isUploaded === "boolean" ? isUploaded : !!fileUrl,
        type,
        tags: tags as string[],
        createdAt: now,         
        updatedAt: now,         
      },
    });

    return jsonOk({ ok: true, id: doc.id, document: doc }, 201);
  } catch (err: any) {
    console.error("DOCUMENT_POST_ERROR", err);
    return jsonErr(err?.message || "Failed to create document", 500);
  }
}
