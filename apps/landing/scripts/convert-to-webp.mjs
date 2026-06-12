// Convert all raster images in public/images/ to .webp
// Usage:
//   node scripts/convert-to-webp.mjs            -> convert, keep originals
//   node scripts/convert-to-webp.mjs --delete   -> convert and delete originals
//   node scripts/convert-to-webp.mjs --rewrite  -> also rewrite src/** references from .jpg/.png/.tiff to .webp

import { readdir, stat, unlink, readFile, writeFile } from "node:fs/promises";
import { join, extname, basename } from "node:path";
import sharp from "sharp";

const ROOT = process.cwd();
const IMG_DIR = join(ROOT, "public", "images");
const SRC_DIR = join(ROOT, "src");
const QUALITY = 82;
const MAX_WIDTH = 2000;
const EXTS = new Set([".jpg", ".jpeg", ".png", ".tif", ".tiff"]);

const args = new Set(process.argv.slice(2));
const SHOULD_DELETE = args.has("--delete");
const SHOULD_REWRITE = args.has("--rewrite");

async function convertAll() {
  const files = await readdir(IMG_DIR);
  const targets = files.filter((f) => EXTS.has(extname(f).toLowerCase()));

  console.log(`Found ${targets.length} image(s) to convert in ${IMG_DIR}`);

  let converted = 0;
  let skipped = 0;
  let totalSavedKB = 0;

  for (const file of targets) {
    const inPath = join(IMG_DIR, file);
    const outPath = join(IMG_DIR, basename(file, extname(file)) + ".webp");

    try {
      const exists = await stat(outPath).then(() => true).catch(() => false);
      if (exists) {
        console.log(`  skip  ${file} (already has .webp)`);
        skipped++;
        continue;
      }

      const inSize = (await stat(inPath)).size;
      await sharp(inPath)
        .rotate()
        .resize({ width: MAX_WIDTH, withoutEnlargement: true })
        .webp({ quality: QUALITY, effort: 5 })
        .toFile(outPath);

      const outSize = (await stat(outPath)).size;
      const savedKB = Math.round((inSize - outSize) / 1024);
      totalSavedKB += savedKB;
      console.log(
        `  ok    ${file} -> .webp  (${Math.round(inSize / 1024)}KB -> ${Math.round(outSize / 1024)}KB, saved ${savedKB}KB)`
      );

      if (SHOULD_DELETE) {
        await unlink(inPath);
        console.log(`        deleted original`);
      }

      converted++;
    } catch (err) {
      console.error(`  fail  ${file}: ${err.message}`);
    }
  }

  console.log(
    `\nDone. Converted: ${converted}, skipped: ${skipped}, total saved: ~${totalSavedKB}KB`
  );

  if (SHOULD_REWRITE) {
    await rewriteReferences();
  } else if (converted > 0) {
    console.log(
      `\nTip: run with --rewrite to update src/** references from .jpg/.png to .webp`
    );
  }
}

async function rewriteReferences() {
  console.log(`\nRewriting references in ${SRC_DIR} ...`);
  const files = await walk(SRC_DIR);
  const codeExts = new Set([".astro", ".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte", ".md", ".mdx", ".css"]);
  const code = files.filter((f) => codeExts.has(extname(f).toLowerCase()));

  let changed = 0;
  for (const file of code) {
    const original = await readFile(file, "utf8");
    const updated = original.replace(
      /(\/images\/[A-Za-z0-9._\-]+)\.(jpg|jpeg|png|tif|tiff)\b/g,
      "$1.webp"
    );
    if (updated !== original) {
      await writeFile(file, updated, "utf8");
      console.log(`  updated  ${file.replace(ROOT, "")}`);
      changed++;
    }
  }
  console.log(`Done. Rewrote ${changed} file(s).`);
}

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const out = [];
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await walk(full)));
    else out.push(full);
  }
  return out;
}

convertAll().catch((err) => {
  console.error(err);
  process.exit(1);
});
