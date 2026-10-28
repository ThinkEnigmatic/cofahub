#!/usr/bin/env node
// Screenshot the active real-Chrome page via CDP Page.captureScreenshot.
import fs from "fs";
async function getWs() {
  const list = await (await fetch("http://127.0.0.1:9223/json/list")).json();
  const tab = list.find((t) => t.type === "page" && t.url.startsWith("http")) || list.find((t) => t.type === "page");
  return tab.webSocketDebuggerUrl;
}
const ws = new WebSocket(await getWs());
let id = 0;
const pending = new Map();
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); }
};
await new Promise((res) => (ws.onopen = res));
function send(method, params = {}) {
  return new Promise((res) => { const mid = ++id; pending.set(mid, res); ws.send(JSON.stringify({ id: mid, method, params })); });
}
const r = await send("Page.captureScreenshot", { format: "png" });
fs.writeFileSync("/tmp/chrome_form.png", Buffer.from(r.data, "base64"));
console.log("saved /tmp/chrome_form.png");
ws.close();
