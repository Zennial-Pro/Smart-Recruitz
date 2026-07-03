#!/usr/bin/env node
// Picks the first free port from a preferred range and spawns `next dev` on it.
// No external dependencies — uses Node's built-in `net` module.

import net from "node:net";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

const PREFERRED = Number(process.env.PORT) || 3000;
const MAX_TRIES = 10;

function isPortFree(port) {
  return new Promise((resolve) => {
    const tester = net.createServer()
      .once("error", () => resolve(false))
      .once("listening", () => tester.close(() => resolve(true)))
      .listen(port, "0.0.0.0");
  });
}

async function findFreePort(start, max) {
  for (let i = 0; i < max; i++) {
    const port = start + i;
    // eslint-disable-next-line no-await-in-loop
    if (await isPortFree(port)) return port;
  }
  throw new Error(`No free port found in range ${start}-${start + max - 1}`);
}

const port = await findFreePort(PREFERRED, MAX_TRIES);
if (port !== PREFERRED) {
  console.log(`Port ${PREFERRED} is busy — using port ${port} instead.`);
}

// This is a pnpm project — launch the LOCAL Next binary directly. Going through
// `npx next` breaks module resolution in pnpm's symlinked node_modules, which
// makes Turbopack panic ("Next.js package not found") in a crash-reload loop.
const localNext = path.resolve("node_modules/.bin/next");
const bin = existsSync(localNext) ? localNext : "next";
// Use webpack, not Turbopack: Turbopack can't resolve `next` through pnpm's
// symlinked node_modules and panics ("Next.js package not found") in a
// crash-reload loop. Webpack is slower to compile but stable here.
const args = ["dev", "--webpack", "--port", String(port), ...process.argv.slice(2)];
const child = spawn(bin, args, { stdio: "inherit", env: process.env });
child.on("exit", (code) => process.exit(code ?? 0));
