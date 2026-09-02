/* Flow Animator Bridge — the on-page panel.
 *
 * Teach it two controls once (the prompt box and the Create button), press
 * Connect, then Start. It fills and submits one topic at a time; when the clips
 * are finished, Grab downloads each one under its topic's id and the local
 * bridge keys it and files it.
 *
 * WHY YOU TEACH IT INSTEAD OF IT KNOWING
 * --------------------------------------
 * Flow ships hashed class names that change between deploys, so a selector
 * committed to this file has a shelf life of about a week. Teaching takes ten
 * seconds and survives every redesign that does not move the buttons.
 *
 * WHY DOWNLOADING DOES NOT USE THE ⋮ MENU
 * ---------------------------------------
 * It cannot. The ⋮ renders only on a genuine CSS :hover, and its menu is a
 * portalled Radix overlay somewhere else in the DOM entirely. Flow puts every
 * clip's real URL in the page as
 *     /fx/api/trpc/media.getMediaUrlRedirect?name=<uuid>
 * so Grab reads those and hands them to chrome.downloads, which follows the
 * redirect with your session cookies attached. Thumbnails carry
 * MEDIA_URL_TYPE_THUMBNAIL and are filtered out, or you would download a
 * folder of stills.
 */
(() => {
  if (window.__flowAnimatorLoaded) return;
  window.__flowAnimatorLoaded = true;

  const state = {
    topics: [], i: 0, running: false, build: null,
    sel: { prompt: "", create: "" },
    gapMs: 8000,
  };
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const send = (m) => new Promise((res) => chrome.runtime.sendMessage(m, res));
  const $ = (sel) => { try { return sel ? document.querySelector(sel) : null; } catch { return null; } };

  // ---------------------------------------------------------------- selectors
  function cssPath(el) {
    if (!(el instanceof Element)) return "";
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 6) {
      let s = el.nodeName.toLowerCase();
      if (el.id) { s += `#${CSS.escape(el.id)}`; parts.unshift(s); break; }
      const p = el.parentNode;
      if (p) {
        const sib = [...p.children].filter((c) => c.nodeName === el.nodeName);
        if (sib.length > 1) s += `:nth-of-type(${sib.indexOf(el) + 1})`;
      }
      parts.unshift(s);
      el = el.parentElement;
    }
    return parts.join(" > ");
  }

  const EDITABLE =
    '[data-slate-editor="true"],[contenteditable="true"],[contenteditable=""],' +
    '[data-lexical-editor],.ProseMirror,.ql-editor,textarea,input';

  function findEditable(node) {
    if (!node) return null;
    const root = node.closest &&
      node.closest('[data-slate-editor="true"],[contenteditable="true"],[contenteditable=""]');
    if (root) return root;
    if (node.isContentEditable || node.tagName === "TEXTAREA" || node.tagName === "INPUT") return node;
    return node.querySelector(EDITABLE) || node;
  }

  function selectAll(t) {
    t.focus();
    try {
      if (t.isContentEditable) {
        const r = document.createRange(); r.selectNodeContents(t);
        const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      } else if (t.select) { t.select(); }
    } catch (e) {}
  }

  async function setValue(node, text) {
    const t = findEditable(node);
    if (!t) return false;
    t.focus();
    selectAll(t);
    // The trusted keystroke is the only route Slate accepts. The fallbacks below
    // exist for the day Flow swaps the editor for a plain textarea; they will
    // not rescue a Slate box, so a failure here is reported, not swallowed.
    const r = await send({ type: "cdpInsert", text });
    if (r && r.ok) return true;
    log(`Trusted insert failed (${r && r.error}).\nIs the debugger banner showing? Trying fallbacks…`);
    try { if (document.execCommand("insertText", false, text)) return true; } catch (e) {}
    try {
      t.dispatchEvent(new InputEvent("beforeinput",
        { bubbles: true, cancelable: true, inputType: "insertText", data: text }));
      t.dispatchEvent(new InputEvent("input",
        { bubbles: true, inputType: "insertText", data: text }));
    } catch (e) {}
    return false;
  }

  // A real pointer press at the button's centre. Radix opens on pointerdown, so
  // el.click() silently does nothing for anything that opens a menu or tray;
  // Create is a plain button and works either way, but this costs nothing and
  // removes a whole class of "it submitted nothing and waited fifteen minutes".
  async function trueClick(el) {
    el.scrollIntoView({ block: "center", inline: "center" });
    await sleep(120);
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return false;
    const x = Math.round(r.left + r.width / 2);
    const y = Math.round(r.top + r.height / 2);
    const vis = host.style.display;
    host.style.display = "none";          // never click our own panel
    const res = await send({ type: "cdpMouse", x, y });
    host.style.display = vis;
    if (res && res.ok) return true;
    try { el.click(); return true; } catch (e) { return false; }
  }

  // ---------------------------------------------------------------------- UI
  const host = document.createElement("div");
  host.style.cssText = "position:fixed;z-index:2147483647;top:80px;left:16px;";
  const root = host.attachShadow({ mode: "open" });
  document.documentElement.appendChild(host);
  root.innerHTML = `
    <style>
      .p{font:13px/1.45 system-ui,sans-serif;width:288px;background:#101014;color:#eaeaea;
         border:1px solid #2a2a33;border-radius:10px;padding:12px;box-shadow:0 8px 30px rgba(0,0,0,.5)}
      .p h1{font-size:13px;margin:0 0 10px;letter-spacing:.02em}
      .row{display:flex;gap:6px;margin:6px 0;flex-wrap:wrap;align-items:center}
      button{background:#1d1d24;color:#eaeaea;border:1px solid #33333d;border-radius:6px;
             padding:6px 8px;font-size:12px;cursor:pointer}
      button:hover{background:#26262f}
      button.go{background:#2f6f4f;border-color:#3a8a63}
      button.stop{background:#7a2f2f;border-color:#9a3a3a}
      .tag{font-size:11px;padding:2px 6px;border-radius:4px;background:#22222a}
      .ok{color:#6fd08c}.bad{color:#e08a8a}
      .st{margin-top:8px;font-size:11px;color:#9a9aa5;white-space:pre-wrap;
          max-height:110px;overflow:auto}
      label{font-size:11px;color:#9a9aa5}
      hr{border:0;border-top:1px solid #24242c;margin:10px 0}
      input[type=number]{width:52px;background:#1d1d24;color:#eaeaea;border:1px solid #33333d;
                         border-radius:4px;padding:2px 4px}
    </style>
    <div class="p">
      <h1>🎞 Flow Animator</h1>
      <div class="row">
        <button id="teachP">Teach: prompt box <span id="tP" class="tag bad">✗</span></button>
      </div>
      <div class="row">
        <button id="teachG">Teach: Create button <span id="tG" class="tag bad">✗</span></button>
      </div>
      <hr>
      <div class="row">
        <button id="connect">Connect bridge <span id="tC" class="tag bad">✗</span></button>
        <span id="who" class="tag">no job</span>
      </div>
      <div class="row">
        <label><input type="checkbox" id="auto" checked> submit automatically</label>
        <label>gap <input type="number" id="gap" value="8" min="2" max="120">s</label>
      </div>
      <div class="row">
        <button id="start" class="go">▶ Start</button>
        <button id="next">Next ⏭</button>
        <button id="stop" class="stop">■ Stop</button>
      </div>
      <hr>
      <div class="row">
        <button id="grab" class="go">⬇ Grab finished clips</button>
        <label><input type="checkbox" id="rev" checked> newest first</label>
      </div>
      <div class="row">
        <label><input type="checkbox" id="arm"> name downloads after topics
          <span id="ctr" class="tag">0</span></label>
        <button id="reset">reset #</button>
      </div>
      <div class="st" id="log">Load a job with Connect.</div>
    </div>`;

  const el = (id) => root.getElementById(id);
  const log = (m) => { el("log").textContent = m; console.log("[flow-animator]", m); };
  const mark = (id, ok) => {
    const t = el(id); t.textContent = ok ? "✓" : "✗";
    t.className = "tag " + (ok ? "ok" : "bad");
  };

  (() => {                                   // drag by the title bar
    const bar = root.querySelector(".p h1");
    bar.style.cursor = "move"; bar.title = "drag me";
    let drag = false, ox = 0, oy = 0;
    bar.addEventListener("mousedown", (e) => {
      const r = host.getBoundingClientRect();
      drag = true; ox = e.clientX - r.left; oy = e.clientY - r.top;
      host.style.left = r.left + "px"; host.style.top = r.top + "px";
      e.preventDefault();
    });
    window.addEventListener("mousemove", (e) => {
      if (!drag) return;
      host.style.left = Math.max(0, e.clientX - ox) + "px";
      host.style.top = Math.max(0, e.clientY - oy) + "px";
    });
    window.addEventListener("mouseup", () => { drag = false; });
  })();

  chrome.storage.local.get(["sel", "armed", "counter"], (st) => {
    if (st.sel) {
      state.sel = Object.assign(state.sel, st.sel);
      mark("tP", !!state.sel.prompt); mark("tG", !!state.sel.create);
    }
    if (st.armed) el("arm").checked = true;
    el("ctr").textContent = String(st.counter || 0);
  });

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg && msg.type === "renamed") {
      el("ctr").textContent = String(msg.index);
      log(`Downloaded → ${msg.id}.mp4 — the bridge keys it as it lands.`);
    }
  });

  // ------------------------------------------------------------------- teach
  function teach(kind, tagId, label) {
    log(`Teach ${label}: click it in Flow. (The panel is click-through until you do.)`);
    host.style.pointerEvents = "none";
    const onClick = (e) => {
      e.preventDefault(); e.stopPropagation();
      let path;
      if (kind === "prompt") {
        const ed = findEditable(e.target);
        // Slate re-renders constantly and hashed classes churn; the editor
        // attribute is the one handle that survives a deploy.
        path = ed && ed.matches && ed.matches('[data-slate-editor="true"]')
          ? '[data-slate-editor="true"]' : cssPath(ed || e.target);
      } else {
        // Climb to the button — Flow's Create is an icon inside one, and a
        // selector for the <svg> matches something with no click handler.
        const btn = e.target.closest && e.target.closest('button,[role="button"]');
        path = cssPath(btn || e.target);
      }
      state.sel[kind] = path;
      chrome.storage.local.set({ sel: state.sel });
      mark(tagId, true);
      log(`${label} taught:\n${path}`);
      host.style.pointerEvents = "auto";
      document.removeEventListener("click", onClick, true);
    };
    document.addEventListener("click", onClick, true);
  }
  el("teachP").onclick = () => teach("prompt", "tP", "the prompt box");
  el("teachG").onclick = () => teach("create", "tG", "the Create button");

  // ----------------------------------------------------------------- connect
  el("connect").onclick = async () => {
    const [mine, resp] = await Promise.all([
      send({ type: "build" }),
      send({ type: "bridgeGet", path: "/prompts" }),
    ]);
    if (!resp || !resp.ok || !resp.data) {
      mark("tC", false);
      log(`Could not reach the bridge: ${resp ? resp.error : "no answer from the worker"}
Is it running?   ./run.sh
On Brave, this also looks exactly like the Local Network Access block —
see docs/BROWSER-SETUP.md.`);
      return;
    }
    const job = resp.data;
    if (mine && job.build !== mine.build) {
      mark("tC", false);
      log(`Build mismatch: this extension is ${mine.build}, the bridge expects ${job.build}.
Reload the extension at chrome://extensions, then hard-reload this tab.
A stale extension fails like a Flow redesign — wrong element, no error.`);
      return;
    }
    state.topics = job.topics || [];
    state.i = 0;
    state.build = job.build;
    state.inbox = job.inbox_name || "flow_inbox";
    await send({
      type: "setJob",
      ids: state.topics.map((t) => t.id),
      inbox: job.inbox_name || "flow_inbox",
    });
    el("ctr").textContent = "0";
    el("who").textContent = `${state.topics.length} topics`;
    mark("tC", true);
    const fields = state.topics.reduce((a, t) => (a[t.field] = (a[t.field] || 0) + 1, a), {});
    log(`Connected: ${state.topics.length} topics `
      + `(${Object.entries(fields).map(([k, v]) => `${v} on ${k}`).join(", ")}).
Numbering reset. Set Flow to the right aspect ratio first — the brief asks for `
      + `${(state.topics[0] || {}).aspect || "9:16"}.`);
  };

  const post = (body) =>
    chrome.runtime.sendMessage({ type: "bridgePost", path: "/status", body }).catch(() => {});

  // --------------------------------------------------------------------- run
  async function runLoop() {
    if (!state.topics.length) { log("Connect the bridge first."); return; }
    if (!state.sel.prompt) { log("Teach the prompt box first."); return; }
    state.running = true;
    const auto = el("auto").checked;
    state.gapMs = Math.max(2, parseInt(el("gap").value || "8", 10)) * 1000;

    for (; state.i < state.topics.length && state.running; state.i++) {
      const t = state.topics[state.i];
      const box = $(state.sel.prompt);
      if (!box) { log("Prompt box not found — re-teach it."); break; }

      const ok = await setValue(box, t.text);
      if (!ok) { log(`Could not fill the prompt for ${t.id}. Stopping rather than submitting an empty box.`); break; }
      log(`${t.index}/${state.topics.length}  ${t.id} filled  (${t.field} field)`);
      post({ topic: t.id, state: "filled" });
      await sleep(700);

      if (!auto) {
        log(`${t.id} is in the box. Press Create yourself, then hit Next.`);
        state.i++;
        state.running = false;
        return;
      }
      const btn = $(state.sel.create);
      if (!btn) { log("Create button not found — re-teach it."); break; }
      if (!(await trueClick(btn))) { log("Create would not click — re-teach it."); break; }
      post({ topic: t.id, state: "submitted" });
      log(`${t.index}/${state.topics.length}  ${t.id} submitted. Next in ${state.gapMs / 1000}s…`);
      await sleep(state.gapMs);
    }
    if (state.i >= state.topics.length) {
      log(`All ${state.topics.length} submitted. Flow takes a few minutes each.
When every clip has a thumbnail: tick "name downloads after topics", then Grab.`);
    }
    state.running = false;
  }
  el("start").onclick = () => runLoop();
  el("next").onclick = () => { if (!state.running) runLoop(); };
  el("stop").onclick = () => {
    state.running = false;
    send({ type: "cdpDetach" });
    log("Stopped. The debugger is detached; press Start to resume where it left off.");
  };

  // -------------------------------------------------------------------- grab
  function videoUrls() {
    const attrs = ["src", "poster", "href", "data-src"];
    const seen = new Set(), out = [];
    for (const e of document.querySelectorAll("*")) {
      for (const a of attrs) {
        const v = e.getAttribute && e.getAttribute(a);
        if (v && v.includes("getMediaUrlRedirect") && !v.includes("MEDIA_URL_TYPE_THUMBNAIL")) {
          const m = v.match(/name=([0-9a-fA-F-]{8,})/);
          const k = m ? m[1] : v;
          if (!seen.has(k)) { seen.add(k); out.push(v); }
        }
      }
    }
    return out;
  }

  el("grab").onclick = async () => {
    const all = videoUrls();
    if (!all.length) {
      log(`No clip URLs on the page.
Scroll the results so every finished clip has rendered, then try again —
Flow only puts a clip's URL in the DOM once its card is on screen.`);
      return;
    }
    let urls = all.slice();
    if (el("rev").checked) urls.reverse();      // newest-first in the DOM → topic order
    const n = state.topics.length || urls.length;
    if (all.length < n) {
      log(`Only ${all.length} of ${n} clips are on the page. Scroll down so the rest render, `
        + `or Grab now and Grab again for the remainder.`);
    }
    urls = urls.slice(0, n);
    state.running = true;
    let ok = 0;
    for (let k = 0; k < urls.length && state.running; k++) {
      const t = state.topics[k];
      const id = t ? t.id : `clip_${String(k + 1).padStart(2, "0")}`;
      const full = urls[k].startsWith("http") ? urls[k] : location.origin + urls[k];
      const r = await send({
        type: "downloadAs", url: full,
        filename: `${state.inbox || "flow_inbox"}/${id}.mp4`,
      });
      if (r && r.ok) { ok++; el("ctr").textContent = String(k + 1); }
      log(`${k + 1}/${urls.length}  ${id}  ${r && r.ok ? "↓" : "FAILED " + ((r && r.error) || "")}`);
      await sleep(700);
    }
    state.running = false;
    log(`Grabbed ${ok}/${urls.length}. Watch the bridge terminal — it keys each clip `
      + `as it lands and tells you if one came back with a hole in it.`);
  };

  el("arm").onchange = () => {
    send({ type: "arm", on: el("arm").checked });
    log(el("arm").checked
      ? `Downloads will be named after topics, in order. Only needed if you download
from Flow's own ⋮ menu — Grab names them itself.`
      : "Download naming off.");
  };
  el("reset").onclick = () => {
    send({ type: "resetCounter" });
    el("ctr").textContent = "0";
    log("Numbering reset to 0.");
  };

  log(`Ready.
1. Teach the prompt box and the Create button (once per browser profile).
2. Connect, then Start.
3. When the clips are done, Grab.`);
})();
