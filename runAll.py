# -*- coding: utf-8 -*-
# This file runs the entire results pipeline:
# - downloads texts
# - downloads the raw dictionary and processes it
# - preprocesses the texts
# - extracts metrical features from the texts
# - extracts dialect features from the texts
# - runs postprocessing on the extracted features
# - gathers the results data

import sys
import greekAnalysisTools.dictionary.download as dlDictionary
import greekAnalysisTools.dictionary.process as pcDictionary
import greekAnalysisTools.shared.utils as utils
from greekAnalysisTools.shared.downloadText import downloadText
from greekAnalysisTools.shared.preprocess import preprocessText, combineTexts
from greekAnalysisTools.shared.postprocess import cleanAndCombineFeatures
from greekAnalysisTools.shared.getResults import resultsPipeline
import greekAnalysisTools.odikon.process as odikon
from greekAnalysisTools.odikon.utils import APPROACH
import greekAnalysisTools.tamnon.process as tamnon
from greekAnalysisTools.tamnon.getTestForms import getTestForms as tamnonGetTestForms
from greekAnalysisTools.tamnon.testRules import testRules as tamnonTestRules


# original set, to populate setup below as necessary;
# for example, if you get through the first 5 texts, and then it crashes,
# you can remove the first five texts from the list below so you don't
# re-check them.
texts = [
{
"textName": "Iliad",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0133%3Abook%3D",
"textAuthor": "Homer",
"numBooks": 24,
"divideByBook": True,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Odyssey",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0135%3Abook%3D",
"textAuthor": "Homer",
"numBooks": 24,
"divideByBook": True,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Hymns",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0137%3Ahymn%3D",
"textAuthor": "Anonymous",
"numBooks": 33,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "HymnsLong",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0137%3Ahymn%3D",
"textAuthor": "Anonymous",
"numBooks": 5,
"divideByBook": True,
"skipForAccuracyCount": True,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "HymnsShort",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0137%3Ahymn%3D",
"textAuthor": "Anonymous",
"increments": [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33],
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": True,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "CallimachusHymns",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0481%3Ahymn%3D",
"textAuthor": "Callimachus",
"numBooks": 6,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Abduction of Helen",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0495%3Abook%3D",
"textAuthor": "Colluthus",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Shield of Heracles",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0127%3Acard%3D",
"increments": [1, 39, 78, 115, 154, 178, 216, 245, 280, 327, 365, 402, 443],
"textAuthor": "Hesiod",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Theogony",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0129%3Acard%3D",
"increments": [1, 29, 53, 63, 104, 139, 173, 207, 240, 270, 304, 337, 371, 404, 453, 492, 507, 545, 585, 617, 645, 687, 729, 767, 807, 820, 853, 886, 901, 938, 963, 1003],
"textAuthor": "Hesiod",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Works and Days",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0131%3Acard%3D",
"increments": [1, 11, 42, 59, 83, 109, 140, 174, 202, 238, 274, 320, 370, 405, 448, 479, 504, 536, 571, 609, 641, 678, 706, 737, 765, 800],
"textAuthor": "Hesiod",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Epitaphius Bios",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0647%3Apoem%3D3",
"increments": [],
"textAuthor": "Moschus",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": True,
},
{
"textName": "Eros Drapeta",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0648%3Apoem%3D1",
"increments": [],
"textAuthor": "Moschus",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": True,
},
{
"textName": "Europa",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0644%3Apoem%3D2",
"increments": [],
"textAuthor": "Moschus",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": True,
},
{
"textName": "Megara",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0645%3Apoem%3D4",
"increments": [],
"textAuthor": "Moschus",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": True,
},
{
"textName": "Dionysiaca",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0485%3Abook%3D",
"textAuthor": "Nonnus of Panopolis",
"numBooks": 48,
"divideByBook": True,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Cynegetica",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0489%3Abook%3D",
"textAuthor": "Oppian of Apamea",
"numBooks": 4,
"divideByBook": True,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Halieutica",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0488%3Abook%3D",
"textAuthor": "Oppian",
"numBooks": 5,
"divideByBook": True,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Fall of Troy",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0490%3Abook%3D",
"textAuthor": "Quintus Smyrnaeus",
"numBooks": 14,
"divideByBook": True,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Idylls_Eidulia",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0228%3Atext%3DId.%3Apoem%3D",
"textAuthor": "Theocritus",
"numBooks": 30,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": True,
},
{
"textName": "Idylls_Epigrams",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0228%3Atext%3DEp.%3Apoem%3D",
"textAuthor": "Theocritus",
"numBooks": 24,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": True,
},
{
"textName": "The Taking of Ilios",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0491%3Abook%3D1",
"increments": [],
"textAuthor": "Tryphiodorus",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Argonautica",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0227%3Abook%3D",
"textAuthor": "Apollonius Rhodius",
"numBooks": 4,
"divideByBook": True,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Phaenomena",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0483%3Abook%3D1",
"increments": [],
"textAuthor": "Aratus Solensis",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": False,
},
{
"textName": "Epithalamium Achillis et Deidameiae",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0671%3Apoem%3D2",
"increments": [],
"textAuthor": "Bion of Phlossa",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": True,
},
{
"textName": "Epitaphius Adonis",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0672%3Apoem%3D1",
"increments": [],
"textAuthor": "Bion of Phlossa",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": True,
},
{
"textName": "Fragmenta",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0673%3Apoem%3D",
"increments":[3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18],
"textAuthor": "Bion of Phlossa",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": False,
"toBeCombined": True,
},
{
"textName": "Works of Moschus",
"textSource": "",
"textAuthor": "Moschus",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": True,
"toBeCombined": False,
"sourceTexts": ["Epitaphius Bios", "Eros Drapeta", "Europa", "Megara"]
},
{
"textName": "Idylls",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0228%3Atext%3DId.%3Apoem%3D",
"textAuthor": "Theocritus",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": True,
"toBeCombined": False,
"sourceTexts": ["Idylls_Eidulia", "Idylls_Epigrams"]
},
{
"textName": "Works of Bion",
"textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A2008.01.0671%3Apoem%3D2",
"increments": [],
"textAuthor": "Bion of Phlossa",
"numBooks": 1,
"divideByBook": False,
"skipForAccuracyCount": False,
"isCombined": True,
"toBeCombined": False,
"sourceTexts": ["Epithalamium Achillis et Deidameiae", "Epitaphius Adonis", "Fragmenta"]
}
]

