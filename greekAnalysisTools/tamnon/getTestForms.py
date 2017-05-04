# -*- coding: utf-8 -*-
# This file is used to get all of the form and lemma info for forms used
# to test the various tamnon rules.

from ..shared import utils as generalUtils
import rules as tRules
import utils
import json

def getTestForms():
    outFileName = "tests/tests_form_data.txt"
    outFile2Name = "tests/tests_lemma_data.txt"

    # get all of the tokens required for test rules
    testTokensDuplicates = []
    for testRule in tRules.rulesList:
        for dialectIndex in testRule["Test_Forms"]:
            dialectTests = testRule["Test_Forms"][dialectIndex]
            for item in dialectTests:
                testTokensDuplicates.append(item[0])

    # get the unique tokens
    sortedUniqTokens = sorted(set(testTokensDuplicates))

    # get the form and lemma information
    lemmas = {}
    results = map(generalUtils.getPerseusData(lemmas, True), sortedUniqTokens)
    print "----- Got Forms! -----"
    lemmaResults = generalUtils.getLemmaInfo(lemmas)

    # save the form and lemma information
    jsonDump = json.dumps(results)
    generalUtils.safeWrite(outFileName, jsonDump)

    jsonDump2 = json.dumps(lemmaResults)
    generalUtils.safeWrite(outFile2Name, jsonDump2)
