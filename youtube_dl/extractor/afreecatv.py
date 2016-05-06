# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    xpath_text,
)


class AfreecaTVIE(InfoExtractor):
    IE_DESC = 'afreecatv.com'
    _VALID_URL = r'''(?x)^
        https?://(?:(live|afbbs|www)\.)?afreeca(?:tv)?\.com(?::\d+)?
        (?:
            /app/(?:index|read_ucc_bbs)\.cgi|
            /player/[Pp]layer\.(?:swf|html))
        \?.*?\bnTitleNo=(?P<id>\d+)'''
    _TEST = {
        'url': 'http://live.afreecatv.com:8079/app/index.cgi?szType=read_ucc_bbs&szBjId=dailyapril&nStationNo=16711924&nBbsNo=18605867&nTitleNo=36164052&szSkin=',
        'md5': 'f72c89fe7ecc14c1b5ce506c4996046e',
        'info_dict': {
            'id': '36164052',
            'ext': 'mp4',
            'title': '데일리 에이프릴 요정들의 시상식!',
            'thumbnail': 're:^https?://videoimg.afreecatv.com/.*$',
            'uploader': 'dailyapril',
            'uploader_id': 'dailyapril',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        parsed_url = compat_urllib_parse_urlparse(url)
        info_url = compat_urlparse.urlunparse(parsed_url._replace(
            netloc='afbbs.afreecatv.com:8080',
            path='/api/video/get_video_info.php'))
        video_xml = self._download_xml(info_url, video_id)

        if xpath_text(video_xml, './track/flag', default='FAIL') != 'SUCCEED':
            raise ExtractorError('Specified AfreecaTV video does not exist',
                                 expected=True)
        title = xpath_text(video_xml, './track/title', 'title')
        uploader = xpath_text(video_xml, './track/nickname', 'uploader')
        uploader_id = xpath_text(video_xml, './track/bj_id', 'uploader id')
        duration = int_or_none(xpath_text(video_xml, './track/duration',
                                          'duration'))
        thumbnail = xpath_text(video_xml, './track/titleImage', 'thumbnail')

        entries = []
        for video_file in video_xml.findall('./track/video/file'):
            entries.append({
                'id': video_file.get('key'),
                'title': title,
                'duration': int_or_none(video_file.get('duration')),
                'url': video_file.text,
            })

        info = {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'duration': duration,
            'thumbnail': thumbnail,
        }

        if len(entries) > 1:
            info['_type'] = 'multi_video'
            info['entries'] = entries
        elif len(entries) == 1:
            info['url'] = entries[0]['url']
        else:
            raise ExtractorError(
                'No files found for the specified AfreecaTV video, either'
                ' the URL is incorrect or the video has been made private.',
                expected=True)

        return info
