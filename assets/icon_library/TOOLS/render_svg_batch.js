#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

async function main() {
  const [manifestPath, rootPath, outputPath, sizeArg] = process.argv.slice(2);
  if (!manifestPath || !rootPath || !outputPath) throw new Error("usage: render_svg_batch.js manifest root output [size]");
  const size = Number(sizeArg || 72);
  const records = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  fs.mkdirSync(outputPath, { recursive: true });
  for (const record of records) {
    const source = path.join(rootPath, ...record.relative_path.split("/"));
    const target = path.join(outputPath, `${record.id}.png`);
    let svg = fs.readFileSync(source, "utf8").replaceAll("currentColor", "#263746");
    await sharp(Buffer.from(svg)).resize(size, size, { fit: "contain" }).png().toFile(target);
  }
  process.stdout.write(JSON.stringify({ rendered: records.length, size }));
}

main().catch(err => { console.error(err.stack || err); process.exit(1); });