# for evaluation, we also want these two texts.
if (True):
    texts.extend([{
    "textName": "Iliad1",
    "textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0133%3Abook%3D",
    "textAuthor": "Homer",
    "numBooks": 1,
    "divideByBook": False,
    "skipForAccuracyCount": True,
    "isCombined": False,
    "toBeCombined": False,
    },
    {
    "textName": "Odyssey1",
    "textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0135%3Abook%3D",
    "textAuthor": "Homer",
    "numBooks": 1,
    "divideByBook": False,
    "skipForAccuracyCount": True,
    "isCombined": False,
    "toBeCombined": False,
    }])


if (False):
    texts = [{
    "textName": "Iliad1",
    "textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0133%3Abook%3D",
    "textAuthor": "Homer",
    "numBooks": 1,
    "divideByBook": False,
    "skipForAccuracyCount": False,
    "isCombined": False,
    "toBeCombined": False,
    },
    {
    "textName": "Odyssey1",
    "textSource": "http://www.perseus.tufts.edu/hopper/xmlchunk?doc=Perseus%3Atext%3A1999.01.0135%3Abook%3D",
    "textAuthor": "Homer",
    "numBooks": 1,
    "divideByBook": False,
    "skipForAccuracyCount": False,
    "isCombined": False,
    "toBeCombined": False,
    }]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Helper Functions

def getScansionEvalResults(approach):
    latexTable = True#False#

    tableOutput = []
    if latexTable:
        s1 = "  \\begin{tabular}{| l |"
        s2 = "\\textbf{Text} & "
        titles = ["Agreement", "Disagreement", "Failure"]
        for title in titles:
            s1 += " c |"
            s2 += "\\textbf{" + title + "} & "
        s1 += "}\n\\hline\n"
        s2 = s2[0:-2] + "\\\\\n\\hline"
        tableOutput.append(s1)
        tableOutput.append(s2)


    texts = ["Iliad1", "Odyssey1", "CallimachusHymns"]
    for textName in texts:
        results, success, fails, differs = odikon.evalText(textName, approach, True)

        if (latexTable):
            s1 = "\\textit{" + textName + "} & "
            s1 += " %s & " % success
            s1 += " %s & " % differs
            s1 += " %s " % fails
            s1 += "\\\\\n\\hline"
            tableOutput.append(s1)

    fn = utils.getScanEvalTableOutputFn(approach)
    utils.safeWrite(fn, "\n".join(tableOutput))

    # Vilnius comparison
    odikon.evalText("Iliad1", approach, False)





