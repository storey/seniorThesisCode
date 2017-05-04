# -*- coding: utf-8 -*-
# The core functions for running Tamnon and extracting the assocaited results

import os
import re
import json
import sys
import copy
import numpy as np
import matplotlib
#matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


from ..shared import utils as generalUtils
import utils

DIALECT = generalUtils.DIALECT

VERBOSE = False

# given a token, information about the tokens parses, the list of rules,
# the data for each lemma, and the number of possible dialect combos, and
# whether we only need a short report
def analyzeToken(token, tokenInfo, rules, evalResults, lemmaData, numCombos, shortReport):
    parseInfo = tokenInfo[0]

    result = {}
    result["token"] = token
    result["parses"] = parseInfo

    if(len(parseInfo) == 0):
        result["valid"] = False
        return result

    result["valid"] = True


    result["reasons"] = []

    for i in range(len(parseInfo)):
        result["reasons"].append([])

    # for each rule
    for rule in rules:
        # testing function returns an array specifying whether the token
        # matches (or doesn't match) a series of dialects;
        tester = rule["Tester"]
        rName = rule["ruleName"]

        comboMatches = []
        parseMatchInfo = []

        # determine the dialect of each parse by this rule
        for i in range(len(parseInfo)):
            parse = parseInfo[i]

            info = [parse, lemmaData[parse["lemma"]]]
            dialects = tester(info)

            # if there is no dialect verdict, just skip
            allZero = True
            for j in range(len(dialects)):
                if not(dialects[j] == 0):
                    allZero = False
            if not(allZero):
                comboMatches.append(dialects)
                parseMatchInfo.append([(i + 1), parse["lemma"], dialects])
                result["reasons"][i].append([dialects, rName])

        # store the results for this token and rule.
        if (len(comboMatches) > 0):
            ruleRes = {}
            # if any parse has some dialect 1 or -1; it definitely does,
            # or len(comboMatches) wouldn't be greater than 0
            ruleRes["maxPossible"] = 1
            # if every parse has some dialect 1 or -1; len(comboMatches) must
            # equal numper of parses
            if (len(comboMatches) == len(parseInfo)):
                ruleRes["minPossible"] = 1
            else:
                ruleRes["minPossible"] = 0

            ruleRes["comboResults"] = {}
            # if any parse has this combo
            ruleRes["comboResults"]["max"] = generalUtils.getNArray(numCombos, 0)
            # if every parse has this combo
            ruleRes["comboResults"]["min"] = generalUtils.getNArray(numCombos, 0)

            ruleRes["dialectResults"] = {}
            # if any parse has this dialect as a yes
            ruleRes["dialectResults"]["max"] = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)
            # if every parse has this dialect as a yes
            ruleRes["dialectResults"]["min"] = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)
            dialectCount = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)

            comboNumbers = []

            for cm in comboMatches:
                number = generalUtils.convertDialectArrayToInt(dialects)
                comboNumbers.append(number)
                for j in range(generalUtils.NUM_DIALECTS):
                    dialectCount[j] += cm[j]

            uniqueComboNumbers = set(comboNumbers)
            if (len(uniqueComboNumbers) == 1):
                uniqueNum = list(uniqueComboNumbers)[0]
                ruleRes["comboResults"]["min"][uniqueNum] = 1
            for cN in uniqueComboNumbers:
                ruleRes["comboResults"]["max"][cN] = 1

            for j in range(generalUtils.NUM_DIALECTS):
                if dialectCount[j] > 0:
                    ruleRes["dialectResults"]["max"][j] = 1
                if dialectCount[j] == len(parseInfo):
                    ruleRes["dialectResults"]["min"][j] = 1
            rule["ruleDecisions"].append([token, parseMatchInfo, ruleRes])

    numParses = len(parseInfo)
    result["parseResults"] = generalUtils.getNArray(numParses, 0)

    possibleCombos = []
    possibleDialects = []

    # unify data for each parse
    for i in range(numParses):
        reasons = []
        dialects = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)
        dialectInconsistent = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)
        dialectReasons = generalUtils.getNArray(generalUtils.NUM_DIALECTS, [])
        for reason in result["reasons"][i]:
            d = reason[0]
            for j in range(len(d)):
                # if the two have different signs
                if (d[j]*dialects[j] == -1):
                    dialects[j] = 1
                    dialectInconsistent[j] = 1
                    # add the name to the list of reasons for this dialect
                    dialectReasons[j].append(reason[1])
                elif d[j] == 1:
                    dialects[j] = 1
                    # add the name to the list of reasons for this dialect
                    dialectReasons[j].append(reason[1])
                elif d[j] == -1:
                    dialects[j] = -1

        # if they are all inconsistent, we say it is an inconsisent token
        oneConsistent = False
        oneInconsistent = False
        for j in range(len(dialects)):
            if (dialectInconsistent[j] == 1):
                oneInconsistent = True
            if (dialects[j] == 1 and dialectInconsistent[j] != 1):
                oneConsistent = True
                break

        # if none are consistent, let us know
        if oneInconsistent and not(oneConsistent):
            if VERBOSE:
                print "INCONSISTENT FORM:"
                print parseInfo[i]
                print result["reasons"][i]
            #print result

        # if any dialects are consistent and others are not, remove
        # the inconsistent ones from the possible list
        if oneInconsistent and oneConsistent:
            for j in range(len(dialects)):
                if (dialectInconsistent[j] == 1):
                    dialects[j] = -1
                    dialectReasons[j] = []


        # get teh combo results
        result["parseResults"][i] = [dialects, dialectReasons]
        possibleCombos.append(generalUtils.convertDialectArrayToInt(dialects))
        for j in range(len(dialects)):
            if (dialects[j] == 1):
                possibleDialects.append(j)


        # run the evaluation to compare it to all of our dialects
        if (utils.INCLUDE_EVAL and not(shortReport)):
            for j in range(len(dialects)):
                tamnonHas = (dialects[j] == 1)


                morpheusDialects = parseInfo[i]["dialect"]
                morpheusTargetDialect = generalUtils.getMorpheusDialectName(j)
                morpheusHas = not(morpheusDialects == None or (morpheusDialects.find(morpheusTargetDialect) == -1))

                if (False):
                    print morpheusDialects
                    print morpheusTargetDialect
                    print morpheusHas
                    print "--------------"



                if (tamnonHas and morpheusHas):
                    evalResults[j]["Both"]["Count"] += 1
                    parse = copy.deepcopy(parseInfo[i])
                    parse["reasons"] = dialectReasons[j]
                    evalResults[j]["Both"]["Parses"].append(parse)
                elif (tamnonHas):
                    evalResults[j]["TOnly"]["Count"] += 1
                    parse = copy.deepcopy(parseInfo[i])
                    parse["reasons"] = dialectReasons[j]
                    evalResults[j]["TOnly"]["Parses"].append(parse)
                elif (morpheusHas):
                    evalResults[j]["MOnly"]["Count"] += 1
                    parse = copy.deepcopy(parseInfo[i])
                    parse["reasons"] = dialectReasons[j]
                    evalResults[j]["MOnly"]["Parses"].append(parse)
                else:
                    evalResults[j]["Neither"]["Count"] += 1


    # does this count as max (or min) for each combo?
    result["comboResults"] = {}
    result["comboResults"]["max"] = generalUtils.getNArray(numCombos, 0)
    result["comboResults"]["min"] = generalUtils.getNArray(numCombos, 0)

    uniqPossibleCombos = set(possibleCombos)
    for item in uniqPossibleCombos:
        result["comboResults"]["max"][item] = 1
    if (len(uniqPossibleCombos) == 1):
        result["comboResults"]["min"][item] = 1

    # does this count as max (or min) for each dialect?
    result["dialectResults"] = {}
    result["dialectResults"]["max"] = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)
    result["dialectResults"]["min"] = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)
    uniqPossibleDialects = set(possibleDialects)
    for item in uniqPossibleDialects:
        result["dialectResults"]["max"][item] = 1
    if (len(uniqPossibleDialects) == 1 and (len(possibleDialects) == numParses)):
        result["dialectResults"]["min"][item] = 1


    # return the information about the token.
    return result

