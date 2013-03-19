#!/usr/bin/env python
# coding: utf-8

'''
Welcome to DeviceAtlas Cloud! All you need to get going is to set your DeviceAtlas
licence key below and import this module into your code.

Device data can then be retrieved as follows:

    import DeviceAtlasCloud.Client
    da = DeviceAtlasCloud.Client.Client()
    headers = {'user_agent': 'iPhone'}
    data = da.getDeviceData(headers)

The returned data will contain the following:

    data['properties']  - contains the device properties
    data['_error']  - contains any errors that occurred when fetching the properties
    data['_source'] -  states where the data came from, one of: 'cookie', 'cache', 'cloud' or 'none'.
    data['_useragent'] - contains the useragent that was used to query for data

@copyright Copyright © 2012 dotMobi. All rights reserved.
'''

__author__ = 'Ronan Cremin (tech@mtld.mobi)'
__copyright__ = 'Copyright © 2012 dotMobi. All rights reserved.'

import sys, urllib, urllib2, httplib, hashlib, os, json, tempfile, time, pprint


class Client:

    def __init__(self):
        ######################################################
        # BASIC SETUP
        # This is all you need to edit to get going
        self.LICENSE_KEY = 'enter_your_license_key_here'

        # ADVANCED SETUP
        # Edit these if you want to tweak behaviour

        self.USE_FILE_CACHE = True
        self.CACHE_ITEM_EXPIRY_SEC = 2592000;           # 2592000 = 30 days in seconds
        self.CACHE_NAME = 'deviceatlas_cache';
        self.CLOUD_HOST = 'api.deviceatlascloud.com'
        self.CLOUD_PORT = '80'
        self.CLOUD_PATH = '/v1/detect/properties?licencekey=%s&useragent=%s'
        self.TEST_USERAGENT = 'Mozilla/5.0 (Linux; U; Android 2.3.3; en-gb; GT-I9100 Build/GINGERBREAD) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'
        self.USE_SYSTEM_TEMP_DIR = True                 # leave as True to use system-defined default temp directory
        self.CUSTOM_CACHE_DIR = '/path/to/your/cache/'  # used only if USE_SYSTEM_TEMP_DIR is False

        # SEND_EXTRA_HEADERS - If this TRUE then extra headers are sent with each request to the service.
        #  If this is FALSE then only select headers essential for detection are sent.*/
        self.SEND_EXTRA_HEADERS = False

        # END OF SETUP, no need to edit below here!
        ######################################################

        # CONSTANTS
        self.USERAGENT = '_useragent';
        self.SOURCE = '_source';
        self.ERROR = '_error';
        self.PROPERTIES = 'properties';
        self.SOURCE_COOKIE = 'cookie';
        self.SOURCE_FILE_CACHE = 'cache';
        self.SOURCE_CLOUD = 'cloud';
        self.SOURCE_NONE = 'none';
        self.DA_HEADER_PREFIX = 'X-DA-'
        self.API_VERSION = 'python/1.1'
        self.UA_HEADER = 'HTTP_USER_AGENT'

        # A list of headers from the end user to pass to DeviceAtlas Cloud. These
        # help with detection, especially if a third party browser or a proxy changes
        # the original user-agent.
        self.ESSENTIAL_HEADERS = ['HTTP_X_PROFILE',
                                    'HTTP_X_WAP_PROFILE',
                                    'HTTP_X_DEVICE_USER_AGENT',
                                    'HTTP_X_ORIGINAL_USER_AGENT',
                                    'HTTP_X_SKYFIRE_PHONE',
                                    'HTTP_X_BOLT_PHONE_UA',
                                    'HTTP_X_ATT_DEVICEID',
                                    'HTTP_ACCEPT',
                                    'HTTP_ACCEPT_LANGUAGE']

        # A list of additional headers to send to DeviceAtlas. These are not sent
        # by default. These headers can be used for carrier detection and geoip.
        self.EXTRA_HEADERS = ['HTTP_CLIENT_IP',
                                'HTTP_X_FORWARDED_FOR',
                                'HTTP_X_FORWARDED',
                                'HTTP_FORWARDED_FOR',
                                'HTTP_FORWARDED',
                                'HTTP_PROXY_CLIENT_IP', # from Web Logic proxy
                                'HTTP_WL_PROXY_CLIENT_IP', # from Web Logic proxy
                                'REMOTE_ADDR'] # not really a header but it comes from the same $_SERVER array

        # END CONSTANTS

    def getDeviceData(self, headers={}, test_mode=False):
        '''Returns device data for given user agent, headers is dict of form:
          {'user_agent': 'Nokia6300', 'accept': 'text/html', 'x_profile': '..',
          'x_wap_profile': '..', 'accept_language': '..'}

        Once data has been returned from DeviceAtlas cloud it can be cached
        locally to speed up subsequent results.
        '''

        # user agent
        user_agent = ''

        if test_mode:
            user_agent = self.TEST_USERAGENT
        elif 'user_agent' in headers:
            user_agent = headers['user_agent'] # legacy api version
            del headers['user_agent']
        elif self.UA_HEADER in os.environ:
            user_agent = os.environ[self.UA_HEADER]

        try:

            results = {}
            results[self.SOURCE] = self.SOURCE_NONE
            results[self.USERAGENT] = user_agent

            # try file cache first
            device_data = ''
            if self.USE_FILE_CACHE:
                device_data = self.cacheGet(user_agent)
                results[self.SOURCE] = self.SOURCE_FILE_CACHE

            # fall back to fetching data from cloud
            if device_data == '':

                # build list of headers from environment variables
                headers.update(self.extractHeaders(self.ESSENTIAL_HEADERS))
                if self.SEND_EXTRA_HEADERS:
                    headers.update(self.extractHeaders(self.EXTRA_HEADERS))

                # call cloud service
                device_data = self.cloudGet(user_agent, headers)
                results[self.SOURCE] = self.SOURCE_CLOUD

                # set caches for future queries
                self.setCaches(user_agent, device_data, results[self.SOURCE])

            # decode json
            results[self.PROPERTIES] = self.decodeData(device_data)

        except Exception, err:
            results[self.ERROR] = str(err)

        return results

    def extractHeaders(self, headers):
        data = {}
        for header in headers:
            if header in os.environ:
                data[self.convertHeaderName(header)] = os.environ[header]

        return data

    def convertHeaderName(self, header):
        '''Converts HTTP header name from HTTP_HEADER_NAME to header_name'''

        if header.startswith('HTTP_'):
            return header[5:].lower().replace('_', '-')
        else:
            return header.lower().replace('_', '-')

    def cloudGet(self, user_agent, headers):
        '''Fetches device data from DeviceAtlas Cloud service. Passed data
        must be a dictionary of HTTP headers'''

        path = self.CLOUD_PATH % (self.LICENSE_KEY, urllib.quote(user_agent))

        # build request
        req = urllib2.Request('http://' + self.CLOUD_HOST + ':' + self.CLOUD_PORT + path)

        # add any additional headers supplied and API version as X-DA-* headers
        headers['version'] = self.API_VERSION
        for header, value in headers.items():
            req.add_header(self.DA_HEADER_PREFIX + header, value)

        try:
            resp = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            raise Exception('Error fetching DeviceAtlas data from Cloud. Code: ' + str(e.code) + ' ' + e.read().strip())

        device_data = resp.read()
        return device_data


    def setCaches(self, user_agent, device_data, source):
        '''Stores DeviceAtlas Cloud device data in file cache for later use'''

        if self.USE_FILE_CACHE and source == self.SOURCE_CLOUD:
            self.cachePut(user_agent, device_data)
        return


    def cacheGet(self, user_agent):
        '''Try and find devices data from the file cache'''

        device_data = ''
        fullpath = self.getCachePath(hashlib.md5(user_agent).hexdigest())

        if os.path.exists(fullpath):
            mtime = os.path.getmtime(fullpath)
            if mtime + self.CACHE_ITEM_EXPIRY_SEC > time.time():

                # read from the cache file
                fr = open(fullpath)
                device_data = fr.read()
                fr.close()

        return device_data


    def cachePut(self, user_agent, device_data):
        '''Put the device data in the file cache'''

        res = True
        fullpath = self.getCachePath(hashlib.md5(user_agent).hexdigest())
        dirname = os.path.dirname(fullpath)

        try:
            if not os.path.exists(dirname):
                os.makedirs(dirname, mode=0755)

            # write to the cache file
            fw = open(fullpath, 'w')
            fw.write(device_data)
            fw.close()

        except:
            raise Exception('Cannot write cache file data at "%s"' % fullpath)

        return res


    def getCacheBasePath(self):
        '''Returns base cache directory path'''

        base_path = ''

        if self.USE_SYSTEM_TEMP_DIR:
            base_path = tempfile.gettempdir()
        else:
            base_path = self.CUSTOM_CACHE_DIR

        base_path += os.sep + self.CACHE_NAME + os.sep

        return base_path

    def getCachePath(self, md5):
        '''Creates a cache path for this item by taking the md5 hash
        and using the first 4 characters to create a directory structure.
        This is done to prevent too many files existing in any one directory
        as this can lead to slowdowns.'''

        first_dir = md5[0:2]
        second_dir = md5[2:4]
        file_name = md5[4:len(md5)]

        return self.getCacheBasePath() + first_dir + os.sep + second_dir + os.sep + file_name


    def decodeData(self, device_data):
        '''Decodes the JSON data and extracts the properties'''

        props = ''
        if not device_data == {}:
            decoded = json.loads(device_data)
            if decoded.has_key(self.PROPERTIES):
                props = decoded[self.PROPERTIES]
            else:
                raise Exception('Cannot get device properties from "%s"' % device_data)

        return props

def test():
    '''Basic tests of cloud lookup'''

    da = Client()
    pp = pprint.PrettyPrinter(indent=4)

    # basic test device, no headers supplied
    data = da.getDeviceData(test_mode=True)
    print '\nTest mode results:'
    pp.pprint(data)

    # user-agent and accept headers sent
    headers = {
		'user_agent': 'SEC-SGHX210/1.0 UP.Link/6.3.1.13.0',
		'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
		}
    data = da.getDeviceData(headers)
    print '\nExample including accept header:'
    pp.pprint(data)

    # larger set of headers
    headers = {
		'user_agent': 'Mozilla/5.0 (Linux; U; Android 2.2; zh-cn; HTC_Desire_A8181 Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
		'accept': 'application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
		'accept_language': 'zh-CN, en-US',
		'x_wap_profile': 'http://www.htcmms.com.tw/Android/Common/Bravo/HTC_Desire_A8181.xml'
		}
    data = da.getDeviceData(headers)
    print '\nExample including multiple headers:'
    pp.pprint(data)


if __name__ == '__main__':
    test()


