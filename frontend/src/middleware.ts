import { NextRequest, NextResponse } from "next/server";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public routes that don't require authentication
  const publicRoutes = [
    "/sign-in",
    "/sign-up",
    "/forgot-password",
    "/verify-email",
    "/complete-researcher-profile",
  ];

  // Check if current path is public
  const isPublicRoute =
    publicRoutes.includes(pathname) ||
    pathname.startsWith("/reset-password/") ||
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/models/");

  if (isPublicRoute) {
    return NextResponse.next();
  }

  // For protected routes, verify authentication
  const cookieHeader = request.headers.get("cookie") || "";
  const API_URL =
    typeof window === "undefined"
      ? process.env.INTERNAL_API_URL // server/middleware/SSR
      : process.env.NEXT_PUBLIC_API_URL; // client/browser

  try {
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

    // Optional: Check if researcher needs to complete profile
    // and redirect them if they try to access other pages
    const userData = await res.json();
    if (
      userData.role === "researcher_pending" ||
      (userData.needs_researcher_profile_completion &&
        pathname !== "/complete-researcher-profile")
    ) {
      // Redirect pending researchers to complete their profile
      return NextResponse.redirect(
        new URL("/complete-researcher-profile", request.url),
      );
    }

    return NextResponse.next();
  } catch (error) {
    console.error("Middleware auth check failed:", error); // eslint-disable-line no-console
    // If fetch fails, redirect to login
    return NextResponse.redirect(new URL("/sign-in", request.url));
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\..*|models).*)",
  ],
};
