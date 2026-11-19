// Política de formato; el contenido se valida posteriormente al abrir el video.
export const VIDEO_MIME_TYPES = ["video/mp4", "video/quicktime", "video/webm"] as const;
export const VIDEO_ACCEPT = VIDEO_MIME_TYPES.join(",");
export const VIDEO_FORMAT_LABELS = ["MP4", "MOV", "WEBM"] as const;
export const VIDEO_FORMAT_ERROR = "Formato no compatible. Selecciona un video MP4, MOV o WEBM.";

export function isAcceptedVideoType(type: string): boolean {
  return VIDEO_MIME_TYPES.some((accepted) => accepted === type);
}
