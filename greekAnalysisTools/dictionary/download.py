# -*- coding: utf-8 -*-
# This file contains code for downloading the dictionaries.
from ..shared import utils
import xml.etree.ElementTree as ET
import json
import re
from bs4 import BeautifulSoup

VERBOSE = True

# get the next level of link out of a mbot.ind[i] item
# baseUrl is the default url used to load this page
# getXML is true if we want to return an xml link, false if we want
# an html link.
def getDictLinkFromSidebarItem(item, baseUrl, getXML):
    link = item.find_all("a")[0].get("href")
    #print link
    if(link[0:10] == "javascript"):
        val = baseUrl
    else:
        if (getXML):
            val = "http://www.perseus.tufts.edu/hopper/xmlchunk" + link
        else:
            val = "http://www.perseus.tufts.edu/hopper/text" + link
    return val

# given a list of links and a depth to search, find all the links of the next
# lower level
def getLowerLinks(urls, index):
    resultLinks = []
    totalNum = len(urls)
    i = 0
    for url in urls:
        if (VERBOSE):
            i += 1
            tab = "  "
            search = re.search('(?<=\%3Aalphabetic\+letter\%3D\*).', url)
            if (search):
                letter = search.group(0)
            else:
                letter = "a"
            if (index == 1):
                print tab + "letter: " + letter + ". " + str(i) + "/" + str(totalNum)
            if (index == 2):
                search2 = re.search('(?<=entry\+group\%3D).*', url)
                if (search2):
                    subsection = search2.group(0)
                else:
                    subsection = "1?"
                print tab + "letter: " + letter + ", subsection: " + subsection + ". " + str(i) + "/" + str(totalNum)
        htmlDoc = utils.getHtmlPage(url)
        soup = BeautifulSoup(htmlDoc, 'html.parser')
        nextSet = []
        selectorString = "#toc div.mbot.ind" + str(index)
        for item in soup.select(selectorString):
            if (index == 2):
                getXML = True
            else:
                getXML = False
            val = getDictLinkFromSidebarItem(item, url, getXML)
            nextSet.append(val)
        resultLinks.extend(nextSet)

    return resultLinks


# get the list of entries for the dictionary and store it in a file
def getEntries(dictName):
    #disppref?url=/hopper/text?doc=Perseus%3Atext%3A1999.04.0057&default.scheme=alphabetic%20letter%3Aentry&default.type=alphabetic%20letter
    #http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.04.0057%3Aentry%3Dku%2Fwn

    #urlString = "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.04.0057%3Aentry%3Dku%2Fwn"

    #"http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.04.0057"

    if (dictName == utils.DICTIONARY_NAMES.LSJ):
        baseURL = "http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.04.0057"
    elif (dictName == utils.DICTIONARY_NAMES.MiddleLiddell):
        baseURL = "http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.04.0058"
    elif (dictName == utils.DICTIONARY_NAMES.Slater):
        baseURL = "http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.04.0072"
    elif (dictName == utils.DICTIONARY_NAMES.Autenrieth):
        baseURL = "http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.04.0073"
    else:
        raise Exception("Invalid Dictionary.")

    if (VERBOSE):
        print "Getting Letter Links..."
    letterLinks = getLowerLinks([baseURL], 0)
    if (VERBOSE):
        print "Getting Subsection Links..."
    subLinks = getLowerLinks(letterLinks, 1)
    if (VERBOSE):
        print "Getting Word Links..."
    wordLinks = getLowerLinks(subLinks, 2)

    outFileName = utils.getDictionaryEntriesFn(dictName)
    utils.safeWrite(outFileName, json.dumps(wordLinks))


# download a dictionary given the list of entries
def downloadDict(dictName):
    inName = utils.getDictionaryEntriesFn(dictName)
    entries = utils.getContent(inName, True)

    fullList = []
    totalNum = len(entries)
    i = 0
    for entry in entries:
        if (VERBOSE):
            i += 1
            print dictName + " processing " + str(i) + " out of " + str(totalNum)
        entryXML = utils.get_TEI_XML(entry)
        fullList.append(entryXML)


    outFileName = utils.getRawDictionaryFn(dictName)
    utils.safeWrite(outFileName, json.dumps(fullList))


# download all the dictionaries.
def downloadAll():
    dictNames = []
    for dictName in dictNames:
        print "Downloading " + dictName + "..."
        downloadDict(dictName)
    print "Done"
