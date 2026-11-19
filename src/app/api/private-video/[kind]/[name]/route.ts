import { stat, realpath, open } from "node:fs/promises";
import path from "node:path";
import { requireUser } from "@/lib/auth/guards";
import { prisma } from "@/lib/prisma";
export const runtime = "nodejs";
export async function GET(request: Request, context: { params: Promise<{ kind: string; name: string }> }) {
 const auth = await requireUser(); if ("error" in auth) return auth.error;
 const { kind, name } = await context.params;
 if (!["uploads-temp", "processed-videos"].includes(kind) || !/^[A-Za-z0-9_-]+\.(mp4|mov|webm)$/i.test(name)) return new Response(null, { status: 404 });
 const url = `/${kind}/${name}`;
 // ADMIN receives no implicit access: ownership is mandatory for every role.
 const video = await prisma.videoMarcha.findFirst({ where: { userId: auth.user.id, OR: [{ localOriginalVideoUrl: url }, { localProcessedVideoUrl: url }, { originalVideoUrl: url }, { processedVideoUrl: url }] } });
 if (!video) return new Response(null, { status: 404 });
 const root = await realpath(path.join(/* turbopackIgnore: true */ process.cwd(), "private-videos", kind));
 let file: string;
 try { file = await realpath(path.join(root, name)); } catch { return new Response(null, { status: 404 }); }
 if (path.dirname(file) !== root) return new Response(null, { status: 404 });
 const size = (await stat(file)).size; let start = 0; let end = size - 1;
 const range = request.headers.get("range");
 if (range) {
  const m = /^bytes=(\d*)-(\d*)$/.exec(range);
  if (!m || (!m[1] && !m[2])) return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });
  if (!m[1]) start = Math.max(0, size - Number(m[2]));
  else { start = Number(m[1]); if (m[2]) end = Math.min(end, Number(m[2])); }
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 || start > end || start >= size) return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });
 }
 const headers: Record<string,string> = { "Content-Type": name.toLowerCase().endsWith(".mov") ? "video/quicktime" : name.toLowerCase().endsWith(".webm") ? "video/webm" : "video/mp4", "Content-Length": String(end-start+1), "Accept-Ranges": "bytes", "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff" };
 if (range) headers["Content-Range"] = `bytes ${start}-${end}/${size}`;
 const handle = await open(file, "r");
 let position = start;
 let closed = false;
 let cancelled = false;
 async function closeFile() {
  if (closed) return;
  closed = true;
  await handle.close();
 }
 const body = new ReadableStream<Uint8Array>({
  async pull(controller) {
   if (closed) return;
   try {
    const chunk = Buffer.alloc(Math.min(64 * 1024, end - position + 1));
    const { bytesRead } = await handle.read(chunk, 0, chunk.length, position);
    if (cancelled) return;
    if (bytesRead) {
     position += bytesRead;
     controller.enqueue(new Uint8Array(chunk.subarray(0, bytesRead)));
    }
    if (!bytesRead || position > end) {
     await closeFile();
     if (!cancelled) controller.close();
    }
   } catch (error) {
    if (!cancelled) {
     await closeFile();
     controller.error(error);
    }
   }
  },
  async cancel() {
   cancelled = true;
   await closeFile();
  },
 });
 return new Response(body, { status: range ? 206 : 200, headers });
}
