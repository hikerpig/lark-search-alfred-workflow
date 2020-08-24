# coding=utf-8

import httplib
import json
import os
import os.path
import struct
import sys
import urllib
import unicodedata
import re

from urlparse import urlparse
from datetime import datetime, date

from searchresult import SearchResult
from lark_common import cookie, larkDomain, larkDriveHome, parsedLarkDomain, unicodeAlfredQuery, headers

def buildSearchPayload(query_str):
    query = {
        "query": query_str,
        "offset": 0,
        "count": 9,
        "candidates_type": 2,
        "folder_tokens": None,
        "config_source": 0,
        "source": "web"
    }

    jsonData = json.dumps(query)
    return jsonData

conn = httplib.HTTPSConnection(parsedLarkDomain.netloc)
conn.request("POST", "/space/api/search/refine_search/",
             buildSearchPayload(unicodeAlfredQuery), headers)
response = conn.getresponse()

resData = response.read()
conn.close()

data = json.loads(resData)['data']

# for debug
# data = {}
# with open('results.json') as json_file:
#     data = json.load(json_file)
# data = data['data']

ITEM_TYPE_ICONNAME_MAPPING = {
    2: 'doc.png',
    3: 'sheet.png',
}

TITLE_REPLACE_PATTERN = "<em>(.*)</em>"

# Extract search results from lark response
searchResultList = []
objs = data['entities']['objs']
for k in data['tokens']:
    obj = objs[k]
    searchResultObject = SearchResult(obj['token'])
    title = obj['title']
    title = re.sub(TITLE_REPLACE_PATTERN, r"\1", title)
    searchResultObject.title = title
    viewed_time = datetime.fromtimestamp(obj['open_time']).strftime('%H:%M')
    updated_time = datetime.fromtimestamp(obj['edit_time']).isoformat()
    searchResultObject.subtitle = "Author: " + obj['author'] + ", You viewed " + viewed_time + ", " + obj['edit_name'] + " updated " + updated_time
    searchResultObject.link = obj['url']
    if ITEM_TYPE_ICONNAME_MAPPING.has_key(obj['type']):
        searchResultObject.icon = "itemicons/" + ITEM_TYPE_ICONNAME_MAPPING.get(obj['type'])
    searchResultList.append(searchResultObject)

itemList = []
for searchResultObject in searchResultList:
    item = {}
    item["uid"] = searchResultObject.id
    item["type"] = "default"
    item["title"] = searchResultObject.title
    item["arg"] = searchResultObject.link
    item["subtitle"] = searchResultObject.subtitle
    if searchResultObject.icon:
        icon = {}
        icon["path"] = searchResultObject.icon
        item["icon"] = icon
    item["autocomplete"] = searchResultObject.title
    itemList.append(item)

items = {}
if not itemList:
    item = {}
    item["uid"] = 1
    item["type"] = "default"
    item["title"] = "No results - go to Lark Space page"
    item["arg"] = larkDriveHome
    itemList.append(item)
items["items"] = itemList
items_json = json.dumps(items)

sys.stdout.write(items_json)
