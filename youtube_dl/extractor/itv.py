# coding: utf-8
from __future__ import unicode_literals

import urllib
import re
import pprint

from .common import InfoExtractor
from ..utils import (
    sanitized_Request
)

XML_POST_DATA="""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/" xmlns:itv="http://schemas.datacontract.org/2004/07/Itv.BB.Mercury.Common.Types" xmlns:com="http://schemas.itv.com/2009/05/Common">
  <soapenv:Header/>
  <soapenv:Body>
    <tem:GetPlaylist>
      <tem:request>
        <itv:ProductionId>%(productionId)s</itv:ProductionId>
        <itv:RequestGuid>FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF</itv:RequestGuid>
        <itv:Vodcrid>
          <com:Id/>
          <com:Partition>itv.com</com:Partition>
        </itv:Vodcrid>
      </tem:request>
      <tem:userInfo>
        <itv:Broadcaster>Itv</itv:Broadcaster>
        <itv:GeoLocationToken>
          <itv:Token/>
        </itv:GeoLocationToken>
        <itv:RevenueScienceValue>ITVPLAYER.12.18.4</itv:RevenueScienceValue>
        <itv:SessionId/>
        <itv:SsoToken/>
        <itv:UserToken/>
      </tem:userInfo>
      <tem:siteInfo>
        <itv:AdvertisingRestriction>None</itv:AdvertisingRestriction>
        <itv:AdvertisingSite>ITV</itv:AdvertisingSite>
        <itv:AdvertisingType>Any</itv:AdvertisingType>
        <itv:Area>ITVPLAYER.VIDEO</itv:Area>
        <itv:Category/>
        <itv:Platform>DotCom</itv:Platform>
        <itv:Site>ItvCom</itv:Site>
      </tem:siteInfo>
      <tem:deviceInfo>
        <itv:ScreenSize>Big</itv:ScreenSize>
      </tem:deviceInfo>
      <tem:playerInfo>
        <itv:Version>2</itv:Version>
      </tem:playerInfo>
    </tem:GetPlaylist>
  </soapenv:Body>
</soapenv:Envelope>
"""


class ITVIE(InfoExtractor):
    _VALID_URL = r'^http://www.itv.com/hub/(?P<show>[-\w]+)/(?P<id>[A-Z]*[\da-f]+)$'
    _TEST = {
        'url': 'http://www.itv.com/hub/vera/1a7314a0025',
        'info_dict': {
            'id': '1-7314-0025#001',
            'ext': 'flv',
            'title': 'Vera',
            'description': 'DCI Vera Stanhope investigates a mysterious double murder in a remote country manor house.'
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }

    _PROD_ID_RE = r'productionId=(?P<productionId>[\dA-Fa-f%]+)"'
    _HEADERS = {"Content-Type":"text/xml; charset=utf-8",
                "Referrer":"http://www.itv.com/mercury/Mercury_VideoPlayer.swf?v=1.5.309/[[DYNAMIC]]/2",
                "SOAPAction":'"http://tempuri.org/PlaylistService/GetPlaylist"'}
    _VIDEO1_RE = r'(?i)(?P<video>mp4:[^\]]+_[A-Z]+([0-9]{3,4})(|_[^\]]+)_(16|4)[-x](9|3)[^\]]*.mp4)'
    _VIDEO2_RE = r'(?i)(?P<video>mp4:[^\]]+_PC01([0-9]{3,4})(|_[^\]]+)_(16|4)[-x](9|3)[^\]]*.mp4)'
    _RTMP_BASE_RE = r'base="(?P<rtmpbase>rtmp[^"]+)"'
    _SUBTITLES_RE = r'<URL><!\[CDATA\[(http://subtitles\.[^\]]*)\]\]></URL>'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_blob = self._search_json_ld(webpage, video_id)

        # TODO more code goes here, for example ...
        productionId = self._html_search_regex(ITVIE._PROD_ID_RE, webpage, 'productionId')
        unencoded_productionId = urllib.unquote(productionId)

        data = XML_POST_DATA % {"productionId": unencoded_productionId}
        xml_request = sanitized_Request("http://mercury.itv.com/PlaylistService.svc", data = data, headers = ITVIE._HEADERS)
        xml_prog_data = self._download_webpage(xml_request, None, "Downloading program data for %s" % (unencoded_productionId))
        open("progdata.xml","w").write(xml_prog_data)
        rtmp_base = self._html_search_regex(ITVIE._RTMP_BASE_RE, xml_prog_data, 'rtmp_base')
        formats = []
        for videos1 in re.finditer(ITVIE._VIDEO1_RE, xml_prog_data):
          formats.append({"url": rtmp_base,
                          "play_path": videos1.group(1),
                          "format_id": videos1.group(0),
                          "protocol": "rtmp",
                          "tbr": int(videos1.group(2)),
                          "ext": "flv",
                          "format_id": int(videos1.group(2)),
                          "no_resume": True,
                          "player_url": "http://www.itv.com/mercury/Mercury_VideoPlayer.swf"})
        for videos2 in re.finditer(ITVIE._VIDEO2_RE, xml_prog_data):
          formats.append({"url":rtmp_base,
                          "play_path": videos2.group(1),
                          "format_id": videos2.group(0),
                          "protocol": "rtmp",
                          "tbr": int(videos2.group(2)),
                          "ext": "flv",
                          "format_if": int(videos2.group(2)),
                          "no_resume": True,
                          "player_url": "http://www.itv.com/mercury/Mercury_VideoPlayer.swf"})

        subtitles = {}
        subtitle_url = None
        #subtitle_url = self._html_search_regex(ITVIE._SUBTITLES_RE, xml_prog_data, 'subtitle_url')
        if subtitle_url:
            subtitles["en"] = [
                {
                    'url': subtitle_url,
                    'ext': "ttml"
                }
            ]
        
        return {
            'id': unencoded_productionId,
            'series': json_blob['series'],
            'title': json_blob['series'],
            'episode': json_blob['episode'],
#            'episode_number': json_blob['episode_number'],
            'description': json_blob['description'],
#            'season_number': json_blob['season_number'],
            'formats': formats,
            'subtitles': subtitles
        }
