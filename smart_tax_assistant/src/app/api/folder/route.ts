// src/app/api/folder/route.ts

import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import prisma from '@/lib/prisma';
import { authOptions } from '@/lib/auth';

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email)
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const folders = await prisma.documentFolder.findMany({
    where: {
      user: { email: session.user.email },
      isDeleted: false
    },
    include: {
      children: true,
      files: {
        where: { isDeleted: false }
      }
    },
  });

  return NextResponse.json(folders);
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email)
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await req.json();
  const { name, color, parentId } = body;

  const folder = await prisma.documentFolder.create({
    data: {
      name,
      color: color || '#3B82F6',
      ...(parentId && {
        parent: { connect: { id: parentId } }
      }),
      user: { connect: { email: session.user.email } },
    },
  });

  return NextResponse.json(folder);
}

