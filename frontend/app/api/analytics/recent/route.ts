import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const query = url.search;

    const backendUrl = `http://localhost:8080/api/analytics/recent${query}`;
    console.log(`[Analytics Proxy] Fetching: ${backendUrl}`);

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });

    if (!response.ok) {
      console.error(`[Analytics Proxy] Backend error: ${response.status}`);
      return NextResponse.json(
        { error: `Backend error: ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log(`[Analytics Proxy] Data received:`, data);
    
    return NextResponse.json(data, {
      headers: {
        "Cache-Control": "no-store, no-cache, must-revalidate",
      },
    });
  } catch (error) {
    console.error("[Analytics Proxy] Error:", error);
    return NextResponse.json(
      { error: "Analytics proxy error", details: String(error) },
      { status: 500 }
    );
  }
}
