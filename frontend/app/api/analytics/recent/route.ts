import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const query = url.search;

    // Use 127.0.0.1 instead of localhost to ensure proper resolution in server context
    const backendHost = process.env.BACKEND_URL || "http://127.0.0.1:8080";
    const backendUrl = `${backendHost}/api/analytics/recent${query}`;
    console.log(`[Analytics Proxy] Fetching from backend: ${backendUrl}`);

    let response;
    try {
      response = await fetch(backendUrl, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        signal: AbortSignal.timeout(10000), // 10 second timeout
      });
    } catch (fetchError) {
      console.error("[Analytics Proxy] Fetch error:", fetchError);
      return NextResponse.json(
        { error: "Failed to connect to backend", details: String(fetchError) },
        { status: 503 }
      );
    }

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`[Analytics Proxy] Backend error: ${response.status}`, errorBody);
      return NextResponse.json(
        { error: `Backend error: ${response.status}`, body: errorBody },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log(`[Analytics Proxy] Data received - ${data.calls?.length || 0} calls`);
    
    return NextResponse.json(data, {
      headers: {
        "Cache-Control": "no-store, no-cache, must-revalidate",
      },
    });
  } catch (error) {
    console.error("[Analytics Proxy] Unexpected error:", error);
    const errorMessage = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      { error: "Analytics proxy error", details: errorMessage },
      { status: 500 }
    );
  }
}
