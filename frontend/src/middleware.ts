import { NextRequest, NextResponse } from "next/server";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  // Exclude login, password reset, email verification, and static public routes
  if (
    pathname === "/sign-in" ||
    pathname === "/sign-up" ||
    pathname === "/forgot-password" ||
    pathname === "/verify-email" ||
    pathname.startsWith("/reset-password/") ||
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/models/")
  ) {
    return NextResponse.next();
  }

  // Proxy the cookie to your backend user check
  const cookieHeader = request.headers.get("cookie") || "";
  const API_URL =
    typeof window === "undefined"
      ? process.env.INTERNAL_API_URL // server/middleware/SSR
      : process.env.NEXT_PUBLIC_API_URL; // client/browser

  const res = await fetch(`${API_URL}/api/v1/auth/profiles/me/`, {
    credentials: "include",
    headers: {
      Cookie: cookieHeader,
      "X-Forwarded-Proto": "https",
    },
  });

  if (res.status !== 200) {
    // Not authenticated: redirect to login
    return NextResponse.redirect(new URL("/sign-in", request.url));
  }

  return NextResponse.next();
}
