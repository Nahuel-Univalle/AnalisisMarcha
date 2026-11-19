import type { NextConfig } from "next";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const appRoot = dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  outputFileTracingExcludes: {
    "/*": [
      "./private-videos/**/*",
      "./tmp/reports/**/*",
      "./public/uploads-temp/**/*",
      "./public/processed-videos/**/*",
    ],
  },
  turbopack: {
    root: appRoot,
  },
};

export default nextConfig;
