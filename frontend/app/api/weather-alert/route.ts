import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

/**
 * Weather Alert Call API
 * 
 * Triggers an outbound weather alert call via Linphone SIP.
 * 
 * POST /api/weather-alert
 *   Body: { "action": "initiate_weather_alert", "userId": "..." }
 *   
 * Returns:
 *   Success: { "success": true, "call_id": "...", "status": "initiated", "message": "..." }
 *   Failure: { "success": false, "error": "...", "message": "..." }
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8080';

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    
    // Validate request
    if (body.action !== 'initiate_weather_alert') {
      return NextResponse.json(
        {
          success: false,
          error: 'INVALID_ACTION',
          message: 'Invalid action specified.'
        },
        { status: 400 }
      );
    }
    
    // Extract userId from request body
    const userId = body.userId || null;
    
    // Forward to Python backend with userId
    const response = await fetch(`${BACKEND_URL}/api/weather-alert/call`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        action: 'initiate_weather_alert',
        user_id: userId,  // Include userId for personalization
      }),
      signal: AbortSignal.timeout(15000), // 15 second timeout
    });
    
    const data = await response.json();
    
    // Return response
    return NextResponse.json(data, {
      status: response.ok ? 200 : response.status,
      headers: {
        'Cache-Control': 'no-store',
      },
    });
    
  } catch (error) {
    console.error('[WeatherAlertAPI] Error:', error);
    
    const message = error instanceof Error ? error.message : 'Internal server error';
    
    return NextResponse.json(
      {
        success: false,
        error: 'INTERNAL_ERROR',
        message: 'Failed to initiate weather alert call.'
      },
      { status: 500 }
    );
  }
}

/**
 * Get call status
 * 
 * GET /api/weather-alert?call_id=xxx
 */
export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const callId = searchParams.get('call_id');
    
    if (!callId) {
      return NextResponse.json(
        {
          success: false,
          error: 'MISSING_CALL_ID',
          message: 'call_id parameter is required.'
        },
        { status: 400 }
      );
    }
    
    // Forward to Python backend
    const response = await fetch(`${BACKEND_URL}/api/weather-alert/call/${callId}`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    
    const data = await response.json();
    
    return NextResponse.json(data, {
      status: response.ok ? 200 : response.status,
      headers: {
        'Cache-Control': 'no-store',
      },
    });
    
  } catch (error) {
    console.error('[WeatherAlertAPI] Status error:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: 'INTERNAL_ERROR',
        message: 'Failed to get call status.'
      },
      { status: 500 }
    );
  }
}
