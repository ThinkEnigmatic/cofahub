#!/usr/bin/env node
// Drive a real Chrome (already launched with --remote-debugging-port=9223) via CDP.
// Usage: node cdp.mjs <command> [args...]
// Commands:
//   open <url>            — create/open a page at <url>
//   eval <js>             — evaluate JS in the active page, print JSON result
//   snapshot              — print the page title + URL + body text
//   click <selector>      — click the first matching element (CSS or text via JS)
//   type <selector> <txt> — set value of first matching input/textarea
//   wait <ms>             — sleep

const CDP = "http://127.0.0.1:9223";

async function getWs(pageId) {
  if (pageId) {
    return `ws://127.0.0.1:9223/devtools/page/${pageId}`;
  }
  const list = await (await fetch(`${CDP}/json/list`)).json();
  // prefer a normal page tab (http/https), else the first page
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
    ws.onopen = () => resolve({
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
    ws.onerror = (e) => reject(new Error("ws error"));
    ws.onclose = () => {};
  });
}

async function main() {
  const [cmd, ...args] = process.argv.slice(2);
  const c = await connect(await getWs());
  try {
    if (cmd === "open") {
      await c.send("Page.navigate", { url: args[0] });
      await new Promise((r) => setTimeout(r, 3000));
      console.log("navigated:", args[0]);
    } else if (cmd === "eval") {
      const r = await c.send("Runtime.evaluate", {
        expression: args[0],
        returnByValue: true,
        awaitPromise: true,
      });
      console.log(JSON.stringify(r.result?.value ?? r.result));
    } else if (cmd === "snapshot") {
      const r = await c.send("Runtime.evaluate", {
        expression: `JSON.stringify({title:document.title,url:location.href,body:document.body.innerText.slice(0,3000)})`,
        returnByValue: true,
      });
      console.log(JSON.parse(r.result.value));
    } else if (cmd === "click") {
      await c.send("Runtime.evaluate", {
        expression: `(()=>{const el=[...document.querySelectorAll('${args[0]}')][0];if(!el)return 'NO_MATCH';el.click();return 'clicked'})()`,
        returnByValue: true,
      });
    } else if (cmd === "type") {
      // Focus + clear, then send real key events via CDP Input domain (works
      // with React-controlled inputs).
      await c.send("Runtime.evaluate", {
        expression: `(()=>{const el=[...document.querySelectorAll('${args[0]}')][0];if(!el)return 'NO_MATCH';el.focus();el.select();return 'focused'})()`,
        returnByValue: true,
      });
      await c.send("Input.dispatchKeyEvent", { type: "keyDown", key: "a", code: "KeyA", modifiers: 4 });
      await c.send("Input.dispatchKeyEvent", { type: "keyUp", key: "a", code: "KeyA", modifiers: 4 });
      await c.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Backspace", code: "Backspace" });
      await c.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Backspace", code: "Backspace" });
      await c.send("Input.insertText", { text: args[1] });
      console.log("typed:", args[1]);
    } else if (cmd === "wait") {
      await new Promise((r) => setTimeout(r, parseInt(args[0] || "1000", 10)));
    }
  } finally {
    c.ws.close();
  }
}

main().catch((e) => {
  console.error("ERR:", e.message);
  process.exit(1);
});
