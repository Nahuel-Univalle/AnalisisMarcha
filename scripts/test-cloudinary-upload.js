/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require("node:fs");
const path = require("node:path");
const { v2: cloudinary } = require("cloudinary");

const projectRoot = path.resolve(__dirname, "..");

function loadEnvFile(fileName) {
  const filePath = path.join(projectRoot, fileName);
  if (!fs.existsSync(filePath)) return;

  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;

    const index = trimmed.indexOf("=");
    const key = trimmed.slice(0, index).trim();
    const value = trimmed
      .slice(index + 1)
      .trim()
      .replace(/^["']|["']$/g, "");

    if (!process.env[key]) process.env[key] = value;
  }
}

function normalizeInputPath(inputPath) {
  if (!inputPath) return null;
  return path.isAbsolute(inputPath)
    ? inputPath
    : path.join(projectRoot, inputPath);
}

loadEnvFile(".env.local");
loadEnvFile(".env");

const missing = [
  "CLOUDINARY_CLOUD_NAME",
  "CLOUDINARY_API_KEY",
  "CLOUDINARY_API_SECRET",
  "CLOUDINARY_FOLDER",
].filter((name) => !process.env[name]);

if (missing.length > 0) {
  console.error(`Faltan variables de Cloudinary: ${missing.join(", ")}`);
  process.exit(1);
}

const videoPath = normalizeInputPath(process.argv[2]);
if (!videoPath) {
  console.error("Uso: node scripts/test-cloudinary-upload.js videos/prueba.mp4");
  process.exit(1);
}

if (!fs.existsSync(videoPath)) {
  console.error(`No existe el archivo: ${videoPath}`);
  process.exit(1);
}

const stat = fs.statSync(videoPath);
if (stat.size <= 0) {
  console.error("El archivo existe, pero está vacío.");
  process.exit(1);
}

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
  secure: true,
});

const publicId = `test-${Date.now()}-${path.parse(videoPath).name}`
  .replace(/[^a-zA-Z0-9_-]+/g, "-")
  .slice(0, 100);

cloudinary.uploader
  .upload(videoPath, {
    resource_type: "video",
    folder: `${process.env.CLOUDINARY_FOLDER.replace(/\/+$/g, "")}/tests`,
    public_id: publicId,
    overwrite: true,
    tags: ["analisis-marcha", "test"],
  })
  .then((result) => {
    console.log("Cloudinary upload OK.");
    console.log(`secure_url: ${result.secure_url}`);
    console.log(`public_id: ${result.public_id}`);
  })
  .catch((error) => {
    console.error("Cloudinary upload falló.");
    console.error(error?.message || String(error));
    process.exit(1);
  });
