# -*- coding: utf-8 -*-
import socket
import sys
import time
import os
import random
import copy
import json
import argparse
import socket
import codecs
if sys.version_info[0] < 3:
    is_py3 = False
    reload(sys)
    sys.setdefaultencoding('utf-8')
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr)
    from urlparse import urlparse
    from urllib import urlencode
    from urllib import quote_plus as url_quote
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib2 import URLError
    from urllib2 import HTTPError
else:
    is_py3 = True
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    from urllib.parse import urlencode
    from urllib.parse import quote_plus as url_quote
    from urllib.parse import urlparse
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.error import URLError
    from urllib.error import HTTPError


class Translation:
    translation = {
        'query': '',
        'phonetic': '',
        'paraphrase': '',
        'explain': []
    }

    def __init__(self):
        pass

    def __setitem__(self, k, v):
        self.translation.update({k: v})

    def __getitem__(self, k):
        pass

    def __new__(self):
        return self.translation

    def __str__(self):
        return str(self.translation)


class BasicTranslator(object):

    def __init__(self, name, **argv):
        self._name = name
        self._agent = None

    def request(self, url, data=None, post=False, header=None):
        if header:
            header = copy.deepcopy(header)
        else:
            header = {}
            header['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) \
                    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'

        if post:
            if data:
                data = urlencode(data).encode('utf-8')
        else:
            if data:
                query_string = urlencode(data)
                url = url + '?' + query_string
                data = None

        req = Request(url, data, header)

        try:
            r = urlopen(req, timeout=5)
        except (URLError, HTTPError, socket.timeout):
            sys.stderr.write("Timed out, please check your network")
            sys.exit()

        if is_py3:
            charset = r.headers.get_param('charset') or 'utf-8'
        else:
            charset = r.headers.getparam('charset') or 'utf-8'

        r = r.read().decode(charset)
        return r

    def http_get(self, url, data=None, header=None):
        return self.request(url, data, False, header)

    def http_post(self, url, data=None, header=None):
        return self.request(url, data, True, header)

    def set_proxy(self, proxy_url=None):
        try:
            import socks
        except ImportError:
            sys.stderr.write("pySocks module should be installed")
            sys.exit()

        proxy_types = {
            'http': socks.PROXY_TYPE_HTTP,
            'socks': socks.PROXY_TYPE_SOCKS4,
            'socks4': socks.PROXY_TYPE_SOCKS4,
            'socks5': socks.PROXY_TYPE_SOCKS5
        }

        url_component = urlparse(proxy_url)

        proxy_args = {
            'proxy_type': proxy_types[url_component.scheme],
            'addr': url_component.hostname,
            'port': url_component.port,
            'username': url_component.username,
            'password': url_component.password
        }

        socks.set_default_proxy(**proxy_args)
        socket.socket = socks.socksocket

    def test_request(self, test_url):
        print("test url: %s" % test_url)
        print(self.request(test_url))

    def translate(self, sl, tl, text):
        res = Translation()
        res['query'] = text         # 需要翻译的文本
        res['paraphrase'] = None    # 简单翻译
        res['phonetic'] = None      # 读音
        res['explain'] = None       # 详细翻译
        return res


class BingDict (BasicTranslator):

    def __init__(self, **argv):
        super(BingDict, self).__init__('bingdict', **argv)
        self._agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:50.0) Gecko/20100101'
        self._agent += ' Firefox/50.0'
        self._url = 'http://bing.com/dict/SerpHoverTrans'

    def translate(self, sl, tl, text):
        if 'zh' in tl:
            self._url = 'http://cn.bing.com/dict/SerpHoverTrans'

        url = self._url + '?q=' + url_quote(text)
        headers = {
            'Host': 'cn.bing.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        resp = self.http_get(url, None, headers)
        res = Translation()
        res['query'] = text
        res['explain'] = self.get_explain(text, resp)
        return res

    def get_explain(self, word, html):
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            sys.stderr.write("Install bs4 module to use bing translator")
            sys.exit()
        if not html:
            return []
        soup = BeautifulSoup(html, 'lxml')
        if soup.find('h4').text.strip() != word:
            return []
        lis = soup.find_all('li')
        trans = []
        for item in lis:
            t = item.get_text()
            if t:
                trans.append(t)
        if not trans:
            return []
        return trans


class CibaTranslator (BasicTranslator):

    def __init__(self, **argv):
        super(CibaTranslator, self).__init__('ciba', **argv)

    def translate(self, sl, tl, text):
        url = 'https://fy.iciba.com/ajax.php'
        req = {}
        req['a'] = 'fy'
        req['f'] = sl
        req['t'] = tl
        req['w'] = text
        r = self.http_get(url, req, None)
        resp = json.loads(r)
        res = Translation()
        res['query'] = text
        res['paraphrase'] = ''
        if 'content' in resp:
            if 'ph_en' in resp['content']:
                res['phonetic'] = resp['content']['ph_en']
            if 'out' in resp['content']:
                res['paraphrase'] = resp['content']['out']
            if 'word_mean' in resp['content']:
                res['explain'] = resp['content']['word_mean']
        return res


class GoogleTranslator (BasicTranslator):

    def __init__(self, **argv):
        super(GoogleTranslator, self).__init__('google', **argv)
        self._agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0)'
        self._agent += ' Gecko/20100101 Firefox/59.0'

    def get_url(self, sl, tl, qry):
        http_host = 'translate.googleapis.com'
        if 'zh' in tl:
            http_host = 'translate.google.cn'
        qry = url_quote(qry)
        url = 'https://{}/translate_a/single?client=gtx&sl={}&tl={}&dt=at&dt=bd&dt=ex&' \
              'dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss&dt=t&q={}'.format(
                  http_host, sl, tl, qry)
        return url

    def translate(self, sl, tl, text):
        self.text = text
        url = self.get_url(sl, tl, text)
        r = self.http_get(url)
        obj = json.loads(r)
        res = Translation()
        res['query'] = text
        res['paraphrase'] = self.get_paraphrase(obj)
        res['explain'] = self.get_explain(obj)
        return res

    def get_paraphrase(self, obj):
        paraphrase = ''
        for x in obj[0]:
            if x[0]:
                paraphrase += x[0]
        return paraphrase

    def get_explain(self, obj):
        explain = []
        if obj[1]:
            for x in obj[1]:
                expl = '[{}] '.format(x[0][0])
                for i in x[2]:
                    expl += i[0] + ';'
                explain.append(expl)
        return explain


