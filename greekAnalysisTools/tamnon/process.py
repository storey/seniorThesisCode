# -*- coding: utf-8 -*-
# given a name such the file with that name has been preprocessed, run the
# tamnon process step on the associated files (cleaned text, form info, lemma
# info), analyzing the dialect of each token and outputing graphs an text
# files with results for overall dialect counts, rule-by-rule information,
# token-by-token results, and potentially information to evaluate tamnon
# against Perseus' Morpheus. This is simply the outward-facing function, with
# core functionality implemented in core.py.

from ..shared import utils as generalUtils
import rules as tRules
import utils
import core
import json
from itertools import groupby

# process the given text; if shortReport is true, return a short report
# rather than all the text. if divideByBook is true, return values for
# individual books and the text as a whole
def processText(textName, shortReport, divideByBook):
    cleanFileName = generalUtils.getTextCleanFn(textName)
    formDataFn = generalUtils.getTextFormDataFn(textName)
    lemmaDataFn = generalUtils.getTextLemmaDataFn(textName)

    longReport = not(shortReport)
    fromPerseus = False

    if (longReport):
        overallResultsFn = generalUtils.getTextOverallResultsFn(textName)
        dialectResultsFn = generalUtils.getTextDialectResultsFn(textName)
        ruleResultsFn = generalUtils.getTextRuleResultsFn(textName)
        tokenResultsFn = generalUtils.getTextTokenResultsFn(textName)
        evaluationResultsFn = generalUtils.getTextEvaluationResultsFn(textName)
        allResultsFn = generalUtils.getTextAllResultsFn(textName)
    featureResultsIntermediateFn = generalUtils.getTextReatureResultsTamnonIntermediateFn(textName)
    featureResults_fn = generalUtils.getTextFeatureDataTamnonFn(textName)

    graphFns = []
    if (longReport):
        # currently obsolete?
        graph_1_fname = generalUtils.getTextGraphFn(textName, "pct", "max", "unsorted")
        graph_2_fname = generalUtils.getTextGraphFn(textName, "pct", "min", "unsorted")
        graph_3_fname = generalUtils.getTextGraphFn(textName, "pct", "max", "sorted")
        graph_4_fname = generalUtils.getTextGraphFn(textName, "pct", "min", "sorted")
        graph_5_fname = generalUtils.getTextGraphFn(textName, "count", "max", "sorted")
        graph_6_fname = generalUtils.getTextGraphFn(textName, "count", "min", "sorted")
        graph_7_fname = generalUtils.getTextGraphFn(textName, "count_small", "max", "sorted")
        graph_8_fname = generalUtils.getTextGraphFn(textName, "count_small", "min", "sorted")
        graphFns = [graph_1_fname, graph_2_fname, graph_3_fname, graph_4_fname,
          graph_5_fname, graph_6_fname, graph_7_fname, graph_8_fname]



    # get the cleaned input data
    inContents = generalUtils.getContent(cleanFileName, True)

    lines2 = []
    if (textName == "CallimachusHymns"):
        for line in inContents:
            if not(line["book"] == 5 and (line["line"] % 2 == 0)):
                lines2.append(line)
    else:
        lines2 = inContents
    inContents = lines2

    # true if we want to print results from a pre-saved file
    resultsFromFile = False#True#
    if not(resultsFromFile):

        if (divideByBook):
            results = []
            numBooks = int(inContents[-1]["book"])
            # from http://stackoverflow.com/questions/30293071/python-find-same-values-in-a-list-and-group-together-a-new-list
            bookScansions = [list(j) for i, j in groupby(inContents, lambda x: x["book"])]
            for i in range(numBooks):
                name = "Book " + str(i+1)

                textBlock = ""
                lines = bookScansions[i]
                for item in lines:
                    textBlock += item["text"]

                (standardizedTokens, sortedUniqTokens) = generalUtils.cleanAndFixBlock(textBlock)

                inputText = (standardizedTokens, sortedUniqTokens)

                result = core.generateResults(inputText, tRules.rulesList, formDataFn, lemmaDataFn, graphFns, False, shortReport)
                result["TextName"] = textName
                result["SubName"] = name
                results.append(result)

        else:
            textBlock = ""
            lines = inContents
            for item in lines:
                textBlock += item["text"]

            (standardizedTokens, sortedUniqTokens) = generalUtils.cleanAndFixBlock(textBlock)

            inputText = (standardizedTokens, sortedUniqTokens)

            # generate the results for the given input text, rules list, form data and lemma
            # data files, and graph filenames, and telling the results generator to use the
            # given files and not go directly to Morpheus for parsing.
            results = core.generateResults(inputText, tRules.rulesList, formDataFn, lemmaDataFn, graphFns, fromPerseus, shortReport)
            results["TextName"] = textName
            results["SubName"] = "Overall"
            fullResults = results

        # save the general feature results
        generalUtils.safeWrite(featureResultsIntermediateFn, json.dumps(results))
    else:
        results = generalUtils.getContent(featureResultsIntermediateFn, True)
        if (divideByBook):
            fullResults = results[0]
        else:
            fullResults = results



    if (longReport):
        # print results
        (overall, dialect, rule, token, evaluation, outputResults) = core.getResultText(fullResults, divideByBook)
    else:
        outputResults = core.extractFeatures(results, divideByBook)
        if (divideByBook):
            outputResults = core.fixCombinedResults(outputResults, inContents, formDataFn, lemmaDataFn, fromPerseus)
        else:
            outputResults = [outputResults]

    generalUtils.safeWrite(featureResults_fn, json.dumps(outputResults))

    #print overall

    if (longReport):
        # stitch the results together for a unified output.
        allResultsText = core.combineResults(overall, dialect, rule, token)

        # print the results to their individual files.
        generalUtils.safeWrite(overallResultsFn, overall)
        generalUtils.safeWrite(dialectResultsFn, dialect)
        generalUtils.safeWrite(ruleResultsFn, rule)
        generalUtils.safeWrite(tokenResultsFn, token)
        if (utils.INCLUDE_EVAL):
            generalUtils.safeWrite(evaluationResultsFn, evaluation)
        generalUtils.safeWrite(allResultsFn, allResultsText)
