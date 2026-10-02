// Stand-in for libQt5SystemInfo.so.5 (Qt module qtsystems), which Sailfish
// does not ship. R7 Documents imports exactly four symbols from it, all about
// the IMEI:
//   QDeviceInfo::QDeviceInfo(QObject*), ~QDeviceInfo(),
//   imei(int) const, imeiCount() const
// We report "no IMEI". The Qt_5 version node has to be set via a version
// script, otherwise the package does not provide
// libQt5SystemInfo.so.5(Qt_5)(64bit) and rpm refuses to install R7.

#include <QtCore/QObject>
#include <QtCore/QString>

class QDeviceInfo : public QObject
{
public:
    explicit QDeviceInfo(QObject *parent = nullptr);
    ~QDeviceInfo();
    QString imei(int interfaceNumber) const;
    int imeiCount() const;
};

QDeviceInfo::QDeviceInfo(QObject *parent) : QObject(parent) {}
QDeviceInfo::~QDeviceInfo() {}
QString QDeviceInfo::imei(int) const { return QString(); }
int QDeviceInfo::imeiCount() const { return 0; }
