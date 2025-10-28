// src/app/api/document/[id]/rename/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';

type ParamsType = { params: Promise<{ id: string }> };

// Validation: invalid filename characters
const INVALID_FILENAME_CHARS = /[\/\\:\*\?"<>\|]/;

// PATCH /api/document/[id]/rename - Rename a file
export async function PATCH(req: Request, { params }: ParamsType) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const { id } = await params;
    const body = await req.json();
    const { name } = body;

    // Validate: name is required
    if (!name || typeof name !== 'string') {
      return NextResponse.json({ error: 'Name is required' }, { status: 400 });
    }

    // Trim whitespace
    const trimmedName = name.trim();

    // Validate: name cannot be empty after trim
    if (trimmedName.length === 0) {
      return NextResponse.json({ error: 'Name cannot be empty' }, { status: 400 });
    }

    // Validate: max length
    if (trimmedName.length > 255) {
      return NextResponse.json({ error: 'Name too long (max 255 characters)' }, { status: 400 });
    }

    // Validate: invalid characters
    if (INVALID_FILENAME_CHARS.test(trimmedName)) {
      return NextResponse.json({
        error: 'Name contains invalid characters: / \\ : * ? " < > |'
      }, { status: 400 });
    }

    // Get user ID
    const user = await prisma.user.findUnique({
      where: { email: session.user.email },
      select: { id: true },
    });

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    // Get the file to rename
    const file = await prisma.documentFile.findFirst({
      where: {
        id,
        userId: user.id,
        isDeleted: false,
      },
      select: {
        id: true,
        name: true,
        folderId: true,
      },
    });

    if (!file) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }

    // Check for duplicate name in same folder
    const duplicate = await prisma.documentFile.findFirst({
      where: {
        userId: user.id,
        folderId: file.folderId,
        name: trimmedName,
        isDeleted: false,
        id: { not: id }, // Exclude current file
      },
    });

    if (duplicate) {
      return NextResponse.json({
        error: 'A file with this name already exists in this folder'
      }, { status: 409 });
    }

    // Update the file name
    const updatedFile = await prisma.documentFile.update({
      where: { id },
      data: { name: trimmedName },
      include: { folder: true },
    });

    console.log(`[Rename File] Renamed file ${file.name} → ${trimmedName}`);

    return NextResponse.json({
      ok: true,
      message: 'File renamed successfully',
      document: updatedFile,
    });

  } catch (error) {
    console.error('[Rename File] Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
