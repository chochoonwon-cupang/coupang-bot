import { NextResponse } from "next/server";

export async function GET() {
  console.log("[cron] /api/request called", new Date().toISOString());
  return NextResponse.json({ ok: true, ts: new Date().toISOString() });
}