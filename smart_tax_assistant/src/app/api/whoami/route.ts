import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth"; // <- path ที่ export authOptions จริง

export async function GET() {
  const session = await getServerSession(authOptions);
  return NextResponse.json({ user: session?.user ?? null });
}
