import { existsSync } from "node:fs";
import { stat } from "node:fs/promises";
import { v2 as cloudinary, UploadApiResponse } from "cloudinary";

const DEFAULT_CLOUDINARY_FOLDER = "analisis-marcha/videos";
const LARGE_UPLOAD_THRESHOLD_BYTES = 90 * 1024 * 1024;

type VideoUploadOptions = {
  folder?: string;
  publicId?: string;
  tags?: string[];
};

export type CloudinaryVideoUploadOk = {
  ok: true;
  secureUrl: string;
  publicId: string;
  bytes: number | null;
  format: string | null;
  duration: number | null;
};

export type CloudinaryVideoUploadError = {
  ok: false;
  errorMessage: string;
  errorCode?: string;
};

export type CloudinaryVideoUpload =
  | CloudinaryVideoUploadOk
  | CloudinaryVideoUploadError;

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
  secure: true,
});

export function missingCloudinaryConfig() {
  return [
    ["CLOUDINARY_CLOUD_NAME", process.env.CLOUDINARY_CLOUD_NAME],
    ["CLOUDINARY_API_KEY", process.env.CLOUDINARY_API_KEY],
    ["CLOUDINARY_API_SECRET", process.env.CLOUDINARY_API_SECRET],
    ["CLOUDINARY_FOLDER", process.env.CLOUDINARY_FOLDER],
  ]
    .filter(([, value]) => !value)
    .map(([name]) => name);
}

function resolveFolder(folder?: string) {
  const baseFolder =
    process.env.CLOUDINARY_FOLDER?.trim() || DEFAULT_CLOUDINARY_FOLDER;
  const normalizedBase = baseFolder.replace(/^\/+|\/+$/g, "");

  if (!folder) return normalizedBase;

  return `${normalizedBase}/${folder.replace(/^\/+|\/+$/g, "")}`;
}

function normalizeResult(result: UploadApiResponse): CloudinaryVideoUploadOk {
  return {
    ok: true,
    secureUrl: result.secure_url,
    publicId: result.public_id,
    bytes: typeof result.bytes === "number" ? result.bytes : null,
    format: typeof result.format === "string" ? result.format : null,
    duration: typeof result.duration === "number" ? result.duration : null,
  };
}

function uploadError(errorMessage: string, errorCode?: string): CloudinaryVideoUploadError {
  return {
    ok: false,
    errorMessage,
    errorCode,
  };
}

export async function uploadVideoToCloudinary(
  filePath: string,
  options: VideoUploadOptions = {}
): Promise<CloudinaryVideoUpload> {
  try {
    const missing = missingCloudinaryConfig();
    if (missing.length > 0) {
      return uploadError(
        `Faltan variables de Cloudinary: ${missing.join(", ")}`,
        "missing_config"
      );
    }

    if (!existsSync(filePath)) {
      return uploadError("El archivo de video no existe.", "file_not_found");
    }

    const fileStat = await stat(filePath);
    if (fileStat.size <= 0) {
      return uploadError("El archivo de video está vacío.", "empty_file");
    }

    const uploadOptions = {
      resource_type: "video" as const,
      folder: resolveFolder(options.folder),
      public_id: options.publicId,
      overwrite: true,
      tags: options.tags,
    };

    const result =
      fileStat.size > LARGE_UPLOAD_THRESHOLD_BYTES
        ? ((await cloudinary.uploader.upload_large(
            filePath,
            uploadOptions
          )) as UploadApiResponse)
        : await cloudinary.uploader.upload(filePath, uploadOptions);

    return normalizeResult(result);
  } catch (error) {
    const details = error as { message?: string; http_code?: number; name?: string };
    return uploadError(
      details.message || "No se pudo subir el video a Cloudinary.",
      details.http_code ? String(details.http_code) : details.name
    );
  }
}

export async function deleteCloudinaryVideo(publicId: string) {
  try {
    await cloudinary.uploader.destroy(publicId, { resource_type: "video" });
  } catch {
    // Best-effort cleanup only.
  }
}
