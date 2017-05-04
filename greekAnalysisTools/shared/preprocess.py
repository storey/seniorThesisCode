# -*- coding: utf-8 -*-
# given a name such that there is a file texts/[name].txt, run the
# preprocess step on the input file, cleaning up the data to produce the
# cleaned text, then running the Perseus Project's Morpheus morphological parser
# on each unique token and storing the form and lemma results in appropriate
# files.

import json
import utils
import sys


# combine a set of source texts into a single text with name textName.
def combineTexts(textName, sourceTexts):

    allLines = []
    for source in sourceTexts:
        inFileName = utils.getTextFn(source)
        lines = utils.getContent(inFileName, True)
        allLines.extend(lines)


    jsonDump = json.dumps(allLines)
    outFileName = utils.getTextFn(textName)
    utils.safeWrite(outFileName, jsonDump)



# textName is the name of the text
# splitByLine is true if the text is stored divided into lines in an
# object, false if it is a large, single block
# includeLemmaData is whether it include the information about lemmas in the
# output or not.
def preprocessText(textName, splitByLine, includeLemmaData):
    # get the necessary filenames
    inFileName = utils.getTextFn(textName)
    cleanFileName = utils.getTextCleanFn(textName)
    outFileName = utils.getTextFormDataFn(textName)
    outLemmasFileName = utils.getTextLemmasFn(textName)
    outFile2Name = utils.getTextLemmaDataFn(textName)

    # read the input data
    inFile = open(inFileName, 'r')
    inContents = inFile.read()
    inFile.close()

    if (splitByLine):
        lines = json.loads(inContents)
        # get the list of all cleaned tokens and unique cleaned tokens
        (fixedLines, fixedTokens, sortedUniqTokens) = utils.cleanAndFixLines(lines)

        # save the cleaned data
        utils.safeWrite(cleanFileName, json.dumps(fixedLines))
    else:
        # get the list of all cleaned tokens and unique cleaned tokens
        (fixedTokens, sortedUniqTokens) = utils.cleanAndFixBlock(inContents)

        # save the cleaned data
        cleanText = " ".join(fixedTokens)
        utils.safeWrite(cleanFileName, cleanText)


    # print general information about the tokens.
    print "Number of Tokens: ", len(fixedTokens)
    print "Number of Unique Tokens: ", len(sortedUniqTokens)

    if (includeLemmaData):
        # run the morphological parse to get info for each unique token
        lemmas = {}
        redownloadFormData = True#False#
        if (redownloadFormData):
            results = map(utils.getPerseusData(lemmas, True), sortedUniqTokens)
        else:
            results = utils.getContent(outFileName, True)
            lemmas = utils.getContent(outLemmasFileName, True)
        empties = 0
        for r in results:
            if (len(r[1]) == 0):
                empties += 1
        print "----- Got Forms! -----"
        print "Perseus lookup failed on " + str(empties) + " of " + str(len(results)) + "."
        print "----------------------"

        # save the form and lemma data in output files.
        if (redownloadFormData):
            jsonDump = json.dumps(results)
            utils.safeWrite(outFileName, jsonDump)
            jsonDump = json.dumps(lemmas)
            utils.safeWrite(outLemmasFileName, jsonDump)

        # get stem information about each of the unique lemmas
        lemmaResults = utils.getLemmaInfo(lemmas)

        jsonDump2 = json.dumps(lemmaResults)
        utils.safeWrite(outFile2Name, jsonDump2)