# given input text, rules, a filename containing information about each form, a
# file containing information about each lemma, the list of graph filenames, and
# whether to get data straight from Perseus' Morpheus, determine all the
# necessary information about the input text and return a series of textual
# reports. If graphFns is non-empty, store the result graphs at the filenames
# specified in graphFns.
# shortReport means we are only looking for minimal information
def generateResults(inputText, rules, formFn, lemmaFn, graphFns, fromPerseus, shortReport):
    (standardizedTokens, sortedUniqTokens) = inputText

    # get the form and lemma info
    (formData, lemmaData) = generalUtils.getFormAndLemmaData(sortedUniqTokens,
      fromPerseus, formFn, lemmaFn)

    numCombos = pow(3, generalUtils.NUM_DIALECTS)
    comboFrequencies = {}
    # array for each combination of dialects (max)
    comboFrequencies["Max"] = generalUtils.getNArray(numCombos, 0)
    # array for each combination of dialects (min)
    comboFrequencies["Min"] = generalUtils.getNArray(numCombos, 0)

    dialectFrequencies = {}
    # array for each dialect (max)
    dialectFrequencies["Max"] = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)
    # array for each dialect (min)
    dialectFrequencies["Min"] = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)

    numValidTokens = 0

    tokenByToken = []

    # set up way to store rule data
    for rule in rules:
        rule["ruleDecisions"] = []

    # set up evaluation stuff
    evalResults = generalUtils.getNArray(generalUtils.NUM_DIALECTS, {})

    for obj in evalResults:
        obj["Both"] = {
            "Count": 0,
            "Parses": []
        }
        obj["TOnly"] = {
            "Count": 0,
            "Parses": []
        }
        obj["MOnly"] = {
            "Count": 0,
            "Parses": []
        }
        obj["Neither"] = {
            "Count": 0
        }

    # run the analysis on each token.
    for token in standardizedTokens:
        if (token in formData):
            tokenInfo = [formData[token]]
            # need to calculate count data, rule data, evaluation results, and
            # individual token data
            res = analyzeToken(token, tokenInfo, rules, evalResults, lemmaData, numCombos, shortReport)
            tokenByToken.append(res)
            if (res["valid"]):
                numValidTokens += 1
                for i in range(numCombos):
                    comboFrequencies["Max"][i] += res["comboResults"]["max"][i]
                    comboFrequencies["Min"][i] += res["comboResults"]["min"][i]
                for i in range(generalUtils.NUM_DIALECTS):
                    dialectFrequencies["Max"][i] += res["dialectResults"]["max"][i]
                    dialectFrequencies["Min"][i] += res["dialectResults"]["min"][i]
        else:
            tokenByToken.append({"valid": False, "token": token})

    ruleResults = []
    # generate the rules text as well as the information necessary for
    # the graphs of the rule results.
    for rule in rules:

        maxPossible = 0
        maxComboOutcomes = generalUtils.getNArray(numCombos, 0)
        maxDialectOutcomes = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)
        minPossible = 0
        minComboOutcomes = generalUtils.getNArray(numCombos, 0)
        minDialectOutcomes = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)

        ruleDecisions = rule["ruleDecisions"]

        for decision in ruleDecisions:
            res = decision[2]
            maxPossible += res["maxPossible"]
            minPossible += res["minPossible"]
            for i in range(numCombos):
                maxComboOutcomes[i] += res["comboResults"]["max"][i]
                minComboOutcomes[i] += res["comboResults"]["min"][i]
            for i in range(generalUtils.NUM_DIALECTS):
                maxDialectOutcomes[i] += res["dialectResults"]["max"][i]
                minDialectOutcomes[i] += res["dialectResults"]["min"][i]


        ruleResult = {}
        ruleResult["Occurrences"] = {}
        ruleResult["Occurrences"]["Max"] = {}
        ruleResult["Occurrences"]["Min"] = {}
        ruleResult["Occurrences"]["Max"]["Possible"] = maxPossible
        ruleResult["Occurrences"]["Max"]["ComboOutcomes"] = maxComboOutcomes
        ruleResult["Occurrences"]["Max"]["DialectOutcomes"] = maxDialectOutcomes
        ruleResult["Occurrences"]["Min"]["Possible"] = minPossible
        ruleResult["Occurrences"]["Min"]["ComboOutcomes"] = minComboOutcomes
        ruleResult["Occurrences"]["Min"]["DialectOutcomes"] = minDialectOutcomes
        ruleResult["Rule"] = {}
        ruleResult["Rule"]["Short_Name"] = rule["Short_Name"]
        ruleResult["Rule"]["ruleName"] = rule["ruleName"]
        if not(shortReport):
            ruleResult["RuleDecisions"] = rule["ruleDecisions"]

        ruleResults.append(ruleResult)

    # setup the results
    results = {}
    results["NumTokens"] = len(standardizedTokens)
    results["NumUniqueTokens"] = len(sortedUniqTokens)
    results["NumValidTokens"] = numValidTokens
    results["ComboFrequencies"] = comboFrequencies
    results["DialectFrequencies"] = dialectFrequencies
    results["RuleResults"] = ruleResults
    if not(shortReport):
        results["TokenResults"] = tokenByToken
        results["EvalResults"] = evalResults

    return results


