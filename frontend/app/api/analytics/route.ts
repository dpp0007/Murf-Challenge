import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const path = url.pathname.replace("/api/analytics", "");
    const query = url.search;

    const fullUrl = `http://localhost:8080/api/analytics${path}${query}`;

    const response = await fetch(fullUrl, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: `Backend error: ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("[Analytics Proxy]", error);
    return NextResponse.json(
      { error: "Analytics proxy error", details: String(error) },
      { status: 500 }
    );
  }
}
