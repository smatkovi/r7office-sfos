# Analysis: R7 Documents (Aurora OS) on Sailfish OS

Working notes from the port. All figures were measured on a Jolla Phone (2026),
Sailfish OS 5.2.0.18, aarch64, against R7 Documents 1.5.5.2126.

## What the package turned out to be

Unpacking the vendor RPM answered the first question immediately: it is
**native, not a repackaged Android APK** (the download page's architecture
column says ANDROID, which is simply wrong there).

* The UI is **Sailfish Silica**. The QML ships as plain text:
  `qml/documents.qml`, `qml/pages/{FilesPage,EditorPage,…}.qml`, 20 occurrences
  of `import Sailfish.Silica 1.0`, plus `Sailfish.Pickers` and `Sailfish.Share`.
* The editor is a `Sailfish.WebView`. The binary contains `HttpServer` /
  `HttpConnection`: the app serves itself over local HTTP from
  `server/page.html` + `server/apps/sdkjs` + `server/apps/web-apps/.../mobile`.
* The native side is the ONLYOFFICE core: `libkernel`, `libgraphics`,
  `libdoctrenderer`, `libPdfFile`, `libDocxRenderer`, `libHtmlRenderer`,
  `libXpsFile`, `libEpubFile`, `libFb2File`, `libUnicodeConverter`,
  `libicu*.58`, and the `x2t` converter in `/usr/libexec/`.
* The `.desktop` file is standard Silica, including
  `[X-Sailjail] Permissions=Internet;MediaIndexing;UserDirs;WebView`.

Dependencies are almost pure Sailfish. `glibc >= 2.38` is required; the
SailfishOS 5.2 target ships 2.41, and Silica 1.2.156 clears the `>= 0.10.9`
requirement. `ldd -r` reports zero unresolved symbols, so R7 is built against a
Qt 5.6-era ABI that matches Sailfish.

## Blind alleys, and what ruled them out

Three hypotheses looked compelling and were all wrong. Recording them because
the measurements are the useful part.

**"The sandbox swallows the D-Bus file descriptor."** Tracker 3 does not return
query results in the D-Bus reply; it writes them into a descriptor the client
passes along (`Query(in s query, in h output_stream, in a{sv} arguments, out as
result)`). Intercepting `sendmsg` showed nine queries each carrying 24 bytes of
SCM_RIGHTS control data, and no error reply came back. Later, a probe built into
the shim ran the identical query from *inside* the real sandbox and received
both documents. The sandbox passes descriptors fine.

**"R7 needs its own patched Gecko."** The user agent string
(`AuroraOffline 4.0.2; AscDesktopEditor`) and the fact that `server/page.html`
was never opened as a file suggested the WebView loaded the UI through a custom
scheme and a native bridge that only R7's Gecko provides. Reading `page.html`
settled it: it loads
`http://localhost:10042/apps/web-apps/apps/api/documents/api.js` and calls
`new DocsAPI.DocEditor(…, "type": "mobile")`. Plain local HTTP, no custom
scheme. `server/` was never opened because the HTTP server never started —
which was a symptom, not the cause.

**"The shim returns a wrong path."** `getPath()` is called exactly once, at
startup, with type 13. During document opening it is not called at all.

## The instrument that actually solved it

For a long time the application appeared completely silent — no warnings, no
errors, nothing in the journal. The reason: the shim installed its Qt message
handler from a library constructor, and R7 installs its own later, displacing
it.

Reinstalling the handler inside `createView()` — after R7 has set its own — and
calling `QLoggingCategory::setFilterRules("*=true")` made the application speak,
and the first run produced the answer:

```
EditorPage.qml:143:13: Cannot assign to non-existent property "urlLoadingOverride"
```

Everything downstream followed from that one QML property. Once it was replaced
with `onLinkClicked`, the same log showed the full chain working:

```
execve /usr/libexec/ru.r7office.documents/x2t | … | Sketch.docx | …/preload…
Convert with args return 0 QProcess::ExitStatus(NormalExit)
bind 0.0.0.0:10042 -> 0
listen fd99 -> 0
connect 127.0.0.1:10042 -> -1   (EINPROGRESS, i.e. normal)
```

A caution for anyone adding interposers: hooking `read`/`open` without a hard
cap throttles the browser engine badly. Gecko reads strings containing
`file:///` constantly; logging each one turns page loads into timeouts. Filter
narrowly and cap the output.

## The file list

R7's `FilesModel` queries Tracker once per extension with the right ontology:

```sparql
PREFIX nfo: <http://tracker.api.gnome.org/ontology/v3/nfo#>
PREFIX nie: <http://tracker.api.gnome.org/ontology/v3/nie#>
SELECT ?path WHERE { ?u nie:url ?path .
                     FILTER(fn:ends-with(nfo:fileName(?u), '.docx')) }
```

Sailfish 5.2 answers it — the indexer is `localsearch` 3.9 with `tinysparql`
3.9, still under the old bus name `org.freedesktop.Tracker3.Miner.Files`.
Running the query by hand returns the documents, as does running it from inside
the sandbox. But no read in the application's address space ever contained a
result, in any run, with the hook in place and the cap never reached. R7 simply
never reads its own output stream.

One detail worth noting for anyone reimplementing this: `nie:url` yields
percent-encoded URLs (`file:///home/user/Documents/New%20document.docx`), not
plain paths.

Since that lives in closed C++, the patch replaces the model rather than the
query, scanning the standard folders with a `FolderListModel`.

## Summary

| Layer | State |
|---|---|
| Silica/Qt | fully compatible — the unmodified Aurora binary runs, five symbols short |
| Native core (`x2t`, converter libraries) | runs on Sailfish aarch64 without changes |
| Tracker, D-Bus, Sailjail, descriptor passing | all working |
| Editor WebView | one incompatible QML property |
| File list | R7 does not read its own Tracker results |
