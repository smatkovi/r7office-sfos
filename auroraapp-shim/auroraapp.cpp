// Stand-in for libauroraapp.so.2 (Aurora OS) on Sailfish OS.
//
// Maps the five Aurora::Application symbols that R7 Documents imports onto
// libsailfishapp. PathType lives in the global namespace, not inside the
// class -- the mangled name says so:
//   _ZN6Aurora11Application7getPathE8PathType  ->  plain "PathType"
//
// The important part: getPath() and cacheDir() return QDir, not QString.
// Returning a QString writes a single pointer into a return slot the caller
// reads as a QDir, which segfaults inside QDir::path() right out of main().

#include <sailfishapp.h>

#include <QtCore/QDebug>
#include <QtCore/QDir>
#include <QtCore/QFile>
#include <QtCore/QLoggingCategory>
#include <QtCore/QStandardPaths>
#include <QtCore/QString>
#include <QtCore/QTextStream>
#include <QtCore/QUrl>
#include <QtGui/QGuiApplication>
#include <QtQuick/QQuickView>

// --- Logging -----------------------------------------------------------------
// The application is started over D-Bus, so its standard output goes nowhere.
// We write our own file instead, and hook the Qt message handler so the
// application's own warnings land there too. Silent unless R7_LOG is set.

static QString logFile()
{
    return QString::fromLocal8Bit(qgetenv("HOME"))
         + QStringLiteral("/.cache/ru.r7office/documents/shim.log");
}

static void writeLine(const QString &line)
{
    static const bool enabled = !qgetenv("R7_LOG").isEmpty();
    if (!enabled)
        return;
    QFile f(logFile());
    if (!f.open(QIODevice::Append | QIODevice::Text))
        return;
    QTextStream(&f) << line << '\n';
}

static QtMessageHandler previousHandler = nullptr;

static void messageHandler(QtMsgType type, const QMessageLogContext &ctx, const QString &text)
{
    static const char *kind[] = { "D", "W", "C", "F", "I" };
    writeLine(QStringLiteral("[%1] %2 (%3:%4)")
              .arg(kind[type <= QtInfoMsg ? type : 0])
              .arg(text)
              .arg(ctx.file ? ctx.file : "?")
              .arg(ctx.line));
    if (previousHandler)
        previousHandler(type, ctx, text);
}

__attribute__((constructor)) static void installHandler()
{
    previousHandler = qInstallMessageHandler(messageHandler);
}

enum PathType {
    PathTypeUnknown = 0,
    PathTypeData,
    PathTypeCache,
    PathTypeConfig,
    PathTypeRuntime,
    PathTypeShare,
    PathTypeHome,
    PathTypeDocuments,
    PathTypeDownloads
};

namespace Aurora {
class Application
{
public:
    static QGuiApplication *application(int &argc, char **argv);
    static QQuickView *createView();
    static QUrl pathTo(const QString &filename);
    static QDir getPath(PathType type);
    static QDir cacheDir(bool shared);
};
}

QGuiApplication *Aurora::Application::application(int &argc, char **argv)
{
    return SailfishApp::application(argc, argv);
}

QQuickView *Aurora::Application::createView()
{
    // The application installs its own message handler while starting up,
    // displacing the one from our constructor. We run after that, so put ours
    // back -- and turn the logging categories on, or Qt swallows the debug
    // lines. This is what made the QML error visible in the first place.
    QLoggingCategory::setFilterRules(QStringLiteral("*=true\nqt.*.debug=false"));
    previousHandler = qInstallMessageHandler(messageHandler);
    writeLine(QStringLiteral("[shim] createView: message handler reinstalled"));
    return SailfishApp::createView();
}

QUrl Aurora::Application::pathTo(const QString &filename)
{
    const QUrl url = SailfishApp::pathTo(filename);
    writeLine(QStringLiteral("[shim] pathTo(%1) -> %2").arg(filename).arg(url.toString()));
    return url;
}

QDir Aurora::Application::getPath(PathType type)
{
    QStandardPaths::StandardLocation loc = QStandardPaths::AppDataLocation;
    switch (type) {
    case PathTypeCache:     loc = QStandardPaths::CacheLocation; break;
    case PathTypeConfig:    loc = QStandardPaths::AppConfigLocation; break;
    case PathTypeRuntime:   loc = QStandardPaths::RuntimeLocation; break;
    case PathTypeHome:      loc = QStandardPaths::HomeLocation; break;
    case PathTypeDocuments: loc = QStandardPaths::DocumentsLocation; break;
    case PathTypeDownloads: loc = QStandardPaths::DownloadLocation; break;
    case PathTypeShare:
        writeLine(QStringLiteral("[shim] getPath(Share=%1)").arg(int(type)));
        return QDir(QStringLiteral("/usr/share/ru.r7office.documents"));
    default: break;
    }
    const QString path = QStandardPaths::writableLocation(loc);
    writeLine(QStringLiteral("[shim] getPath(%1) -> %2").arg(int(type)).arg(path));
    return QDir(path);
}

QDir Aurora::Application::cacheDir(bool shared)
{
    QString path = QStandardPaths::writableLocation(QStandardPaths::CacheLocation);
    if (shared)
        path = QStandardPaths::writableLocation(QStandardPaths::GenericCacheLocation);
    QDir().mkpath(path);
    writeLine(QStringLiteral("[shim] cacheDir(%1) -> %2").arg(shared).arg(path));
    return QDir(path);
}