#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Main Section


numTexts = len(texts)

totalLines = 0
totalSuccesses = 0

# download and process the dictionary
downloadDictionary = True#False#
processDictionary = True#False#

# download and get tokens for the text
preWork = True#False#

# scan the text
scan = True#False#
# only scan the text with no feature extraction
scanOnly = False#True#

#scanApproach = APPROACH.STUDENT
#scanApproach = APPROACH.NATIVE_SPEAKER
scanApproach = APPROACH.FALLBACK

# dialect analyze the text
dialect = True#False#

# combine and clean the features for the text
featureCleaning = True#False#

# get the results
runResults = True#False#
# skip the 3d graphs, which block execution until the user accesses them.
skipBlockingSteps = True#False#

# run evaluation steps
runEval = True#False#




# download the dictionaries
if (downloadDictionary):
    print "downloading dictionary..."
    dlDictionary.getEntries(utils.DICTIONARY_NAMES.LSJ)
    print "got entries... downloading entries."
    dlDictionary.downloadDict(utils.DICTIONARY_NAMES.LSJ)
    print "done downloading dictionary."
    print "===================="

if (processDictionary):
    print "processing dictionary..."
    pcDictionary.processDict1(utils.DICTIONARY_NAMES.LSJ)
    pcDictionary.processDict2(utils.DICTIONARY_NAMES.LSJ)
    print "done processing dictionary."
    print "===================="

# evaluate Tamnon
if (runEval):
    print "Testing Tamnon Rules..."
    tamnonGetTestForms()
    tamnonTestRules()
    print "Tamnon Rules Test Complete."
    print "===================="

# preprocessing, feature extraction
if (preWork or scan or dialect):
    # for all the texts
    for i in range(numTexts):
        text = texts[i]
        textName = text["textName"]
        textSource = text["textSource"]
        startBook = 1
        endBook = text["numBooks"]
        divideByBook = text["divideByBook"]
        isCombined = text["isCombined"]
        toBeCombined = text["toBeCombined"]
        skipForAccuracy = text["skipForAccuracyCount"]
        if ("increments" in text):
            hasIncrements = True
            increments = text["increments"]
        else:
            hasIncrements = False
            increments = None


        print textName + "(" + str(i+1) + "/" + str(numTexts) + ") ..."


        print "Text Name: " + textName

        if preWork:
            if not(isCombined):
                # download the text
                downloadText(textName, textSource, startBook, endBook, increments)
            else:
                combineTexts(textName, text["sourceTexts"])

        if (toBeCombined):
            print "~~skipping~~"
        else:
            if preWork:
                # preprocess the text
                preprocessText(textName, True, True)
                #          preprocessText(textName, True, False)

            if (dialect):
                shortReport = True
                #divideByBook = False
                tamnon.processText(textName, shortReport, divideByBook)
                print "  dialect analysis done."

            if (scan):
                results, numLines, numSuccesses = odikon.processText(textName, scanApproach, True)
                if not(skipForAccuracy):
                    totalLines += numLines
                    totalSuccesses += numSuccesses
                if not(scanOnly):
                    printResults = False#True#
                    featureResult = odikon.processFeatures(textName, divideByBook, results, scanApproach, printResults)
                print "  metrical analysis done."

        print textName + " done."
        print "===================="


if scan:
    if (totalLines == 0):
        print("Total: Success on %d out of %d. (%.2f%%)" % (totalSuccesses, totalLines, (0)))
    else:
        print("Total: Success on %d out of %d. (%.2f%%)" % (totalSuccesses, totalLines, (100.0*totalSuccesses/totalLines)))

    print "===================="

if (featureCleaning):
    print "Combining Features..."
    cleanAndCombineFeatures(texts, scanApproach)
    print "Done Combining Features."
    print "===================="


if (runResults):
    print "Running Results..."
    resultsPipeline(skipBlockingSteps)
    print "Done Running Results."
    print "===================="


if (runEval):
    print "Running Odikon Evaluation..."
    for approach in [APPROACH.STUDENT, APPROACH.NATIVE_SPEAKER]:
        getScansionEvalResults(approach)
    print "Scansion Evaluation Complete."
    print "===================="


print "===== All Done ====="
print "===================="





# this compares the Native Speaker and Student Approaches on a gvien text.
compareApproaches = False
if (compareApproaches):
    textName = "Odyssey1"
    odikon.compareApproaches(textName)
