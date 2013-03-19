DeviceAtlas Cloud

***** INTRO *****
DeviceAtlas Cloud is a web service which can return device information such
as screen width, screen height, is mobile, vendor, model etc. To see a full
list of properties in DeviceAtlas please visit http://deviceatlas.com .

The Python client API provides an easy way to query DeviceAtlas Cloud. It 
provides the ability to cache returned data locally to greatly improve 
performance.



***** CACHING *****
The client API uses a file cache to speed up subsequent requests. It is 
recommended to always use the cache.



***** CONFIG ***** 
The DeviceAtlas Cloud client is configured by setting the properties at the 
top of the DeviceAtlasCloud/Client.py file. The only required property is your 
DeviceAtlas licence key.



***** EXAMPLE USAGE *****
It is very easy to use the Client API. You simply need to import the module
and then instantiate the Client:

    import DeviceAtlasCloud.Client
    da = DeviceAtlasCloud.Client.Client()
    headers = {'user_agent': 'iPhone'}
    data = da.getDeviceData(headers)

The returned data will contain the following:

    data['properties']  - contains the device properties
    data['_error']  - contains any errors that occurred in fetching properties
    data['_source'] -  origin of data, one of: 'cookie', 'cache', 'cloud' or 'none'.
    data['_useragent'] - contains the useragent that was used to query for data

You can test for valid operation of the module by simply running it on the
command line:

    $ python Client.py 

    Test mode results:
    {   '_source': 'cloud',
        'properties': {   u'isMobilePhone': True,
                          u'model': u'iPhone',
                          u'vendor': u'Apple'}}

    Example including accept header:
    {   '_source': 'cloud',
        'properties': {   u'isMobilePhone': True,
                          u'model': u'SGH-X210',
                          u'vendor': u'Samsung'}}

    Example including multiple headers:
    {   '_source': 'cloud',
        'properties': {   u'isMobilePhone': True,
                          u'model': u'Desire',
                          u'vendor': u'HTC'}}

The included example.py script uses the client API to query DeviceAtlas Cloud
and displays a webpage with all the returned properties. This example can be
used with any web server that supports Python CGI scripts.

The Client API uses your device's User-Agent and other HTTP headers to
determine what device it is. If you are testing using a desktop web browser it
is recommended to use a User-Agent switcher plugin to modify the browser's
User-Agent.

Alternatively, simply passing True to getDeviceData() will make the client API
use a built in test User-Agent. This example script can also be run on the
command line. 

