# -*- coding: utf-8 -*-
# This file is the portal for other programs to call processing functions.
# The core code that actually does the scansion is in core.py.
import json
from utils import FOOT, VERBOSE, VERY_VERBOSE, APPROACH
import core
from ..shared import utils as generalUtils

# The second pass involves making terminal -ew and -ewn into single syllables,
#    as well as attempting to combine mute-liquid pars like "pr" into a single
#    consonant.
# The third pass has ictus lengthening only (no need to combine -ewn if we don't need to but do need ictus lengthening )
# The fourth pass has the second pass and ictus lengthening
# Like fourth pass, but combine some stranger things than -ewn.
NUM_PASSES = 5

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Scansion function
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# scan the given line object, with line text in betacode at line["text"]
# lemma info and form info contain lemma and form info; dictionary contains
# dictionary data.
# approach is a constant stating the approach (student or native speaker)
# to use.
def scanLine(line, lemmaInfo, formInfo, dictionary, approach):
    text = line["text"]
    # if we're left with nothing, break
    if(text.isspace()):
        return {"Scan Result": 0, "Obj": {}, "Line": line}


    # run through the pipeline, getting the phonemes, syllables, lengths,
    # and scansion.
    worked = False;
    phonemes = core.getPhonemes(text, formInfo, dictionary, approach)
    if (VERBOSE):
        print "Line:"
        print line
        print "------------"
        print "Phonemes:"
        print phonemes
        print "------------"
    for passNumber in range(1, NUM_PASSES + 1):
        #print "Pass: " + str(passNumber)
        syllables = core.getSyllables(phonemes, passNumber, approach)
        if (VERBOSE):
            print "Syllables:"
            print core.getSyllablesString(syllables)
            print "------------"

        syllablesWithLengths = core.giveSyllablesLengths(syllables, lemmaInfo, formInfo, passNumber, approach)
        if (VERBOSE):
            print "Syllables w/ lengths:"
            print core.getSyllablesString(syllablesWithLengths)
            print "------------"

        scansions = core.getScansions(syllablesWithLengths, passNumber, approach)
        validScans = len(scansions)

        if (VERBOSE):
            print "Valid scans: " + str(validScans)
            print "------------"
            for i in range(validScans):
                scan = scansions[i]
                print "  Scan " + str(i) + ":"
                print "  " + scan.toString()
                print "--------------"

        if (validScans > 1):
            # abort
            break
        elif (validScans == 1):
            # valid scan found, break
            resultScansion = scansions[0]
            worked = True;
            break


    lineStr = "Line %d: " % line["line"]
    if worked:
        #print "Feet 2: " + ",".join(finalGuess.feet)
        lineStr += "success. Feet: " + ",".join(resultScansion.feet) + "." #.feet
        toReturn = {"Scan Result": 1, "Obj": resultScansion, "Features": core.extractFeatures(resultScansion), "Line": line}
    else:
        lineStr += "failed."
        toReturn = {"Scan Result": 0, "Obj": {}, "Line": line}
    if (VERY_VERBOSE):
        print lineStr
    return toReturn


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ External functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# get the scansion for a single line
def scanSingleLine(textName, line_number, approach):
    (lines, lemma, form, dictionary) = generalUtils.getScanData(textName)
    myLine = lines[line_number-1]
    return scanLine(myLine, lemma, form, dictionary, approach)

# get the scansions for an entire text
def processText(textName, approach, printSuccess):
    (lines, lemma, form, dictionary) = generalUtils.getScanData(textName)

    myResults = []

    size = len(lines)
    for i in range(size):
        myLine = lines[i]
        if (approach == APPROACH.FALLBACK):
            result = scanLine(myLine, lemma, form, dictionary, APPROACH.NATIVE_SPEAKER)
            if (result["Scan Result"] == 0):
                result = scanLine(myLine, lemma, form, dictionary, APPROACH.STUDENT)
        else:
            result = scanLine(myLine, lemma, form, dictionary, approach)
        myResults.append(result)
    #%.2f" + str(success) + "" + str(size) + "" + str(100.0*success/size) + "
    if (printSuccess):
        core.printSuccessRate(myResults)
    numSuccesses = core.getSuccessRate(myResults)

    #core.printFeatureResults(myResults)
    return myResults, size, numSuccesses


# compare the two approaches on a text
def compareApproaches(textName):
    (lines, lemma, form, dictionary) = generalUtils.getScanData(textName)

    myResults = []

    size = len(lines)
    for i in range(size):
        if (i % 1000 == 0 and i != 0):
            print "~~~~ %d/%d ~~~~" % (i, size)
        myLine = lines[i]
        resultStudent = scanLine(myLine, lemma, form, dictionary, APPROACH.STUDENT)
        resultNativeSpeaker = scanLine(myLine, lemma, form, dictionary, APPROACH.NATIVE_SPEAKER)

        sSuccess = (resultStudent["Scan Result"] == 1)
        nsSuccess = (resultNativeSpeaker["Scan Result"] == 1)

        if sSuccess and nsSuccess:
            sFeetString = "".join(map(lambda x: x[0], resultStudent["Obj"].feet))
            nsFeetString = "".join(map(lambda x: x[0], resultNativeSpeaker["Obj"].feet))
            if sFeetString != nsFeetString:
                print "Approaches differed on %s line %d." % (textName, (i+1))
                print "  Student: %s" % sFeetString
                print "  Native Speaker: %s" % nsFeetString
                print "------"
        elif sSuccess and not(nsSuccess):
            print "Native Speaker only failed on %s line %d." % (textName, (i+1))
            print "------"
        elif nsSuccess and not(sSuccess):
            if (True):
                print "Student only failed on %s line %d." % (textName, (i+1))
                print "------"
        else:
            if (True):
                print "Both failed on %s line %d." % (textName, (i+1))
                print "------"
    print "Done."