# given a set of results divided by book, unite them
def unifyDividedByBook(results):
    unified = {}

    numTokens = copy.deepcopy(results[0]["NumTokens"])
    comboFrequencies = copy.deepcopy(results[0]["ComboFrequencies"])
    dialectFrequencies = copy.deepcopy(results[0]["DialectFrequencies"])
    ruleResults = copy.deepcopy(results[0]["RuleResults"])

    numCombos = len(results[0]["ComboFrequencies"]["Max"])
    types = ["Max", "Min"]

    for i in range(1, len(results)):
        myResult = results[i]
        numTokens += myResult["NumTokens"]

        for aType in types:
            for k in range(numCombos):
                comboFrequencies[aType][k] += results[i]["ComboFrequencies"][aType][k]
            for k in range(generalUtils.NUM_DIALECTS):
                dialectFrequencies[aType][k] += results[i]["DialectFrequencies"][aType][k]

            rr = results[i]["RuleResults"]
            for j in range(len(ruleResults)):
                    myRRSub = ruleResults[j]["Occurrences"][aType]
                    rrSub = rr[j]["Occurrences"][aType]
                    myRRSub["Possible"] += rrSub["Possible"]

                    for k in range(numCombos):
                        myRRSub["ComboOutcomes"][k] += rrSub["ComboOutcomes"][k]
                    for k in range(generalUtils.NUM_DIALECTS):
                        myRRSub["DialectOutcomes"][k] += rrSub["DialectOutcomes"][k]


    unified["NumTokens"] = numTokens
    unified["NumUniqueTokens"] = 0
    unified["NumValidTokens"] = 0
    unified["ComboFrequencies"] = comboFrequencies
    unified["DialectFrequencies"] = dialectFrequencies
    unified["RuleResults"] = ruleResults

    unified["TextName"] = results[0]["TextName"]
    unified["SubName"] = "Overall"
    return unified

