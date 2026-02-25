import { NextResponse } from "next/server";
import { cookies } from "next/headers";

async function doLogout() {
  const cookieStore = await cookies();
  cookieStore.delete("auth_session");
}

export async function GET(request: Request) {
  try {
    await doLogout();
    const url = new URL(request.url);
    return NextResponse.redirect(new URL("/", url.origin));
  } catch {
    return NextResponse.redirect(new URL("/", "http://localhost:3000"));
  }
}

export async function POST() {
  try {
    await doLogout();
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ ok: true });
  }
}
