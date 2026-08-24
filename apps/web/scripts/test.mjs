import { spawnSync } from "node:child_process";

const args = process.argv.slice(2).filter((arg) => arg !== "--runInBand");
const result = spawnSync("vitest", ["run", ...args], {
  shell: process.platform === "win32",
  stdio: "inherit"
});

process.exit(result.status ?? 1);