class YoudaoTranslator (BasicTranslator):

    def __init__(self, **argv):
        super(YoudaoTranslator, self).__init__('youdao', **argv)
        self.url = 'https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
        self.D = "ebSeFb%=XZ%T[KZ)c(sy!"

    def get_md5(self, value):
        import hashlib
        m = hashlib.md5()
        m.update(value.encode('utf-8'))
        return m.hexdigest()

    def sign(self, text, salt):
        s = "fanyideskweb" + text + salt + self.D
        return self.get_md5(s)

    def translate(self, sl, tl, text):
        self.text = text
        salt = str(int(time.time() * 1000) + random.randint(0, 10))
        sign = self.sign(text, salt)
        header = {
            'Cookie': 'OUTFOX_SEARCH_USER_ID=-2022895048@10.168.8.76;',
            'Referer': 'http://fanyi.youdao.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; rv:51.0) Gecko/20100101 Firefox/51.0',
        }
        data = {
            'i': text,
            'from': sl,
            'to': tl,
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'salt': salt,
            'sign': sign,
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_CL1CKBUTTON',
            'typoResult': 'true'
        }
        r = self.http_post(self.url, data, header)
        obj = json.loads(r)
        res = Translation()
        res['query'] = text
        res['paraphrase'] = self.get_paraphrase(obj)
        res['explain'] = self.get_explain(obj)
        return res

    def get_paraphrase(self, obj):
        translation = ''
        t = obj.get('translateResult')
        if t:
            for n in t:
                part = []
                for m in n:
                    x = m.get('tgt')
                    if x:
                        part.append(x)
                if part:
                    translation += ', '.join(part)
        return translation

    def get_explain(self, obj):
        explain = []
        if 'smartResult' in obj:
            smarts = obj['smartResult']['entries']
            for entry in smarts:
                if entry:
                    entry = entry.replace('\r', '')
                    entry = entry.replace('\n', '')
                    explain.append(entry)
        return explain


ENGINES = {
    'google': GoogleTranslator,
    'youdao': YoudaoTranslator,
    'bing': BingDict,
    'ciba': CibaTranslator,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', required=True)
    parser.add_argument('--engine', required=True)
    parser.add_argument('--toLang', required=True)
    parser.add_argument('--proxy', required=False)
    args = parser.parse_args()

    text = args.text.strip('\'')
    text = text.strip('\"')
    text = text.strip()
    engine = args.engine
    to_lang = args.toLang

    cls = ENGINES.get(engine)
    if not cls:
        sys.stderr.write(
            "Engine name: %s was not found. Use google translator" % engine)
        cls = ENGINES.get('google')

    translator = cls()

    if args.proxy:
        translator.set_proxy(args.proxy)

    res = translator.translate('auto', to_lang, text)
    if not res:
        sys.stderr.write("Translation failed")
        sys.exit()

    sys.stdout.write(str(res))


if __name__ == '__main__':
    def test1():
        t = BingDict()
        r = t.translate('', '', 'good')
        print(r)

    def test2():
        t = CibaTranslator()
        r = t.translate('', '', 'good')
        print(r)

    def test3():
        gt = GoogleTranslator()
        r = gt.translate('auto', 'zh', 'private')
        print(r)

    def test4():
        t = YoudaoTranslator()
        r = t.translate('auto', 'zh', 'kiss')
        print(r)

    def test5():
        t = BasicTranslator('test_proxy')
        t.set_proxy('socks://localhost:1081')
        t.test_request('https://www.reddit.com')

    # test5()
    main()
