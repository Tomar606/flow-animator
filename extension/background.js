/* Flow Animator Bridge — service worker.
 *
 * Everything that needs a privilege the page does not have happens here:
 * the debugger protocol, downloads, and the fetches to the local bridge.
 *
 * TWO THINGS THIS FILE EXISTS FOR, both learned the hard way:
 *
 * 1. Flow's prompt box is a Slate editor and it rejects synthetic input.
 *    Setting `.value`, dispatching `input`, firing `beforeinput` — the text
 *    appears and the Create button stays disabled, because Slate keeps its own
 *    document model and only trusts events that came from the browser itself.
 *    The way in is `Input.insertText` over the Chrome debugger protocol, which
 *    is why this extension asks for the `debugger` permission and why Chrome
 *    shows a "started debugging this browser" banner while a run is going.
 *    The banner is expected. Do not click Cancel on it — that detaches us.
 *
 * 2. Flow is a Radix app, and Radix menus, dialogs and trays open on
 *    `pointerdown`, not on `click`. A synthetic `el.click()` reaches React's
 *    onClick handler and does nothing at all: `aria-expanded` stays "false" and
 *    nothing is logged. So anything that opens something goes through
 *    `Input.dispatchMouseEvent` too. Plain buttons work either way, which is
 *    exactly why this took so long to find.
 */

const BRIDGE_BUILD = 1;              // must match EXPECTED_BUILD in src/flowanim/serve.py
const BRIDGE = "http://127.0.0.1:8765";

// ---------------------------------------------------------------- downloads
// Chrome names a download itself unless someone intervenes here. When the panel
// has "name downloads after topics" ticked, each finished video is renamed to
// the next topic id in the served order, inside the bridge's inbox folder.
chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
  chrome.storage.local.get(["armed", "counter", "ids", "inbox"], (st) => {
    const inbox = st.inbox || "flow_inbox";
    const isVideo =
      (item.mime && item.mime.startsWith("video")) ||
      /\.(mp4|webm|mov|m4v)$/i.test(item.filename || "");
    const alreadyOurs = new RegExp("^" + inbox + "/").test(item.filename || "");
    if (st.armed && isVideo && !alreadyOurs) {
      const ids = st.ids || [];
      const n = st.counter || 0;
      const id = ids[n] || `clip_${String(n + 1).padStart(2, "0")}`;
      chrome.storage.local.set({ counter: n + 1 });
      suggest({ filename: `${inbox}/${id}.mp4`, conflictAction: "overwrite" });
      chrome.runtime.sendMessage({ type: "renamed", index: n + 1, id }).catch(() => {});
    } else {
      suggest();
    }
  });
  return true;                        // suggest() is called asynchronously
});

// Clicking the toolbar icon force-injects the panel, for the case where the
// content script did not run because the tab predates the extension.
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;
  try {
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
  } catch (e) {
    console.warn("[flow-animator] inject failed:", e);
  }
});

// ------------------------------------------------------------------ debugger
let dbgTab = null;

async function ensureAttached(tabId) {
  if (dbgTab === tabId) return;
  if (dbgTab != null) {
    try { await chrome.debugger.detach({ tabId: dbgTab }); } catch (e) {}
    dbgTab = null;
  }
  await chrome.debugger.attach({ tabId }, "1.3");
  dbgTab = tabId;
}
chrome.tabs.onRemoved.addListener((id) => { if (dbgTab === id) dbgTab = null; });
chrome.debugger.onDetach.addListener((src) => { if (src.tabId === dbgTab) dbgTab = null; });

const cmd = (tabId, method, params) =>
  chrome.debugger.sendCommand({ tabId }, method, params);

// ------------------------------------------------------------------ messages
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg) return;
  const tabId = sender.tab && sender.tab.id;

  if (msg.type === "build") { sendResponse({ ok: true, build: BRIDGE_BUILD }); return true; }

  if (msg.type === "arm") {
    chrome.storage.local.set({ armed: !!msg.on }, () => sendResponse({ ok: true }));
    return true;
  }

  if (msg.type === "setJob") {
    // A fresh Connect resets the numbering. Forgetting this is how a second run
    // overwrites the first run's clips with the wrong topic ids.
    chrome.storage.local.set(
      { ids: msg.ids || [], inbox: msg.inbox || "flow_inbox", counter: 0 },
      () => sendResponse({ ok: true }));
    return true;
  }

  if (msg.type === "resetCounter") {
    chrome.storage.local.set({ counter: 0 }, () => sendResponse({ ok: true }));
    return true;
  }

  if (msg.type === "cdpInsert") {
    (async () => {
      try {
        await ensureAttached(tabId);
        // Select-all first, so this replaces the previous topic's prompt rather
        // than appending to it. Both events must be trusted or Slate ignores them.
        for (const type of ["keyDown", "keyUp"]) {
          await cmd(tabId, "Input.dispatchKeyEvent",
            { type, modifiers: 4, key: "a", code: "KeyA", windowsVirtualKeyCode: 65 });
        }
        await cmd(tabId, "Input.insertText", { text: msg.text });
        sendResponse({ ok: true });
      } catch (e) {
        sendResponse({ ok: false, error: String((e && e.message) || e) });
      }
    })();
    return true;
  }

  if (msg.type === "cdpMouse") {
    (async () => {
      try {
        await ensureAttached(tabId);
        const { x, y } = msg;
        await cmd(tabId, "Input.dispatchMouseEvent", { type: "mouseMoved", x, y, buttons: 0 });
        await cmd(tabId, "Input.dispatchMouseEvent",
          { type: "mousePressed", x, y, button: "left", buttons: 1, clickCount: 1 });
        await cmd(tabId, "Input.dispatchMouseEvent",
          { type: "mouseReleased", x, y, button: "left", buttons: 0, clickCount: 1 });
        sendResponse({ ok: true });
      } catch (e) {
        sendResponse({ ok: false, error: String((e && e.message) || e) });
      }
    })();
    return true;
  }

  if (msg.type === "cdpDetach") {
    (async () => {
      if (dbgTab != null) {
        try { await chrome.debugger.detach({ tabId: dbgTab }); } catch (e) {}
        dbgTab = null;
      }
      sendResponse({ ok: true });
    })();
    return true;
  }

  if (msg.type === "downloadAs") {
    chrome.downloads.download(
      { url: msg.url, filename: msg.filename, conflictAction: "overwrite" },
      (id) => sendResponse({
        ok: id != null, id,
        error: chrome.runtime.lastError && chrome.runtime.lastError.message,
      }));
    return true;
  }

  // The bridge is reached from here, not from the page: the service worker is
  // not subject to the Flow tab's CSP or its mixed-content rules.
  if (msg.type === "bridgeGet") {
    fetch(msg.url || BRIDGE + msg.path)
      .then((r) => r.json())
      .then((data) => sendResponse({ ok: true, data }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true;
  }

  if (msg.type === "bridgePost") {
    fetch(msg.url || BRIDGE + msg.path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ build: BRIDGE_BUILD, ...(msg.body || {}) }),
    })
      .then(() => sendResponse({ ok: true }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true;
  }
});
