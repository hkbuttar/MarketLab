import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { chromium } from "playwright";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDirectory, "../..");
const outputDirectory = path.join(projectRoot, "docs/assets/screenshots");
const baseUrl = process.env.MARKETLAB_SCREENSHOT_URL ?? "http://[::1]:3000";
const pages = [
  ["dashboard", "/"],
  ["factor-lab", "/factors"],
  ["ml-lab", "/models"],
];

await mkdir(outputDirectory, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
  });
  for (const [name, pathname] of pages) {
    const response = await page.goto(`${baseUrl}${pathname}`, {
      waitUntil: "networkidle",
    });
    if (!response?.ok()) {
      throw new Error(`${pathname} returned HTTP ${response?.status() ?? "unknown"}`);
    }
    await page.screenshot({
      path: path.join(outputDirectory, `${name}.png`),
      fullPage: true,
    });
    console.log(`Captured ${name}.png`);
  }
} finally {
  await browser.close();
}
