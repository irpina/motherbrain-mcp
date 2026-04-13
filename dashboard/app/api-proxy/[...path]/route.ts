import { type NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_INTERNAL_URL ?? "http://api:8000";
const API_KEY = process.env.API_KEY ?? "supersecret";

async function proxy(
  request: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
) {
  await ctx.params; // ensure params are resolved (unused but required by Next.js types)

  // Preserve trailing slash from original request
  const rawPath = request.nextUrl.pathname.replace(/^\/api-proxy/, "");
  const search = request.nextUrl.search;
  const target = API_URL + rawPath + search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  
  // Inject API key - server-side only, browser never sees this
  headers.set("X-API-Key", API_KEY);

  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : request.body;

  const upstream = await fetch(target, {
    method: request.method,
    headers,
    body,
    redirect: "follow",
    // @ts-expect-error duplex required for streaming body
    duplex: "half",
  });

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: upstream.headers,
  });
}

export const GET = (
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
) => proxy(req, ctx);
export const POST = (
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
) => proxy(req, ctx);
export const PUT = (
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
) => proxy(req, ctx);
export const PATCH = (
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
) => proxy(req, ctx);
export const DELETE = (
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
) => proxy(req, ctx);
export const OPTIONS = (
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
) => proxy(req, ctx);
