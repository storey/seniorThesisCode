# -*- coding: utf-8 -*-
# This file runs the tests for each of the rules. Make sure to run
# tamnonGetTestForms.py first.

from ..shared import utils as generalUtils
import rules as tRules
import core
import utils
import json


# get the form and lemma data for the given set of (unique) tokens
def getFormData(tokenList):
    formInfoFileName = "tests/tests_form_data.txt"
    formInfoFile = open(formInfoFileName, 'r')
    formInfo_contents = formInfoFile.read()
    formInfoFile.close()
    formInfo = json.loads(formInfo_contents)

    lemmaInfoFileName = "tests/tests_lemma_data.txt"
    lemmaInfoFile = open(lemmaInfoFileName, 'r')
    lemmaInfoContents = lemmaInfoFile.read()
    lemmaInfoFile.close()
    lemmaInfo = json.loads(lemmaInfoContents)

    formInfoDict = {}
    for fi in formInfo:
        form = fi[0]
        parses = fi[1]
        if (form in tokenList):
            formInfoDict[form] = parses
    return (formInfoDict, lemmaInfo)

# given a target dialect and a token result that failed to match that
# target dialect, print an informative string;
def getFailureText(targetDialect, res, index):
    if (index == -1):
        return "Token \"" + res["token"] + "\" is not " + generalUtils.getDialectName(targetDialect) + "."
    else:
        return "Token \"" + res["token"] + "\", parse " + str(index) + ", is not " + generalUtils.getDialectName(targetDialect) + "."

# given a token, information about the token, information about the lemmas,
# the index of the parse to examine (-1 for all of them), the function that
# tests for whether a rule applies to the given token, the name of the rule,
# and the dialect that the tester should return, make sure that the rule
# tester returns the correct result.
def testToken(token, tokenInfo, lemmaInfo, index, tester, ruleName, targetDialect):
    # get the parses we are examining; if index is -1, all of them, otherwise
    # just the parse at index index.
    if (index == -1):
        formInfo= [tokenInfo[0]]
    else:
        formInfo= [[tokenInfo[0][index]]]

    # build dummy rules, since we don't care about this info
    dummyRules = [{
        "Tester": tester,
        "ruleName": ruleName,
        "ruleDecisions": []
    }]

    # build dummy eval, since we don't care #TODO: make this a flag in core
    dummyEval = generalUtils.getNArray(generalUtils.NUM_DIALECTS, {})
    for obj in dummyEval:
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

    # get number of combos
    numCombos = pow(3, generalUtils.NUM_DIALECTS)
    res = core.analyzeToken(token, formInfo, dummyRules, dummyEval, lemmaInfo, numCombos, True)

    correct_string = "%s: Correct.\n" % (token)
    if (targetDialect == generalUtils.DIALECT.ANY):
        allZero = True
        arr = res["dialectResults"]["max"]
        for j in range(len(arr)):
            if not(arr[j] == 0):
                allZero = False
        if (allZero):
            return (True, correct_string)
        else:
            return (False, getFailureText(targetDialect, res, index))
    else:
        if (res["dialectResults"]["max"][targetDialect] == 1):
            return (True, correct_string)
        else:
            return (False, getFailureText(targetDialect, res, index))
    return (False, "%s: ERROR! NO MATCH AT ALL!\n" % (token))

# test all of the rules
def testRules():
    # get the rules list
    rulesList = tRules.rulesList

    # get the list of unique tokens
    testTokensDuplicates = []
    for testRule in rulesList:
        for dialectIndex in testRule["Test_Forms"]:
            dialectTests = testRule["Test_Forms"][dialectIndex]
            for item in dialectTests:
                testTokensDuplicates.append(item[0])

    testTokensList = sorted(set(testTokensDuplicates))

    # get the form and lemma info from the tokens.
    (formData, lemmaInfo) = getFormData(testTokensList)

    rulesToTest = rulesList
    # to test an individual rule, use
    # rulesToTest = [rulesList[36]]

    allPassed = True

    # check the test forms for each of the rules, and print out any errors.
    for i in range(len(rulesToTest)):
        testRule = rulesToTest[i]
        tester = testRule["Tester"]
        ruleName = testRule["ruleName"]
        printedRuleTitle = False
        ruleTitle = "~~~~~~%d: RULE: %s~~~~~~" % (i, ruleName)
        for dialectIndex in testRule["Test_Forms"]:
            dialectTests = testRule["Test_Forms"][dialectIndex]
            for item in dialectTests:
                token = item[0]
                index = item[1]
                tokenInfo = [formData[token]]
                # need to calculate count data, rule data, individual token data
                (correct, txt) = testToken(token, tokenInfo, lemmaInfo, index,
                  tester, ruleName, dialectIndex)
                if (not(correct)):
                    if not(printedRuleTitle):
                        printedRuleTitle = True
                        print ruleTitle
                    allPassed = False
                    print "  ~~~" + generalUtils.getDialectName(dialectIndex) + ":~~~"
                    print txt
    if (allPassed):
        print "All Tests Passed! :)"