# given a unified set of features, set the uniqueTokens and validTokens
# to their proper values
def fixCombinedResults(results, lines, formDataFn, lemmaDataFn, fromPerseus):

    textBlock = ""
    for item in lines:
        textBlock += item["text"]

    (standardizedTokens, sortedUniqTokens) = generalUtils.cleanAndFixBlock(textBlock)
    (formData, lemmaData) = generalUtils.getFormAndLemmaData(sortedUniqTokens,
      fromPerseus, formDataFn, lemmaDataFn)

    numValidTokens = 0

    # run the analysis on each token.
    for token in standardizedTokens:
        if (token in formData):
            parseInfo = formData[token]
            if (len(parseInfo) != 0):
                numValidTokens += 1


    numTokens = len(standardizedTokens)
    numUniques = len(sortedUniqTokens)

    results[0]["NumUniqueTokens"] = numUniques
    results[0]["NumValidTokens"] = numValidTokens
    return results

# given a set of results, extract features
# divideByBook is true if the results are a list divided by book;
def extractFeatures(results, divideByBook):
    if divideByBook:
        features = []
        overall = extractFeatures(unifyDividedByBook(results), False)
        features.append(overall)

        for res in results:
            features.append(extractFeatures(res, False))

        return features
    else:
        featureResults = {}

        featureResults["NumTokens"] = results["NumTokens"]
        featureResults["NumUniqueTokens"] = results["NumUniqueTokens"]
        featureResults["NumValidTokens"] = results["NumValidTokens"]

        featureResults["DialectFrequencies"] = results["DialectFrequencies"]
        featureResults["ComboFrequencies"] = results["ComboFrequencies"]

        featureResults["RuleResults"] = []
        for i in range(len(results["RuleResults"])):
            res = results["RuleResults"][i]

            featureObj = {}
            featureObj["Rule"] = res["Rule"]
            featureObj["Occurrences"] = res["Occurrences"]
            featureResults["RuleResults"].append(featureObj)


        featureResults["TextName"] = results["TextName"]
        featureResults["SubName"] = results["SubName"]

        return featureResults


