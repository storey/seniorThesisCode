# This file does all the postprocessing, taking the raw features produced
# by Tamnon and Odikon, turning them into nice feature vectors, and combining
# everything together into a giant matrix.

import utils as generalUtils
import json

# given raw odikon feature data, create a clean, one-dimensional feature vector
# getText is true if we want the name of each feature rather than the feature values.
def cleanRawOdikon(raw, getText):
    finalFV = []
    success = raw["NumSuccessful"]

    if success == 0:
        return generalUtils.getNArray(51, 0)

    sp = raw["Spondaicism"]
    spFV = []
    for i in range(len(sp)):
        if (getText):
            spFV.append("Foot %d is spondaic" % (i+1))
        else:
            spFV.append(1.0*sp[i]/success)
    finalFV.extend(spFV)

    sr = raw["SpondaicRuns"]
    srFV = []
    for i in range(len(sr)):
        if (getText):
            srTypes = ["Single Double", "Double Double", "Triple", "Quadruple", "Quintuple"]
            srFV.append("Spondaic Runs: %s" % srTypes[i])
        else:
            srFV.append(1.0*sr[i]/success)
    finalFV.extend(srFV)

    caes = raw["CaesuraCounts"]
    caesFV = []

    for i in range(len(caes["anyCaesura"])):
        if (getText):
            caesFV.append("Some caesura at position %d" % (i))
        else:
            caesFV.append(1.0*caes["anyCaesura"][i]/success)
    for i in range(len(caes["masculineCaesura"])):
        if (getText):
            caesFV.append("Masculine caesura at position %d" % (i))
        else:
            caesFV.append(1.0*caes["masculineCaesura"][i]/success)
    for i in range(len(caes["feminineCaesura"])):
        if (getText):
            caesFV.append("Feminine caesura at position %d" % (i))
        else:
            caesFV.append(1.0*caes["feminineCaesura"][i]/success)
    for i in range(len(caes["principalCaesura"])):
        if (getText):
            caesFV.append("Principal caesura at position %d" % (i))
        else:
            caesFV.append(1.0*caes["principalCaesura"][i]/success)

    finalFV.extend(caesFV)

    diaer = raw["DiaeresisCounts"]
    diaerFV = []
    for i in range(len(diaer)):
        if (getText):
            diaerFV.append("Diaeresis at position %d" % (i))
        else:
            diaerFV.append(1.0*diaer[i]/success)
    finalFV.extend(diaerFV)

    corr = raw["Correption"]
    corrFV = []
    correptionHappened = corr[0]
    correptionMayHave = corr[1]
    corrTotal = correptionHappened + correptionMayHave
    if (corrTotal > 0):
        if (getText):
            corrFV.append("Frequency correption happened when it could have")
        else:
            corrFV.append(1.0*correptionHappened/corrTotal)
    else:
        if (getText):
            corrFV.append("Frequency correption happened when it could have")
        else:
            corrFV.append(0)
    if (getText):
        corrFV.append("Overall correption frequency")
    else:
        corrFV.append(1.0*correptionHappened/success)
    finalFV.extend(corrFV)

    il = raw["IctusLengthening"]
    ilFV = []
    for i in range(len(il)):
        if (getText):
            ilFV.append("Overall Ictus Lengthening frequency")
        else:
            ilFV.append(1.0*il[i]/success)

    # percentage of ictus lengthenings due to space
    if (il[0] > 0):
        if (getText):
            ilFV.append("Percentage of ictus lengthenings followed by space")
        else:
            ilFV.append(1.0*il[1]/il[0])
    else:
        if (getText):
            ilFV.append("Percentage of ictus lengthenings followed by space")
        else:
            # we default to 1, as this is the more common setup;
            ilFV.append(1)

    finalFV.extend(ilFV)

    ml = raw["MuteLiquid"]
    mlNames = ["r/l/n/m", "r/l", "n/m"]
    for i in range(len(ml)):
        sub = ml[i]
        subFV = []
        mlHappened = sub[0]
        mlMayHave = sub[1]
        mlTotal = mlHappened + mlMayHave
        if (mlTotal > 0):
            if (getText):
                subFV.append("Mute Liquid (%s) frequency in places it could have happened" % mlNames[i])
            else:
                subFV.append(1.0*mlHappened/mlTotal)
        else:
            if (getText):
                subFV.append("Mute Liquid (%s) frequency in places it could have happened" % mlNames[i])
            else:
                subFV.append(0)

        if (getText):
            subFV.append("Total Mute Liquid (%s) frequency" % mlNames[i])
        else:
            subFV.append(1.0*mlHappened/success)
        finalFV.extend(subFV)

    if False:
        digam = raw["Digamma"]
        digamNames = ["Total", "Closed Syl", "Hiatus"]
        for i in range(len(digam)):
            sub = digam[i]
            subFV = []
            digamHappened = sub[0]
            digamCouldHave = sub[1]
            digamTotal = digamHappened + digamCouldHave
            if (mlTotal > 0):
                if (getText):
                    subFV.append("%s digamma frequency in places it could have happened" % digamNames[i])
                else:
                    subFV.append(1.0*digamHappened/digamTotal)
            else:
                if (getText):
                    subFV.append("(%s digamma in places it could have happened" % digamNames[i])
                else:
                    subFV.append(0)

            if (getText):
                subFV.append("%s digamma frequency" % digamNames[i])
            else:
                subFV.append(1.0*digamHappened/success)
            finalFV.extend(subFV)

    mls = raw["MeyersLaws"]
    mlsFV = []
    for i in range(len(mls)):
        if (getText):
            mlsFV.append("Meyer's Law %d frequency" % (i+1))
        else:
            mlsFV.append(1.0*mls[i]/success)
    finalFV.extend(mlsFV)

    return finalFV

