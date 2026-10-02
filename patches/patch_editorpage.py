#!/usr/bin/env python3
"""Make EditorPage.qml work with Sailfish's WebView.

Aurora's Sailfish.WebView has a `urlLoadingOverride` property; Sailfish 5.2
does not. Assigning it makes the whole WebView component fail to instantiate,
so the editor never appears and you only see Silica's loader error. Sailfish
offers the `linkClicked(url)` signal instead, which carries the same intent:
hand foreign URLs to the system, keep our own inside the view.

This single property is what kept documents from opening at all. With it fixed,
the rest of the chain runs: x2t converts, the built-in HTTP server listens on
127.0.0.1:10042, and the mobile sdkjs frontend loads.
"""
PATH = "/usr/share/ru.r7office.documents/qml/pages/EditorPage.qml"

OLD = '''            urlLoadingOverride: function(data) {
                if (controller.testUrl(data.url))
                    return true;

                Qt.openUrlExternally(data.url)
                return false;
            }
'''

NEW = '''            onLinkClicked: {
                if (!controller.testUrl(url))
                    Qt.openUrlExternally(url)
            }
'''

def main():
    text = open(PATH).read()
    if "onLinkClicked" in text:
        print("EditorPage.qml already patched")
        return
    if OLD not in text:
        raise SystemExit("anchor not found -- a different version?")
    open(PATH, "w").write(text.replace(OLD, NEW))
    print("EditorPage.qml patched")

if __name__ == "__main__":
    main()