# given a parse, convert it to a string
def stringifyParse(parse, longform):
    s = ""
    if (longform):
        pre = "  "
    else:
        pre = "--"
    s += pre + "Form: " + parse["form"] + ", Lemma: " + parse["lemma"] + ".\n"
    if (longform):
        if (parse["dialect"] == None):
            parseDialect = "none"
        else:
            parseDialect = parse["dialect"]
        s += "  Dialect: " + parseDialect + "\n"
        s += "  Reasons: " + "; ".join(parse["reasons"]) + "\n"
        s += "    " + parse.__str__() + "\n"
    s += "----------"
    return s

# given a set of results, give them in pretty print form
# divideByBook is true if the analysis was divided into multiple books
def getResultText(results):

    featureResults = {}

    tab = "    "
    hl = "-----------"
    hlStrong = "==========="

    # =============================================
    # put together the overall results
    overallResults = []
    overallResults.append("OVERALL INFO:")

    # =============================================
    # put together the dialect results
    dialectPre = []
    dialectResults = []

    # store the dialect information
    dialectPre.append(["~~ Token Counts ~~"])
    dialectPre.append(["Number of Tokens: %d" % results["NumTokens"]])
    dialectPre.append(["Number of Unique Tokens: %d" % results["NumUniqueTokens"]])
    dialectPre.append(["Number of Valid Tokens: %d" % results["NumValidTokens"]])
    featureResults["NumTokens"] = results["NumTokens"]
    featureResults["NumUniqueTokens"] = results["NumUniqueTokens"]
    featureResults["NumValidTokens"] = results["NumValidTokens"]
    # For a full dialect output, we would want a token breakdown by dialect
    # as the second elements of the follwoing
    dialectPre.append(["-- Pure Dialect --"])
    for i in range(len(results["DialectFrequencies"]["Max"])):
        maxVal = results["DialectFrequencies"]["Max"][i]
        minVal = results["DialectFrequencies"]["Min"][i]
        dialectName = generalUtils.getDialectName(i)
        dialectPre.append(["  %s Tokens:\n  Max: %d\n  Min: %d" % (dialectName, maxVal, minVal)])

    dialectPre.append(["-- Combinations --"])
    for i in range(len(results["ComboFrequencies"]["Max"])):
        maxVal = results["ComboFrequencies"]["Max"][i]
        minVal = results["ComboFrequencies"]["Min"][i]
        comboName = generalUtils.getComboName(i)
        dialectPre.append(["  %s Tokens:\n  Max: %d\n  Min: %d" % (comboName, maxVal, minVal)])

    featureResults["NumValidTokens"] = results["DialectFrequencies"]
    featureResults["NumValidTokens"] = results["ComboFrequencies"]

    # append the overall dialect information to the overall results and all
    # dialect information to the dialect results
    for pre in dialectPre:
        overallResults.append(pre[0])
        dialectResults.append(pre[0])
        if (len(pre) >= 2):
            dialectResults.extend(pre[1])

    # =============================================
    # put together the rule results
    rulePre = []
    ruleResults = []

    rulePre.append("~~ Rule Results ~~")
    rulePre.append("- Rule Name, some breakdown.")

    # add the general rules text to the overall and rule reports
    for pre in rulePre:
        overallResults.append(pre)
        ruleResults.append(pre)


    featureResults["RuleResults"] = []
    for i in range(len(results["RuleResults"])):
        res = results["RuleResults"][i]
        # generate the text for this rule
        s = "%s: Max Occ: %d, Min Occ: %d" % (res["Rule"]["ruleName"], res["Occurrences"]["Max"]["Possible"], res["Occurrences"]["Min"]["Possible"])
        for j in range(generalUtils.NUM_DIALECTS):
            s += "\n  %s: Max: %d, Min: %d" % (generalUtils.getDialectName(j), res["Occurrences"]["Max"]["DialectOutcomes"][j], res["Occurrences"]["Min"]["DialectOutcomes"][j])
        overallResults.append(s)
        ruleResults.append(s)

        featureObj = {}
        featureObj["Rule"] = res["Rule"]
        featureObj["Occurrences"] = res["Occurrences"]
        featureResults["RuleResults"].append(featureObj)

        for tokenInfo in res["RuleDecisions"]:
            token = tokenInfo[0]
            notable_parses = tokenInfo[1]
            ruleResults.append("%s%s:" % (tab, token))
            for parse in notable_parses:
                s = "%s%sParse %d: %s. " % (tab, tab, parse[0], parse[1])
                s += "Dialect: " + "[" + ", ".join(map(str, parse[2])) + "]"
                ruleResults.append(s)
        ruleResults.append(hlStrong)

    # =============================================
    # put together the individual token results

    tokenResults = []
    tokenByToken = []

    for token in results["TokenResults"]:
        if (token["valid"]):

            s = "%s:\n" % (token["token"])
            s += tab + "Overall:\n"
            dialects = []
            for i in range(len(token["dialectResults"]["max"])):
                maxVal = token["dialectResults"]["max"][i]
                minVal = token["dialectResults"]["min"][i]
                dialectName = generalUtils.getDialectName(i)
                if (minVal == 1):
                    dialects.append("Definitely " + dialectName)
                elif (maxVal == 1):
                    dialects.append("Possibly " + dialectName)

            if (len(dialects) == 0):
                dialects.append("No clear dialect markers")
            s += tab + tab + ", ".join(dialects) + "\n"
            s += tab + hl + "\n"

            parseCount = 0
            for parse in token["parses"]:
                parseResults = token["parseResults"][parseCount]
                parseDialects = parseResults[0]
                parseDialectRules = parseResults[1]
                parseCount += 1
                s += tab + "Parse %d: %s:\n" % (parseCount, parse["lemma"])
                dialects = []
                dialectReasonsList = []
                for i in range(len(parseDialects)):
                    dialectName = generalUtils.getDialectName(i)
                    if (parseDialects[i] == 1):
                        dialects.append(dialectName)
                        s2 = tab + tab + tab + dialectName + " Reasons: " + ", ".join(parseDialectRules[i]) + "\n"
                        dialectReasonsList.append(s2)
                if (len(dialects) == 0):
                    dialects.append("No clear dialect markers")
                s += tab + tab + ", ".join(dialects) + "\n"
                s += "".join(dialectReasonsList)
                s += tab + hl + "\n"


            tokenByToken.append(s)
        else:
            tokenByToken.append("No form information for %s\n" % token["token"])


    tokenResults.append("~~ Individual Token Results ~~")
    tokenResults.append("\n".join(tokenByToken))

    # =============================================
    # put together the evaluation results
    eval_title = "~~ Evaluation Results ~~"
    #evaluationInfo = [eval_title, "Evaluation Information Disabled."]
    evaluationInfo = []

    # true if we want to print less info for something that is marked as every
    # dialect we are differeniating between, e.g. "epic ionic aeolic"
    avoidUniform = True

    # true if we also want to print out a results table in latex
    latexTable = True

    if (latexTable):
        s1 = "  \\begin{tabular}{| l |"
        s2 = "& "
        for i in range(generalUtils.NUM_DIALECTS):
            dialectName = generalUtils.getDialectName(i)
            s1 += " l |"
            s2 += "\\textbf{" + dialectName + "} & "
        s1 += "}\n\\hline\n"
        s2 = s2[0:-2] + "\\\\\n\\hline"
        print s1
        print s2
        bothNums = []
        tOnlyNums = []
        mOnlyNums = []
        neitherNums = []

    # evaluation results
    for i in range(len(results["EvalResults"])):
        dialect = results["EvalResults"][i]
        dialectName = generalUtils.getDialectName(i)
        evaluationInfo.append("~~~~ Dialect: " + dialectName + " ~~~~")
        bothDialect = dialect["Both"]
        tamnonOnly = dialect["TOnly"]
        morpheusOnly = dialect["MOnly"]
        bothNotDialect = dialect["Neither"]

        if (latexTable):
            bothNums.append(bothDialect["Count"])
            tOnlyNums.append(tamnonOnly["Count"])
            mOnlyNums.append(morpheusOnly["Count"])
            neitherNums.append(bothNotDialect["Count"])

        evaluationInfo.append("~~~ Total Counts: ~~~")
        evaluationInfo.append("~~ Both: " + str(bothDialect["Count"]) + " ~~")
        evaluationInfo.append("~~ Tamnon Only: " + str(tamnonOnly["Count"]) + " ~~")
        evaluationInfo.append("~~ Morpheus Only: " + str(morpheusOnly["Count"]) + " ~~")
        evaluationInfo.append("~~ Neither: " + str(bothNotDialect["Count"]) + " ~~")


        evaluationInfo.append("~~~ Individual Parses: ~~~")
        # given sorted parses and evaluation info
        def handleSortedParses(unsorted, ei):
            sp = sorted(unsorted, key=(lambda x: x["lemma"] + x["form"] + x.__str__()))
            lastParse = ""
            duplicates = 1
            initial = True
            for parse in sp:
                currentParse = stringifyParse(parse, True)
                if (currentParse == lastParse):
                    duplicates += 1
                else:
                    if (initial):
                        initial = False
                    else:
                        ei.append("(Parse appears %d times)" % duplicates)
                        ei.append("=======================")
                        duplicates = 1
                    lastParse = currentParse

                    if (avoidUniform and "dialect" in parse):
                        d = parse["dialect"]
                        if (d != None):
                            hasAll = True
                            for name in generalUtils.MORPHEUS_DIALECT_NAMES:
                                if d.find(name) == -1:
                                    hasAll = False
                            if (hasAll):
                                ei.append(stringifyParse(parse, False))
                                continue
                    ei.append(currentParse)
            ei.append("")

        evaluationInfo.append("~~ Both: " + str(bothDialect["Count"]) + " ~~")
        handleSortedParses(bothDialect["Parses"], evaluationInfo)

        evaluationInfo.append("~~ Tamnon Only: " + str(tamnonOnly["Count"]) + " ~~")
        handleSortedParses(tamnonOnly["Parses"], evaluationInfo)

        evaluationInfo.append("~~ Morpheus Only: " + str(morpheusOnly["Count"]) + " ~~")
        handleSortedParses(morpheusOnly["Parses"], evaluationInfo)


    if (latexTable):
        myList = [
            [bothNums, "Both"],
            [tOnlyNums, "\\bcode{ta/mnon}"],
            [mOnlyNums, "Morpheus"],
            [neitherNums, "Neither"]
        ]
        lineEnd = "\\\\\n\\hline"
        for i in range(len(myList)):
            item = myList[i]
            line = "\\textbf{" + item[1] + "}: & "
            for j in range(generalUtils.NUM_DIALECTS):
                line += str(item[0][j]) + " parses & "
            line = line[0:-2]
            line += lineEnd
            print line

        totalExamined = 0
        total = bothNums[0] + tOnlyNums[0] + mOnlyNums[0] + neitherNums[0]
        line = "\\textbf{Match on (Total: " + str(total) + ")}: & "
        for j in range(generalUtils.NUM_DIALECTS):
            agree = bothNums[j] + neitherNums[j]
            totalExamined += tOnlyNums[j] + mOnlyNums[j]
            line += "%d parses (%.2f\\%%)" % (agree, ((100.0*agree)/total)) + " & "
        line = line[0:-2] + lineEnd
        print line

        print "-------"
        print "Total Examined: " + str(totalExamined)


    # create all the result text
    overallResultsText = "\n".join(overallResults)
    dialectResultsText = "\n".join(dialectResults)
    ruleResultsText = "\n".join(ruleResults)
    tokenResultsText = "\n".join(tokenResults)
    evaluationResultsText = "\n".join(evaluationInfo)

    return (overallResultsText, dialectResultsText, ruleResultsText, tokenResultsText, evaluationResultsText, featureResults)




# given the individual pieces from generateResults, not including the accuracy
# evaluation results, combine them into a single piece of text
def combineResults(overall, dialect, rule, token):
    s = "-------OVERALL RESULTS:-------\n" + overall
    s += "\n-------SPECIFIC RESULTS:-------\n"
    s += dialect + "\n" + rule + "\n" + token
    return s

# given the individual pieces from generateResults, including the accuracy
# evaluation results, combine them into a single piece of text
def combineResultsEval(overall, dialect, rule, token, evaluation):
    s = "-------OVERALL RESULTS:-------\n" + overall
    s += "\n-------SPECIFIC RESULTS:-------\n"
    s += dialect + "\n" + rule + "\n" + token + "\n" + evaluation
    return s
