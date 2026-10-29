#!/usr/bin/env node
// Download a URL through the running Chrome (port 9223) session, so Cloudflare
// cookies carry over. Writes the raw bytes to a local file.
// Usage: node cdp_download.mjs <url> <outfile>
import fs from "node:fs";

const CDP = "http://127.0.0.1:9223";

async function getWs() {
  const list = await (await fetch(`${CDP}/json/list`)).json();
  const pages = list.filter((t) => t.type === "page");
  const tab = pages.find((t) => t.url.startsWith("http")) || pages[0];
  if (!tab) throw new Error("no page target");
  return tab.webSocketDebuggerUrl;
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let id = 0;
    const pending = new Map();
    ws.onopen = () =>
      resolve({
        ws,
        send(method, params = {}) {
          return new Promise((res, rej) => {
            const mid = ++id;
            pending.set(mid, { res, rej });
            ws.send(JSON.stringify({ id: mid, method, params }));
          });
        },
      });
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        const p = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) p.rej(new Error(JSON.stringify(msg.error)));
        else p.res(msg.result);
      }
    };
    ws.onerror = () => reject(new Error("ws error"));
  });
}

async function main() {
  const [url, outfile] = process.argv.slice(2);
  if (!url || !outfile) {
    console.error("usage: node cdp_download.mjs <url> <outfile>");
    process.exit(1);
  }
  const c = await connect(await getWs());
  try {
    // Fetch in-page (carries cookies) and return base64 of the response body.
    const r = await c.send("Runtime.evaluate", {
      expression: `fetch(${JSON.stringify(url)}).then(async r => {
        if (!r.ok) return { status: r.status, ok: false };
        const buf = await r.arrayBuffer();
        let binary = '';
        const bytes = new Uint8Array(buf);
        for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
        return { status: r.status, ok: true, base64: btoa(binary), size: bytes.length };
      })`,
      returnByValue: true,
      awaitPromise: true,
    });
    const v = r.result?.value;
    if (!v || !v.ok) {
      console.error("download failed:", v?.status ?? "no result");
      process.exit(1);
    }
    fs.writeFileSync(outfile, Buffer.from(v.base64, "base64"));
    console.log(`wrote ${outfile} (${v.size} bytes)`);
  } finally {
    c.ws.close();
  }
}

main().catch((e) => {
  console.error("ERR:", e.message);
  process.exit(1);
});
