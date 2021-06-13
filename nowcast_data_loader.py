import json
from datetime import datetime, timedelta, timezone

from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl, QEventLoop, QTextStream
from qgis.core import QgsNetworkAccessManager

from .nowcast_settings import SettingsManager


class NowcastDataLoader:
    def __init__(self):
        self.eventloop = None
        self.isRepliedN1 = False
        self.isRepliedN2 = False

    def fetch_nowcast_timedata(self):
        n1 = 'https://www.jma.go.jp/bosai/jmatile/data/nowc/targetTimes_N1.json'
        n2 = 'https://www.jma.go.jp/bosai/jmatile/data/nowc/targetTimes_N2.json'

        networkAccessManager = QgsNetworkAccessManager.instance()

        self.eventLoop = QEventLoop()
        req1 = QNetworkRequest(QUrl(n1))
        req2 = QNetworkRequest(QUrl(n2))
        reply1 = networkAccessManager.get(req1)
        reply2 = networkAccessManager.get(req2)
        reply1.finished.connect(self.gotReplyFromN1)
        reply2.finished.connect(self.gotReplyFromN2)
        self.eventLoop.exec_()

        past_timedata_list = self.jsonify(
            reply1) if reply1.error() == QNetworkReply.NoError else []
        forecast_timedata_list = self.jsonify(
            reply2) if reply2.error() == QNetworkReply.NoError else []

        past_tiledata_list = list(
            map(self.get_tiledata_from, past_timedata_list))
        forecast_tiledata_list = list(
            map(self.get_tiledata_from, forecast_timedata_list))

        extended_tiledata_list = self.make_extended_tiledata_list(
            past_tiledata_list[0])

        return extended_tiledata_list + past_tiledata_list, forecast_tiledata_list

    def gotReplyFromN1(self):
        self.isRepliedN1 = True
        if self.isRepliedN2:
            self.eventLoop.quit()

    def gotReplyFromN2(self):
        self.isRepliedN2 = True
        if self.isRepliedN1:
            self.eventLoop.quit()

    @ staticmethod
    def make_extended_tiledata_list(oldest_past_tiledata):
        oldest_datetime = oldest_past_tiledata['datetime']

        def make_tiledata(jst_dt: datetime):
            utc_dt = jst_dt - timedelta(hours=9)
            yyyymmddhhmmss = f'{str(utc_dt.year)}{str(utc_dt.month).zfill(2)}{str(utc_dt.day).zfill(2)}{str(utc_dt.hour).zfill(2)}{str(utc_dt.minute).zfill(2)}{str(utc_dt.second).zfill(2)}'
            return {
                'datetime': jst_dt,
                'url': f'https://www.jma.go.jp/bosai/jmatile/data/nowc/{yyyymmddhhmmss}/none/{yyyymmddhhmmss}/surf/hrpns/' + r'{z}/{x}/{y}.png'

            }

        settings = SettingsManager()
        extend_duration = int(settings.get_setting('duration')) - 180
        extended_tiledata_list = [make_tiledata(
            oldest_datetime - timedelta(minutes=(extend_duration - i * 5))) for i in range(0, extend_duration // 5)]
        return extended_tiledata_list

    @ staticmethod
    def jsonify(reply: QNetworkReply):
        json_str = QTextStream(reply).readAll()
        json_dict = json.loads(json_str)
        return sorted(json_dict, key=lambda x: x['validtime'])

    @staticmethod
    def get_tiledata_from(timedata: dict):
        baseurl = r'https://www.jma.go.jp/bosai/jmatile/data/nowc/{basetime}/none/{validtime}/surf/hrpns/{z}/{x}/{y}.png'
        tileurl = baseurl.replace(r'{basetime}', timedata['basetime']).replace(
            r'{validtime}', timedata['validtime'])

        def text_to_datetime(yyyymmddhhmmss: str):
            year = int(yyyymmddhhmmss[0:4])
            month = int(yyyymmddhhmmss[4:6])
            day = int(yyyymmddhhmmss[6:8])
            hour = int(yyyymmddhhmmss[8:10])
            minute = int(yyyymmddhhmmss[10:12])
            second = int(yyyymmddhhmmss[12:14])
            jst_dt = datetime(
                year, month, day, hour, minute, second, tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))

            return jst_dt

        return {
            'datetime': text_to_datetime(timedata['validtime']),
            'url': tileurl
        }
