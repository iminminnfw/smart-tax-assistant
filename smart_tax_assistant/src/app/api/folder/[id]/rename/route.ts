// src/app/api/folder/[id]/rename/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';

type ParamsType = { params: Promise<{ id: string }> };

// Validation: invalid folder name characters
const INVALID_FOLDER_CHARS = /[\/\\:\*\?"<>\|]/;

// PATCH /api/folder/[id]/rename - Rename a folder
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
    if (INVALID_FOLDER_CHARS.test(trimmedName)) {
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

    // Get the folder to rename
    const folder = await prisma.documentFolder.findFirst({
      where: {
        id,
        userId: user.id,
        isDeleted: false,
      },
      select: {
        id: true,
        name: true,
        parentId: true,
      },
    });

    if (!folder) {
      return NextResponse.json({ error: 'Folder not found' }, { status: 404 });
    }

    // Check for duplicate name in same parent
    const duplicate = await prisma.documentFolder.findFirst({
      where: {
        userId: user.id,
        parentId: folder.parentId,
        name: trimmedName,
        isDeleted: false,
        id: { not: id }, // Exclude current folder
      },
    });

    if (duplicate) {
      return NextResponse.json({
        error: 'A folder with this name already exists in this location'
      }, { status: 409 });
    }

    // Update the folder name
    const updatedFolder = await prisma.documentFolder.update({
      where: { id },
      data: { name: trimmedName },
      include: {
        parent: true,
        files: {
          where: { isDeleted: false },
          orderBy: { createdAt: 'desc' },
        },
        subfolders: {
          where: { isDeleted: false },
          orderBy: { createdAt: 'desc' },
        },
      },
    });

    console.log(`[Rename Folder] Renamed folder ${folder.name} → ${trimmedName}`);

    return NextResponse.json({
      ok: true,
      message: 'Folder renamed successfully',
      folder: updatedFolder,
    });

  } catch (error) {
    console.error('[Rename Folder] Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