# given raw tamnon feature data, create a clean, one-dimensional feature vector
# getText is true if we want the name of each feature rather than the feature values.
def cleanRawTamnon(raw, getText):
    finalFV = []
    total = raw["NumTokens"]
    success = raw["NumValidTokens"]

    df = raw["DialectFrequencies"]
    cf = raw["ComboFrequencies"]
    rr = raw["RuleResults"]

    successRate = 1.0*success/total
    # this is a bad feature because the dictionaries are tailored to Homeric
    # vocabulary and therefore later works will have a lower success rate
    # for vocabulary inclusion reasons
    if (False):
        if (getText):
            finalFV.append("Success Rate")
        else:
            finalFV.append(successRate)

    # for each of type max min, look at the combos, dialects, and rules
    types = ["Max", "Min"]
    for aType in types:
        combos = cf[aType]
        cfFV = []
        for i in range(len(combos)):
            cCount = combos[i]
            if (getText):
                cfFV.append("Combo [%s] frequency (%s)" % (generalUtils.getComboName(i), aType))
            else:
                cfFV.append(1.0*cCount/success)
        finalFV.extend(cfFV)

        dialects = df[aType]
        dfFV = []
        for i in range(len(dialects)):
            dCount = dialects[i]
            if (getText):
                dfFV.append("Dialect %s frequency (%s)" % (generalUtils.getDialectName(i), aType))
            else:
                dfFV.append(1.0*dCount/success)
        finalFV.extend(dfFV)

        # for each rule, grab the combo and dialect outcomes
        for rule in rr:
            ruleCs = rule["Occurrences"][aType]["ComboOutcomes"]
            ruleDs = rule["Occurrences"][aType]["DialectOutcomes"]

            cfFV = []
            for j in range(len(ruleCs)):
                cCount = ruleCs[j]
                if (getText):
                    cfFV.append("Combo [%s] frequency (%s, %s)" % (generalUtils.getComboName(j), aType, rule["Rule"]["ruleName"]))
                else:
                    cfFV.append(1.0*cCount/success)
            finalFV.extend(cfFV)

            dialects = df[aType]
            dfFV = []
            for j in range(len(ruleDs)):
                dCount = ruleDs[j]
                if (getText):
                    dfFV.append("Dialect %s frequency (%s, %s)" % (generalUtils.getDialectName(j), aType, rule["Rule"]["ruleName"]))
                else:
                    dfFV.append(1.0*dCount/success)
            finalFV.extend(dfFV)

    return finalFV

# takes a list of the texts whose features we are to combine; the list
# should include the name for the text and whether it is divided by book
# also takes the Odikon approach to examine
def cleanAndCombineFeatures(texts, approach):

    matrix = []

    textNames = []

    featureNames = []

    numTexts = len(texts)
    # for all the texts
    for i in range(numTexts):
        text = texts[i]
        textName = text["textName"]
        divideByBook = text["divideByBook"]
        toBeCombined = text["toBeCombined"]

        if (toBeCombined or textName == "Iliad1" or textName == "Odyssey1"):
            continue

        ofn = generalUtils.getTextFeatureDataOdikonFn(textName, approach)
        tfn = generalUtils.getTextFeatureDataTamnonFn(textName)

        odikonFeaturesRaw = generalUtils.getContent(ofn, True)
        tamnonFeaturesRaw = generalUtils.getContent(tfn, True)

        if (len(odikonFeaturesRaw) != len(tamnonFeaturesRaw)):
            raise Exception("Number of subtexts for " + textName + " do not match")

        # for each set of features (the books plus the overall text)
        for j in range(len(odikonFeaturesRaw)):
            # get the raw features for this subtext
            ro = odikonFeaturesRaw[j]
            rt = tamnonFeaturesRaw[j]

            # determine the names for these two texts and make sure they match
            roString = ro["TextName"] + ": " + ro["SubName"]
            rtString = rt["TextName"] + ": " + rt["SubName"]
            if (roString != rtString):
                raise Exception("Book mismatch! " + roString + " and " + rtString)

            # add the cleaned features to the row
            row = []
            row.extend(cleanRawOdikon(ro, False))
            row.extend(cleanRawTamnon(rt, False))
            matrix.append(row)
            textNames.append(roString)

            # and one time, get the list of feature names.
            if (i == 0 and j == 0):
                featureNames.extend(cleanRawOdikon(ro, True))
                featureNames.extend(cleanRawTamnon(rt, True))

    # output the information.
    print "Number of Features: %d." % len(matrix[0])
    output = {
    "rowNames": textNames,
    "matrix": matrix,
    "featureNames": featureNames
    }
    fName = generalUtils.getFeatureMatrixFn()
    generalUtils.safeWrite(fName, json.dumps(output))
