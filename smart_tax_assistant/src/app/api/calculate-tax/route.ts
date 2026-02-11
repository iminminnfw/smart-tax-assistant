import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

// Increase timeout for long AI processing
export const maxDuration = 3600; // 1 hour for Vercel
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    console.log('[Proxy] ========================================');
    console.log('[Proxy] Forwarding to backend:', BACKEND_URL);
    console.log('[Proxy] This may take a while (up to 1 hour for AI)...');

    // Use native http module for long requests
    const response = await fetch(`${BACKEND_URL}/api/calculate-tax`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      // @ts-ignore - Next.js specific options
      next: { revalidate: 0 },
    });

    console.log('[Proxy] Backend response status:', response.status);

    const text = await response.text();
    console.log('[Proxy] Backend response body:', text.slice(0, 1000));

    let data;
    try {
      data = JSON.parse(text);
    } catch {
      console.error('[Proxy] Failed to parse JSON:', text);
      return NextResponse.json(
        {
          error: 'Backend returned invalid response',
          detail: text,
          status: response.status
        },
        { status: 500 }
      );
    }

    if (!response.ok) {
      console.error('[Proxy] Backend error:', JSON.stringify(data, null, 2));
      return NextResponse.json(
        {
          error: data.detail || 'Backend error',
          error_type: data.error_type || 'Unknown',
          traceback: data.traceback || '',
          status: response.status
        },
        { status: response.status }
      );
    }

    console.log('[Proxy] Success!');
    return NextResponse.json(data);
  } catch (error) {
    console.error('[Proxy] Connection error:', error);
    return NextResponse.json(
      {
        error: 'Failed to connect to backend',
        detail: String(error),
        hint: 'Make sure Python backend is running on port 8001'
      },
      { status: 500 }
    );
  }
}
