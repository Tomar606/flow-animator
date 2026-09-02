# Browser setup

The extension drives the browser you are already signed into. That is the whole
point: Google Flow is covered by a Google AI subscription but is **UI-only** —
those credits do not apply to the API, and the API bills separately. Rather than
pay twice, this drives the real logged-in session.

Chrome and Brave both work. Brave needs one extra step, and without it the bridge
fails **silently** — see the last section.

---

## 1. Load the extension

1. Open `chrome://extensions` (Brave: `brave://extensions`).
2. Turn on **Developer mode**, top right.
3. **Load unpacked**, and pick this repo's `extension/` folder.
4. Note the **ID** shown under the extension's name. You need it for Brave.

> **The extension's ID comes from where the folder lives.** An unpacked extension
> with no `key` in its manifest is identified by its path, so moving or renaming
> this repo changes the ID — and any policy that referenced the old one silently
> stops matching. If you move the repo, redo step 4 and the Brave section.

**There is no hot reload.** After editing anything in `extension/`, reload the
extension on that page *and* hard-reload the Flow tab. A stale extension fails
exactly like a Flow redesign — wrong element, no error, nothing in the log. The
build handshake exists to catch this: if the panel says *build mismatch*, that is
what happened.

---

## 2. Downloads

The extension writes clips into a subfolder of your browser's download directory,
and the bridge watches that folder. They must agree.

- Settings → Downloads → **turn OFF "Ask where to save each file"**. If the
  browser opens a save dialog per clip, nothing lands where the bridge is looking.
- The default location must match `"inbox"` in `config.json`. `setup.sh` writes
  it as `~/Downloads/flow_inbox`; change it there if your browser saves elsewhere.

Chrome appends ` (1)` to a filename that is already taken and an extension cannot
prevent it. The bridge strips that suffix, so a re-download of one topic still
resolves to the right topic.

---

## 3. The debugging banner is expected

While a run is going, Chrome shows **"… is debugging this browser"**. Do not
dismiss it — clicking Cancel detaches the debugger and the next prompt will not
fill.

It is there because Flow's prompt box is a **Slate editor, and it rejects
synthetic input**. Setting `.value`, dispatching `input`, firing `beforeinput` —
the text appears on screen and the Create button stays disabled, because Slate
keeps its own document model and only trusts events that came from the browser
itself. The only way in is `Input.insertText` over the Chrome debugger protocol,
which is why the extension requests the `debugger` permission.

The same applies to clicking. Flow is a **Radix** app, and Radix menus, dialogs
and trays open on `pointerdown`, not on `click` — a synthetic `el.click()`
reaches React's handler and does nothing at all, with `aria-expanded` still
`"false"` and nothing logged. Anything that opens something goes through a real
dispatched mouse event.

---

## 4. Brave: the permission that makes it look broken

**Chromium's Local Network Access check blocks the bridge, and it is silent.**
Requests to loopback are gated behind a permission, and workers are in scope — so
the extension's service worker is caught by it.

The failure has no error anywhere. The TCP connection to `127.0.0.1:8765` is
ESTABLISHED and the HTTP request is simply never delivered. From the bridge it
looks exactly like an extension that was never loaded. In the tab it looks like a
permission prompt that does nothing when you answer it, because a service worker
has no tab for a prompt to attach to.

The fix is a policy allowlist rather than turning the feature off. On macOS,
create `/Library/Managed Preferences/com.brave.Browser.plist`, root-owned:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>LocalNetworkAccessAllowedForUrls</key>
  <array>
    <string>chrome-extension://YOUR_EXTENSION_ID</string>
    <string>http://127.0.0.1:8765</string>
    <string>http://localhost:8765</string>
  </array>
</dict>
</plist>
```

```bash
sudo chown root:wheel "/Library/Managed Preferences/com.brave.Browser.plist"
sudo chmod 644 "/Library/Managed Preferences/com.brave.Browser.plist"
```

Restart the browser and confirm at `brave://policy` that the policy is listed and
its value is what you wrote. Local Network Access stays enforced everywhere else.

`--disable-features=LocalNetworkAccessChecks` also works and is worse: it is
browser-wide and has to be passed on every launch.

On Chrome the same policy key exists under `com.google.Chrome`, but Chrome has
not needed it in practice.

---

## 5. Check it before you spend anything

```bash
./run.sh doctor        # Python, ffmpeg, libvpx, folders, port, topics file
./run.sh               # then press Connect in the panel
```

If Connect fails, in this order:

1. Is `./run.sh` actually running, and on the port in `config.json`?
2. Does the panel say **build mismatch**? Reload the extension and hard-reload
   the tab.
3. Brave? Section 4.
4. Open the service worker's console — `chrome://extensions` → the extension →
   **service worker** — and press Connect again. A CORS or network error appears
   there and nowhere else.
