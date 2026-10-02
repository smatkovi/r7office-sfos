#!/usr/bin/env python3
"""Give FilesPage.qml a file list that actually fills.

R7's FilesModel sends its Tracker queries correctly -- one per extension, with
a working output file descriptor, no error reply -- but never reads the results
back. The list therefore stays empty ("Documents not found") even though
Tracker happily returns the documents. Measured from inside the sandbox: the
same query delivers both test documents there, so neither Tracker nor Sailjail
is at fault and `Sandboxing=Disabled` is not needed.

We point the list view at our own model, built from StandardPaths.documents and
.download via FolderListModel. The roles are the ones the delegate already
uses, so search, delete, rename and share keep working. R7's filesModel stays
in place because removeFile() hangs off it.
"""
PATH = "/usr/share/ru.r7office.documents/qml/pages/FilesPage.qml"

IMPORT_ANCHOR = "import Sailfish.Share 1.0\n"
IMPORT_ADDED = "import Qt.labs.folderlistmodel 2.1\n"

MODEL_ANCHOR = """        sortParameter: appSettings.sortParameter
    }
    property string vaitedDocument
"""

MODEL_NEW = """        sortParameter: appSettings.sortParameter
    }

    // --- Own file list ----------------------------------------------------
    // R7's FilesModel queries Tracker correctly but never reads the results,
    // so its list is always empty. We collect the documents ourselves from the
    // standard folders. R7's filesModel stays because removeFile() uses it.
    readonly property var documentFilters: ["*.doc", "*.docx", "*.odt", "*.rtf",
                                            "*.xls", "*.xlsx", "*.ods",
                                            "*.ppt", "*.pptx", "*.odp"]

    function asUrl(path) {
        return path.indexOf("file:") === 0 ? path : "file://" + path
    }

    function rebuildList() {
        if (!filesView)
            return
        ownList.clear()
        var search = filesView.searchText.toLowerCase()
        var readers = [ documentsReader, downloadsReader ]
        for (var r = 0; r < readers.length; ++r) {
            for (var i = 0; i < readers[r].count; ++i) {
                var name = readers[r].get(i, "fileName")
                if (search.length > 0 && name.toLowerCase().indexOf(search) < 0)
                    continue
                ownList.append({
                    "path": readers[r].get(i, "filePath"),
                    "fileName": name,
                    "extension": readers[r].get(i, "fileSuffix"),
                    "size": readers[r].get(i, "fileSize"),
                    "lastChanges": readers[r].get(i, "fileModified")
                })
            }
        }
    }

    ListModel { id: ownList }

    FolderListModel {
        id: documentsReader

        folder: root.asUrl(StandardPaths.documents)
        nameFilters: root.documentFilters
        showDirs: false
        sortField: FolderListModel.Time
        sortReversed: true
        onCountChanged: root.rebuildList()
    }

    FolderListModel {
        id: downloadsReader

        folder: root.asUrl(StandardPaths.download)
        nameFilters: root.documentFilters
        showDirs: false
        sortField: FolderListModel.Time
        sortReversed: true
        onCountChanged: root.rebuildList()
    }

    Connections {
        target: filesView
        onSearchTextChanged: root.rebuildList()
    }

    property string vaitedDocument
"""

VIEW_ANCHOR = "        model: root.filesModel\n"
VIEW_NEW = "        model: ownList\n"

def main():
    text = open(PATH).read()
    if "ownList" in text:
        print("FilesPage.qml already patched")
        return
    for anchor, what in ((IMPORT_ANCHOR, "import"), (MODEL_ANCHOR, "model"),
                         (VIEW_ANCHOR, "list view")):
        if anchor not in text:
            raise SystemExit("%s anchor not found -- a different version?" % what)
    text = text.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_ADDED, 1)
    text = text.replace(MODEL_ANCHOR, MODEL_NEW, 1)
    text = text.replace(VIEW_ANCHOR, VIEW_NEW, 1)
    open(PATH, "w").write(text)
    print("FilesPage.qml patched")

if __name__ == "__main__":
    main()
