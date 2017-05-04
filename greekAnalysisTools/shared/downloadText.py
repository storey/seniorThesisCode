# -*- coding: utf-8 -*-
# download a text from Perseus
from urllib2 import Request, urlopen, build_opener, URLError, HTTPError
import xml.etree.ElementTree as ET
import re
import json

import utils


# startBook and endBook should be indexed from 1
# increments is a custom set of increments to download from
def downloadText(textName, textSource, startBook, endBook, increments):
    books = []
    if (not(increments) == None):
        # if there are multiple cards, use them all, otherwise, it is single book.
        if (len(increments) >= 1):
            for i in range(len(increments)):
                index = increments[i]
                url = textSource + str(index)
                bookResult = utils.parse_TEI(utils.get_TEI_XML(url), textName, 1, True, index)
                books.extend(bookResult)
        else:
            url = textSource
            bookResult = utils.parse_TEI(utils.get_TEI_XML(url), textName, 1, False, 0)
            books.extend(bookResult)
    else:
        books = []
        for i in range(startBook-1, endBook):
            index = i+1
            url = textSource + str(index)
            bookResult = utils.parse_TEI(utils.get_TEI_XML(url), textName, index, False, 0)
            books.extend(bookResult)

    print "Lines: " + str(len(books))
    outFileName = utils.getTextFn(textName)
    utils.safeWrite(outFileName, json.dumps(books))
