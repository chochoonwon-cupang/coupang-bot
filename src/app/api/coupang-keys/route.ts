import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { supabaseAdmin } from "@/lib/supabase";

export async function GET(request: Request) {
  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("auth_session");
    if (!sessionCookie?.value) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }
    const session = JSON.parse(sessionCookie.value);
    const mainUsername = (session?.username ?? "").trim();
    if (!mainUsername) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const account = (searchParams.get("account") ?? mainUsername).trim() || mainUsername;

    // 권한: 본인 또는 managed_usernames에 있는 계정만 조회 가능
    const { data: userRow } = await supabaseAdmin
      .from("users")
      .select("managed_usernames")
      .eq("username", mainUsername)
      .single();
    const managed = ((userRow?.managed_usernames ?? "") as string)
      .split(",")
      .map((s: string) => s.trim())
      .filter(Boolean);
    const allowed = account === mainUsername || managed.includes(account);
    if (!allowed) {
      return NextResponse.json({ error: "해당 계정에 대한 권한이 없습니다." }, { status: 403 });
    }

    const { data, error } = await supabaseAdmin
      .from("users")
      .select("coupang_access_key, coupang_secret_key")
      .eq("username", account)
      .single();

    if (error && error.code !== "PGRST116") throw error;
    const ak = (data?.coupang_access_key ?? "") as string;
    const sk = (data?.coupang_secret_key ?? "") as string;
    return NextResponse.json({
      coupang_access_key: ak,
      coupang_secret_key: sk,
    });
  } catch (e) {
    console.error("[API] coupang-keys get error:", e);
    return NextResponse.json(
      { error: "설정 조회 실패" },
      { status: 500 }
    );
  }
}

export async function PUT(request: Request) {
  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("auth_session");
    if (!sessionCookie?.value) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }
    const session = JSON.parse(sessionCookie.value);
    if (!session?.username) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }

    const body = await request.json();
    const access_key = String(body.coupang_access_key ?? body.access_key ?? "").trim();
    const secret_key = String(body.coupang_secret_key ?? body.secret_key ?? "").trim();
    const apply_to_all = Boolean(body.apply_to_all);
    const mainUsername = (session?.username ?? "").trim();

    if (!mainUsername) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }

    if (apply_to_all) {
      // 전체아이디사용: 메인 + managed_usernames 전체에 동일 API 키 저장
      const { data: userRow } = await supabaseAdmin
        .from("users")
        .select("managed_usernames")
        .eq("username", mainUsername)
        .single();
      const managedStr = (userRow?.managed_usernames ?? "") as string;
      const managed = managedStr.split(",").map((s: string) => s.trim()).filter(Boolean);
      const accountsToUpdate = [mainUsername, ...managed];

      let updatedCount = 0;
      for (const account of accountsToUpdate) {
        const { error } = await supabaseAdmin
          .from("users")
          .update({ coupang_access_key: access_key, coupang_secret_key: secret_key })
          .eq("username", account);
        if (!error) updatedCount += 1;
      }
      return NextResponse.json({ ok: true, updated_count: updatedCount, accounts: accountsToUpdate });
    }

    const account = (body.account ?? mainUsername).trim() || mainUsername;
    if (!account) {
      return NextResponse.json({ error: "저장할 계정이 지정되지 않았습니다." }, { status: 400 });
    }

    // 권한: 본인 또는 managed_usernames에 있는 계정만 저장 가능
    const { data: userRow } = await supabaseAdmin
      .from("users")
      .select("managed_usernames")
      .eq("username", mainUsername)
      .single();
    const managed = ((userRow?.managed_usernames ?? "") as string)
      .split(",")
      .map((s: string) => s.trim())
      .filter(Boolean);
    const allowed = account === mainUsername || managed.includes(account);
    if (!allowed) {
      return NextResponse.json({ error: "해당 계정에 대한 권한이 없습니다." }, { status: 403 });
    }

    const { data, error } = await supabaseAdmin
      .from("users")
      .update({
        coupang_access_key: access_key,
        coupang_secret_key: secret_key,
      })
      .eq("username", account)
      .select("username, coupang_access_key");

    if (error) {
      console.error("[API] coupang-keys put error:", error);
      return NextResponse.json(
        { error: "저장 실패", message: error.message, details: error.details },
        { status: 500 }
      );
    }
    if (!data || data.length === 0) {
      console.error("[API] coupang-keys put: no rows updated, account=", account);
      return NextResponse.json(
        { error: "저장 실패", message: "해당 사용자를 찾을 수 없습니다." },
        { status: 404 }
      );
    }
    return NextResponse.json({ ok: true, updated: data[0]?.username });
  } catch (e) {
    console.error("[API] coupang-keys put error:", e);
    return NextResponse.json(
      { error: "저장 실패", message: String(e) },
      { status: 500 }
    );
  }
}