# given a string like "--|--|-uu|--|-uu|-x", extract the feet as a string
# of Ss, Ds and Fs, e.g. SSDSDF
# returns success and the list of feet
def extractFeetFromString(s):
    split = s.split("|")
    if (len(split) != 6):
        return False, []
    feet = ""
    for s in split:
        if (s == "--"):
            feet += "S"
        elif (s == "-uu"):
            feet += "D"
        elif (s == "-x"):
            feet += "F"
        else:
            return False, []
    #FOOT.DACTYL
    return True, feet

# evaluate a text against ground truth or another scanner.
# textName is the name of the text; approach is the scansion approach to use
# groundTruth is true if we are comparing against ground truth, false if
# against the Vilnius scansion.
def evalText(textName, approach, groundTruth):
    (lines, lemma, form, dictionary) = generalUtils.getScanData(textName)

    if groundTruth:
        targetScans = generalUtils.getTargetScanData(textName)
    else:
        data_fn = "scanData/thesaurusComScansion/Book1.txt"
        targetScans = generalUtils.getContent(data_fn, True)
    myResults = []
    evalInfo = []

    size = len(targetScans)
    odikonFails = 0
    odikonDiffers = 0
    compareFails = 0
    bothFails = 0
    for i in range(size):
        myLine = lines[i]
        result = scanLine(myLine, lemma, form, dictionary, approach)
        myResults.append(result)

        odikonSuccess = (result["Scan Result"] == 1)

        if groundTruth:
            compareSuccess = True
            compareFeetString = (targetScans[i] + "F")
        else:
            tLine = targetScans[i]
            compareRunSuccess = tLine["Scan Result"] == 1
            compareFeetSuccess, compareFeetString = extractFeetFromString(tLine["Scan"])
            compareSuccess = compareRunSuccess and compareFeetSuccess

        if odikonSuccess and compareSuccess:
            odikonFeetString = "".join(map(lambda x: x[0], result["Obj"].feet))
            if compareFeetString != odikonFeetString:
                evalInfo.append("Line %d Odikon Mismatch" % (i+1))
                evalInfo.append("Line: " + myLine["text"])
                if groundTruth:
                    evalInfo.append("  Ground Truth:  " + compareFeetString)
                else:
                    evalInfo.append("  Other Scanner: " + compareFeetString)
                evalInfo.append("  Odikon:        " + odikonFeetString)
                odikonDiffers += 1
        elif odikonSuccess:
            evalInfo.append("Line %d Comparative Scansion Failed" % (i+1))
            compareFails += 1
        elif compareSuccess:
            evalInfo.append("Line %d Odikon Scansion Failed" % (i+1))
            odikonFails += 1
        else:
            evalInfo.append("Line %d Both Scansions Failed" % (i+1))
            odikonFails += 1
            compareFails += 1
            bothFails += 1
        #print targetScans[i]
    #evalResults

    odikonTotalFails = odikonFails + odikonDiffers
    odikonSuccess = size - odikonTotalFails
    s = "Eval results for " + textName + "\n"
    if not(groundTruth):
        s += "Comparing to Vilnius scanner.\n"
    s += "Odikon differed/failed on %d/%d lines (Differed: %d. Failed: %d).\n" % (odikonTotalFails, size, odikonDiffers, odikonFails)
    s += "Compare failed on %d/%d lines.\n" % (compareFails, size)
    if (bothFails > 0):
        s += "Both failed on %d/%d lines.\n" % (bothFails, size)
    s += "\n".join(evalInfo)

    if groundTruth:
        fName = generalUtils.getScanEvalOutputFn(textName, approach)
    else:
        fName = generalUtils.getScanEvalOutputFn("Vilnius", approach)
    generalUtils.safeWrite(fName, s)

    return myResults, odikonSuccess, odikonFails, odikonDiffers

# the name of the text, whether we are dividing a large text into books
# as well, the actual results, the approach used, and whether to print the results.
def processFeatures(textName, divide_by_book, results, approach, printResults):

    # Callimachus Meyer's laws check
    if (False):
        for i in range(len(results)):
            myResult = results[i]
            if (myResult["Scan Result"] == 1):
                mls = myResult["Features"]["MeyersLaws"]
                if (mls[0] == 0 or mls[1] == 0 or mls[2] == 0):
                    print str(i) + ": " + myResult["Obj"].toString()
                    print results[i]
                    print mls

    if (True):
        featureResults = core.getFeatureResults(results, textName, divide_by_book)
        if (printResults):
            core.reportOnFeatures(featureResults)
        core.saveFeatureResults(featureResults, textName, approach)
        return featureResults

    #core.printLineResults(myResults, False)
    #core.reportOnFeatures(lines, myResults)
