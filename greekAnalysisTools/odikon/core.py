# -*- coding: utf-8 -*-
# Contains the core functions used by process.py. There are a lot of
# improvements that could be made for the native speaker approach, but the
# biggest one is having a better dictionary to start with, and that will
# take time we don't have in the timeframe of this project :(

import json
import re
import copy
from itertools import groupby
from utils import APPROACH, FOOT, SYL, VERBOSE, VERY_VERBOSE
from ..shared import utils as generalUtils

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Objects and helper functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# object containing a list of consonants followed by a
# vowel sound, plus information about whether the set is followed by a
# space (for word-end stuff) or a space and then a vowel (for correption)
class CVObj:
    def __init__(self):
        self.consonants = []
        self.vowel = ""
        self.vowelSpaceVowel = False
        self.wordEndVowel = False
        self.lastVowelInWord = False
        self.pauseNext = False

    def toString(self):
        s = "".join(self.consonants) + self.vowel
        if (self.wordEndVowel):
            s += "[space]"
        return s

# object containing a single syllable
# startConsonants holds the consonants at the start of the syllable
# vowel contains the central vowel or dipthong plus associated diacritic info
# coreVowel contains the central vowel or dipthong with no diacritic info
# vowelInherentLength contains the vowel's inherent length (l, s, ?)
# endConsonant is the consonant at the end of the syllable, or "" if there is none.
# vowelSpaceVowel is true if this syllable ends with a vowel, there is
#     a space, and the next syllable starts with a vowel.
# doubleConsonantNext is whether the next syllable starts with zeta, xi, psi
# length is the length of this syllable
class SyllableObj:
    def __init__(self):
        # the list of consonants at the start of this syllable
        self.startConsonants = []
        # the vowel with all its diacritic info
        self.vowel = ""
        # just the vowel, no diacritics
        self.coreVowel = ""
        # vowel's inherent length
        self.vowelInherentLength = "?"
        # just the vowel accent
        self.vowelAccent = ""
        # just the vowel breathing
        self.vowelBreathing = ""
        # the consonant at the end of this syllable
        self.endConsonant = ""
        # is this vowel at the end of a word (a in polem*a*)
        self.wordEndVowel = False
        # is this the last vowel in the word (second o in polem*o*n)
        self.lastVowelInWord = False
        # is this the last vowel in the word and the next space counts as a
        # pause, that is, the next word isn't an enclitic and this isn't a
        # proclitic.
        self.pauseNext = False
        # is this vowel followed by a space and then another vowel?
        self.vowelSpaceVowel = False
        # are there multiple consonants at the start of the next syllable?
        self.doubleConsonantNext = False
        # is this followed by a potentially short z?
        self.possibleShortZNext = False
        # is there a mute followed by any liquid (r/l/m/n) after this vowel
        self.muteLiquidNext = False
        # is there a mute followed by a liquid (r/l) after this vowel
        self.muteLiquid1Next = False
        # is there a mute followed by a liquid (m/n) after this vowel
        self.muteLiquid2Next = False
        # would a digamma make this a closed syllable?
        self.closedByDigamma = False
        # would a digamma cause hiatus in this syllable?
        self.hiatusByDigamma = False
        # has this syllable been lengthened by ictus lengthening?
        self.ictusLengthened = False
        # what is the metrical length of this syllable
        self.length = SYL.UNKNOWN
        # does this syllable contain two vowels
        self.doubleVowel = False

    def toString(self):
        s = "".join(self.startConsonants) + self.vowel + self.endConsonant
        lengthStrings = {
        SYL.UNKNOWN: "<?>",
        SYL.SHORT: "<short>",
        SYL.LONG: "<long>"
        }
        s += lengthStrings[self.length]
        if (self.wordEndVowel):
            s += "[space]"
        if (self.lastVowelInWord):
            s += "[YlastVowel]"#""#
        if (self.pauseNext):
            s += "[PauseNext]"#""#
        else:
            s += ""#"[NlastVowel]"#
        return s

# print a list of syllables
def getSyllablesString(syllables):
    s = ""
    for syl in syllables:
        s += syl.toString()
        s += "-"
    return s


# object containing a scanned line
# syllables is a list of syllables in the line.
# feet is the list of feet in the line.
class ScannedLine:
    def __init__(self, syls, ft):
        self.syllables = syls
        self.feet = ft

    def toString(self):
        s = "Syllables: " + getSyllablesString(self.syllables)
        s += "\nFeet: " + ",".join(self.feet)
        return s


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Odikon sub-modules
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Phoneme Division
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# TODO
def getStemForParseIrregular(parseData, entry):
    return ("", [])

# ---------getStem -----------
# probably use entry pos for stem for adv/adj difference
# if parseData/entry["pos"] = "verb"
#   based on tense, voice; multiple possible stems
# if parseData/entry["pos"] = "noun"
#   if nom singular, 1 thing; otherwise, other
# if parseData/entry["pos"] = "adj"
#   have to think about this; masc/fem/neuter? singular?
# if parseData["pos"] = "part"
#   messy participle stuff
# if parseData/entry["pos"] = "pron"
#   per pronoun?
# if parseData/entry["pos"] = "article"
#   per article?
# if parseData/entry["pos"] = "adv"
#   per adverb? unless lemma data is an adjective

# stem from entry["pos"], ending handling from parseData["pos"]


# given parse data and a dictionary entry for the associated lemma, get two
# pieces of information about the stem; first, a string containing the stem
# with no accents, and second, the lengths of the vowels in the stem
def getStemForParse(parseData, entry):
    # if irregular, do separate handling
    if entry["irregular"]:
        return getStemForParseIrregular(parseData, entry)

    pos = entry["pos"]
    if (pos == "??"): #TODO: shouldn't need this
        pos = parseData["pos"]

    if (VERY_VERBOSE):
        print parseData
        print "---"
        print entry
        print "======"
    # verb: by tense, voice
    # noun: by nom/sg vs others
    # adj: by gender
    # adv, pron, article; just a single thing?
    try:
        if pos == "verb":
            if not("tense" in parseData):
                if (parseData["lemma"] == "fhmi/" or parseData["lemma"] == "e)/dw" or parseData["form"] == "e)pi/staito"):
                    tense = "pres"
                else:
                    if (VERBOSE): #TODO
                        print "VERB TENSE PROBLEM:"
                        print entry["betacode"]
                        print "---"
                        print parseData
                        print "---"
                        print entry
                        print "======"
                    return "nonexistant&&", []
            else:
                tense = parseData["tense"]
            if "voice" in parseData:
                voice = parseData["voice"]
            else:
                #TODO
                voice = "act"
            if (type(entry["stem"]) == type("a") or type(entry["stem"]) == type(u'a')):
                if (VERBOSE):
                    print "STEM PROBLEM:"
                    print parseData
                    print "---"
                    print entry
                    print "======"
                stem = entry["stem"]
                stemVowelLengths = entry["stemDivision"]
            else:
                if (tense == "futperf"):
                    # futperf setup
                    stem = entry["stem"][tense]
                    stemVowelLengths = entry["stemDivision"][tense]
                elif (tense == "imperf" or tense == "aor" or tense == "plup"):
                    # have to handle the unaugmented case
                    if (tense == "aor" and voice == "mp"):
                        voice = "mid"
                    if ((tense == "imperf" or tense == "plup") and (voice == "mid" or voice == "pass")):
                        voice = "mp"
                    augmented = "y"
                    # if unaugmented verb or a participle
                    if (parseData["feature"] == "unaugmented" or parseData["pos"] == "part"):
                        augmented = "n"
                    stem = entry["stem"][tense][voice][augmented]
                    stemVowelLengths = entry["stemDivision"][tense][voice][augmented]
                else:
                    if (tense == "fut" and voice == "mp"):
                        voice = "mid"
                    if ((tense == "pres" or tense == "perf") and (voice == "mid" or voice == "pass")):
                        voice = "mp"
                    if (tense in entry["stem"]):
                        stem = entry["stem"][tense][voice]
                        stemVowelLengths = entry["stemDivision"][tense][voice]
                    else: # e.g. te/mei
                        if (VERBOSE): #TODO
                            print ""
                            print "------"
                        return "nonexistant&&", []
        elif pos == "noun":
            if (type(entry["stem"]) == type("a") or type(entry["stem"]) == type(u'a')):
                if (VERBOSE):
                    print "STEM PROBLEM:"
                    print parseData
                    print "---"
                    print entry
                    print "======"
                stem = entry["stem"]
                stemVowelLengths = entry["stemDivision"]
            else:
                if parseData["pos"] == "adv":# TODO
                    myKey = "nomsg"
                elif (not("case") in parseData):
                    if not(parseData["feature"] == None) and parseData["feature"].find("indeclform") != -1:
                        myKey = "nomsg"
                    else: #TODO: this should never happen
                        myKey = "nomsg"
                # differentiate between nominative singular and the rest, e.g.
                # ai)c vs ai)go/s
                elif ((parseData["case"] == "nom") and (parseData["number"] == "sg")):
                    myKey = "nomsg"
                else:
                    myKey = "rest"
                stem = entry["stem"]["rest"]
                stemVowelLengths = entry["stemDivision"]["rest"]
        elif pos == "adj":
            if (type(entry["stem"]) == type("a") or type(entry["stem"]) == type(u'a')):
                if (VERBOSE):
                    print "STEM PROBLEM:"
                    print parseData
                    print "---"
                    print entry
                    print "======"
                stem = entry["stem"]
                stemVowelLengths = entry["stemDivision"]
            else:
                if (parseData["pos"] == "adv"):
                    myKey = "neutNom"
                elif (not("gender") in parseData):
                    if ("feature" in parseData and not(parseData["feature"] == None)):
                        if parseData["feature"].find("indeclform") != -1:
                            myKey = "neutNom"
                        else:
                            #TODO (this shouldn't happen )
                            myKey = "neutNom"
                    else:
                        # TODO: Morpheus problem; e.g. a)rei/osin, no gender
                        myKey = "neutNom"
                else:
                    gender = parseData["gender"]
                    if ("case" in parseData): # issue with pole/sin, which has no case...
                        if (parseData["case"] == "nom" and (gender == "masc" or gender == "neut")):
                            myKey = gender + "Nom"
                        else:
                            myKey = gender
                    else:
                        myKey = gender
                stem = entry["stem"][myKey]
                stemVowelLengths = entry["stemDivision"][myKey]
        elif pos == "adv":
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        elif pos == "pron":
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        elif pos == "article":
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        elif pos == "prep":
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        elif pos == "conj":
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        elif pos == "partic":
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        elif pos == "exclam":
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        elif pos == "part":
            if (VERBOSE):
                print "Participle Issue:"
                print entry["betacode"]
                print "---"
                print parseData
                print "---"
                print entry
                print "======"
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        elif pos == "numeral":
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        elif pos == "irreg":
            stem = entry["stem"]
            stemVowelLengths = entry["stemDivision"]
        else:
            raise Exception("Invalid part of speech: " + pos)
    except KeyError as ke:
        print "KEY ERROR!"
        print parseData
        print "---"
        print entry
        print "======"
        print ke
        raise Exception("Key Failure")


    return (stem, stemVowelLengths)



keepNonDiphthongsRegex = re.compile('(a|o|e|h|w)[/=+]([iu])')
#ending = re.sub(keepNonDiphthongsRegex, r'\1\2+', ending)
# split a betacode string into a set of phonemes
def splitStringIntoPhonemes(s):
    # if we have something like εΐ (ei+/), it is not a dipthong so split
    # the two vowels with a split symbol
    s = re.sub(r'([aeiouhw])\+', r'.\1', s)
    # modify dipthongs so the next step won't split them
    s = re.sub(r'((?:a|e|o|u)i|(?:a|o|e|h|w)u)', r'[\1]', s)
    s = re.sub(r'\[(a|e|o|u)i\]', r'.\1!', s)
    s = re.sub(r'\[(a|o|e|h|w)u\]', r'.\1@', s)
    # split all letters
    s = re.sub(r'(\w)', r'.\1', s)
    # unencode dipthongs
    s = re.sub(r'(a|e|o|u)!', r'.\1i', s)
    s = re.sub(r'(a|o|e|h|w)@', r'.\1u', s)
    # remove multiple splits
    s = re.sub(r'\.+', '.', s)
    return s

# given a list of phonemes, apply the default lengths to vowels
def applyBasicLengthsToPhonemes(phonemeString):
    resultVowels = []

    phons = phonemeString.split(".")
    for p in phons:
        if not(re.search(r'[aeiouhw]', p) == None):
            # diphthongs are just set as long by default
            if not(re.search(r'([aeiouhw]{2})|[hw]', p) == None):
                resultVowels.append(generalUtils.VOWEL_LEN.LONG)
            elif not(re.search(r'[eo]', p) == None):
                resultVowels.append(generalUtils.VOWEL_LEN.SHORT)
            else:
                resultVowels.append(generalUtils.VOWEL_LEN.UNKNOWN)
    return resultVowels

# get the default set of lengths for a string
def getDefaultLengths(s):
    phons = splitStringIntoPhonemes(s)
    res = applyBasicLengthsToPhonemes(phons)
    return res

# check whether this only has e/o/h/w + dipthongs (in which case we don't need
# to check for inherent lengths)
dipthongReplaceRegex = re.compile("(a|e|o|u)i(?![=/]*\+)|(a|o|e|h|w)u(?![=/]*\+)")
targetVowelsRegex = re.compile("[aiu]")
def allKnownVowels(ending):
    s = re.sub(dipthongReplaceRegex, r'1', ending)
    if not(re.search(targetVowelsRegex, s) == None):
        return False
    return True

# given an ending type, part of speech, an ending, and the associated parse
# data, return the proper phonetic division (with lengths) for that ending
def getEndingDivision(endingType, pos, ending, parseData):
    newEnding = ending
    if (len(ending) > 0 and ending[0] == "+"):
        return False, [], ending #TODO: always false if no match?
    if (allKnownVowels(ending)): # if there are only e/o/h/w/diphthongs, grab defaults
        res = getDefaultLengths(ending)
        if (endingType == generalUtils.ENDING_TYPES.VERB.OIDA):
            newEnding = "v" + ending
    else:
        worked, endingLens, funcNewEnding = generalUtils.ENDING_DIVISIONS[endingType](ending, parseData)
        if worked:
            res = endingLens
            newEnding = funcNewEnding
        else:
            if (VERBOSE):
                print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
                print "Ending " + ending + " not in list of endings for " + endingType + "."
                print "Lemma: " + parseData["lemma"]
                print "Form: " + parseData["form"]
                print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            # just default to the basic setup
            res = getDefaultLengths(ending)
    return True, res, newEnding

# given a token, data on a potential parse of the token, and dictionary,
# return the phonemes for that form (and a digamma'd stem if necessary )
accentReplaceRegex = re.compile('[=/]')
def getFormVowelLengths(token, parseData, dictionary):
    #print token
    #print parseData
    lemma = parseData["lemma"]
    #print parseData

    if lemma in dictionary:
        entry = dictionary[lemma]
        #print entry
        #print "-------------"

        accentlessToken = re.sub(accentReplaceRegex, "", token)
        (stem, stemVowelLengths) = getStemForParse(parseData, entry)

        defaultLens = getDefaultLengths(token)

        if (type(stem) != type([])):
            stem = [stem]
            stemVowelLengths = [stemVowelLengths]

        oneWorked = False
        newToken = token
        for i in range(len(stem)):
            if VERBOSE:
                print entry
            myStem = stem[i]
            checkStem = myStem.replace("v", "")
            if (accentlessToken.find(checkStem) == 0):
                ending = accentlessToken.replace(checkStem, "", 1)
                #print checkStem
                #print accentlessToken
                #print stem + " - " + ending

                if (token.find(myStem) == 0):
                    ending = token.replace(checkStem, "", 1)
                    ending = re.sub(keepNonDiphthongsRegex, r'\1\2+', ending)
                    ending = re.sub(accentReplaceRegex, "", ending)

                success, endingLengths, newEnding = getEndingDivision(entry["endingType"], parseData["pos"], ending, parseData)

                if not(success):
                    continue

                allLengths = copy.deepcopy(stemVowelLengths[i])

                if False:
                    print accentlessToken
                    print myStem
                    print ending
                    print allLengths
                    print endingLengths
                allLengths.extend(endingLengths)

                if (len(defaultLens) == len(allLengths)): # until we figure out ai)dei=sqai type stuf;; TODO
                    oneWorked = True
                    if len(newEnding) == 0 or (newEnding[0] == "'" or newEnding[0] == ")" or newEnding[0] == "(" or newEnding[0] == "+"):
                        newToken = myStem + newEnding# todo: add accent back in
                    else:
                        newToken = myStem + "." + newEnding# todo: add accent back in
                    break

        if not(oneWorked):
            if (VERBOSE):
                print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
                print "Stem does not match form " + accentlessToken + "."
                print stem
                print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            allLengths = defaultLens

        if False:
            print token
            print allLengths

        # get ending using stem on token.remove("/\=")
        # get ending type from entry[endingType]
        # get ending pieces from some superdictionary, passing type and ending

        return allLengths, newToken
    else:
        if (VERBOSE):
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            print "Lemma " + lemma + " not in dictionary."
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

        resultVowels = getDefaultLengths(token)

        return resultVowels, token

# given a list of potential for a series of vowels, combine them into
# one set
def unifyPossibleTokenVowelLengths(possibles):
    res = []
    # TODO: look at this; example issue is when we have xruseiois from xruseos,
    # so we end up with iois as the ending;
    allSame = True
    base = len(possibles[0][0])

    # this defaults to taking one without the digamma, if that is possible;
    minLen = len(possibles[0][1].replace("/", "").replace("=", ""))
    minToken = possibles[0][1]

    for j in range(len(possibles)):
        if len(possibles[j][0]) != base:
            allSame = False

        newLen = len(possibles[j][1].replace("/", "").replace("=", ""))
        if newLen < minLen:
            minLen = newLen
            minToken = possibles[j][1]
    if not(allSame):
        return False, []

    for j in range(len(possibles[0][0])):
        v = possibles[0][0][j][0]
        # possible lengths
        vLengths = set(map(lambda x: x[0][j], possibles))
        if (len(vLengths) > 1):
            lengthResult = generalUtils.VOWEL_LEN.UNKNOWN
            res.append(lengthResult)
        else:
            lengthResult = possibles[0][0][j]
            res.append(lengthResult)


    tokenWithDigamma = minToken
    return True, res, tokenWithDigamma

# given a word divided into phonemes and list of vowel lengths for the vowels
# in the word, return a string representation of the phoneme division
def buildPhonemeStringWithLengths(token, resultLengths):
    phonemes = splitStringIntoPhonemes(token).split(".")
    res = []
    vowelsSeen = 0
    for p in phonemes:
        # vowel, including diphthong
        if not(re.search(r'[aeiouhw]', p) == None):
            vowelResult = p + "[" + resultLengths[vowelsSeen] + "]"
            res.append(vowelResult)
            vowelsSeen += 1
        # consonant
        else:
            res.append(p)
    if (VERBOSE):
        if not(vowelsSeen == len(resultLengths)):
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            print "Vowel mismatch:"
            print token
            print resultLengths
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    return ".".join(res) + "."

# given an individual form, determine whether it is an enclitic
encliticLemmaRe = re.compile("^((tis)|(pou/(2)?)|(poqi)|(ph)|(poi)|(poqen)|(pote/(2)?)|(pw(2)?)|(pws)|(ge)|(te)|(toi(2)?)|(pe/r)|(qh/n))$")
encliticFormRe = re.compile("^((mou(=)?)|(moi/(/)?)|(me(/)?)|(sou(=)?)|(soi(/)?)|(se(/)?)|(e\((/)?)|(sfi(/)?si)|(meu(=)?)|(se/?o)|(seu=?)|(toi/?)|(te/)|(tu/)|(e\(/o)|(mi/?n)|(ni/?n)|(sfi/?)|(sfi/?n)|(sfwe/?)|(sfwi/?n)|(sfe/as)|(sfe/?a)|(nu/?n?)|(ke/?)|(ke/?n))$")
def isFormEnclitic(form):
    lemma = form["lemma"]
    form = form["form"]
    if not(re.search(encliticLemmaRe, lemma) == None):
        return True
    if lemma == "e(/" and (form == "ou(=" or form == "oi(=" or form == "e(/o" or form == "e(o" or form == "eu(=" or form == "eu(" or form == "e(/qen" or form == "e(qen"):
        return True
    if lemma == "sfei=s" and (form == "sfe/" or form == "sfe" or form == "sfe/wn" or form == "sfewn" or form == "sfa/s" or form == "sfa=s" or form == "sfas"):
        return True
    if lemma[0:-1] == "a)/ra" and (form == "r(a/" or form == "r(a"):
        return True
    if not(re.search(encliticFormRe, form) == None):
        return True
    if lemma == "ei)mi/" and "tense" in form and "mood" in form:
        tense = form["tense"]
        mood = form["mood"]
        if (tense == "pres" and mood == "ind" and not(form[0:3] == "ei)")):
            return True
    if lemma == "phmi/" and "tense" in form and "mood" in form:
        tense = form["tense"]
        mood = form["mood"]
        if (tense == "pres" and mood == "ind" and not(form == "ph/|s" or form == "ph=|s")):
            return True
    return False

# given an individual form, determine whether it is proclitic
procliticRe = re.compile("^((ei\)s)|(e\)k)|(e\)c)|(ei\))|(ei\)2)|(w\(s)|(ou\)([\d]+)?))$")
def isFormProclitic(form):
    lemma = form["lemma"]
    form = form["form"]
    if lemma == "o(" and (form[:1] == "o" or form[:1] == "h" or form[:2] == "ai"):
        return True
    if not(re.search(procliticRe, lemma) == None):
        return True
    return False

# given an individual form, determine whether it is an enclitic or proclitic
def getSingleFormCliticism(form):
    isEnclitic = False
    isProclitic = False
    if isFormEnclitic(form):
        isEnclitic = True
        if False and (not(form["feature"]) or not("enclitic" in form["feature"])):
            print "enclitic"
            print form
            print "---"
    if isFormProclitic(form):
        isProclitic = True
        if False and (not(form["feature"]) or not("proclitic" in form["feature"])):
            print "proclitic"
            print form
            print "---"
    return isEnclitic, isProclitic

# given a list of forms, return whether this is an enclitic or proclitic
def getCliticism(forms):
    if (len(forms) == 0):
        return False, False
    allEnclitic = True
    allProclitic = True
    for form in forms:
        isEnclitic, isProclitic = getSingleFormCliticism(form)
        if not(isEnclitic):
            allEnclitic = False
        if not(isProclitic):
            allProclitic = False
    return allEnclitic, allProclitic

# return true if all the lemmas match
def allLemmasMatch(forms, target):
    if (len(forms) == 0):
        return False

    allMatch = True
    for form in forms:
        if (form["lemma"] != target):
            allMatch = False
            break

    return allMatch

# special adjustments for a few odd words
def specialAdjustPhonemes(forms, phonemes):
    if (allLemmasMatch(forms, "*za/kunqos") or allLemmasMatch(forms, "*ze/leia")):
        return re.sub(r"^\.z", r".z[s]", phonemes)
    if (allLemmasMatch(forms, "ske/parnon") or allLemmasMatch(forms, "*skama/ndrios") or allLemmasMatch(forms, "*ska/mandros")):
        return re.sub(r"^\.s\.k", r".sk", phonemes)

    return phonemes



# given a token, plus form information and a dictionary, split the token into
# phonemes, (if approach is NATIVE_SPEAKER, then vowels are given their lengths.)
def getTokenPhonemes(token, formInfo, dictionary, approach):
    if (not(token == "")):
        #splitStringIntoPhonemes
        fixed = generalUtils.fixToken(token)
        #print token
        forms = formInfo[fixed]
        isEnclitic, isProclitic = getCliticism(forms)
        if (approach == APPROACH.NATIVE_SPEAKER):
            if (len(forms) > 0):
                possibleTokenVowelLengths = map(lambda x: getFormVowelLengths(fixed, x, dictionary), forms)
                success, resultLengths, resultToken = unifyPossibleTokenVowelLengths(possibleTokenVowelLengths)

                if not(success):
                    resultLengths = getDefaultLengths(fixed)
                    resultToken = token
            else:
                # just default to the basic setup
                resultLengths = getDefaultLengths(fixed)
                resultToken = token


            if False:
                print token
                print resultToken
                print "~~~~~"
            result = buildPhonemeStringWithLengths(resultToken, resultLengths)
            result = specialAdjustPhonemes(forms, result)
            #print result
            return result, isEnclitic, isProclitic
        else: # approach == APPROACH.STUDENT
            result = splitStringIntoPhonemes(token)
            result = specialAdjustPhonemes(forms, result)
            return result, isEnclitic, isProclitic

    else:
        return "", False, False

# given the text of a line, information about forms, a dictionary, and the
# approach taken (student or native speaker), divide the line into phonemes
def getPhonemes(lineText, formInfo, dictionary, approach):
    tokens = lineText.split(" ")
    resultLine = ""
    for token in tokens:
        tokenDivision, isEnclitic, isProclitic = getTokenPhonemes(token, formInfo, dictionary, approach)

        if isEnclitic and (len(resultLine) >= 1 and resultLine[-1] == " "):
            resultLine = resultLine[0:-1] + tokenDivision + ". "
        elif isProclitic:
            resultLine += tokenDivision + "."
        else:
            resultLine += tokenDivision + ". "

    # remove multiple splits
    line = re.sub(r'\.+', '.', resultLine)

    # remove final 2 characters, ". "
    line = line[:-2]


    # note that we have a . at the very start, ". ." for spaces.
    return line
    if False:
        if (approach == APPROACH.NATIVE_SPEAKER):
            tokens = lineText.split(" ")
            resultLine = ""
            for token in tokens:
                tokenDivision, isEnclitic, isProclitic = getTokenPhonemes(token, formInfo, dictionary)
                if isEnclitic and (resultLine[-1] == " "):
                    resultLine = resultLine[0:-1] + tokenDivision + ". "
                elif isProclitic:
                    resultLine += tokenDivision + "."
                else:
                    resultLine += tokenDivision + ". "
            # note: we mark divisions with a .

            lineText = re.sub(r'\s+', '. ', lineText)
            line = splitStringIntoPhonemes(lineText)
            print "l1:"
            print line


            # remove multiple splits
            line = re.sub(r'\.+', '.', resultLine)
            print "l2:"
            print line

            # note that we have a . at the very start, ". ." for spaces.
            return line
        else: # approach == APPROACH.STUDENT
            # note: we mark divisions with a .
            # collapse spaces
            lineText = re.sub(r'\s+', '. ', lineText)
            # split the string into phonemes
            line = splitStringIntoPhonemes(lineText)


            # note that we have a . at the very start, ". ." for spaces.
            return line


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Syllabification
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# return true if the sound is a consonant
def isConsonant(sound):
    match = re.match("[bgdzqklmncprstfxyv]", sound)
    # we could just return match, but I feel it is better style to return
    # True/False rather than an object/null
    if (match):
        return True
    else:
        return False

# given a list of sounds, divide them into groups of some number of consonants
# followed by a single vowel. This will allow easy conversion to syllables in
# a second pass
def getCVs(splitSounds):
    # first, attach all consonant sounds before a vowel sound to that vowel
    cvs = []
    current = CVObj()
    for i in range(len(splitSounds)):
        sound = splitSounds[i]
        if (sound == " "):
            # if the last vowel was followed by a space, mark it.
            if (len(cvs) > 0):
                cvs[-1].lastVowelInWord = True
                cvs[-1].pauseNext = True
                if (len(current.consonants) == 0):
                    cvs[-1].wordEndVowel = True
            continue
        elif isConsonant(sound):
            current.consonants.append(sound)
        else:
            # if this is a vowel, the previous character was a space, and the
            # one before that was a vowel, then we have vowel-sound, space,
            # vowel sound and would cause correption.
            if (i > 1 and splitSounds[i-1] == " " and not(isConsonant(splitSounds[i-2]))):
                cvs[-1].vowelSpaceVowel = True
            current.vowel = sound
            cvs.append(current)
            current = CVObj()
    # append final item
    cvs.append(current)

    if VERY_VERBOSE:
        s = ""
        for cv in cvs:
            s += cv.toString()
            s += "-"
        print "CV Split:"
        print s
    return cvs

# true if this is two consonants, one of which is a digamma
def digammaDoublet(consonants):
    return len(consonants) == 2 and (consonants[0] == "v" or consonants[1] == "v")

# given a list of consanant-vowel groupings, convert them into a list of
# syllables
def cvsToSyllables(cvs):
    syllables = []
    for i in range(len(cvs)):
        current = SyllableObj()
        cv = cvs[i]

        # if this is not the first cv and there is more than one consonant,
        # the first consonant was taken by the previous syllable, so
        # ignore it
        cvStartConsonants = []
        if (not(i == 0) and (len(cv.consonants) > 1) and not(digammaDoublet(cv.consonants))):
            cvStartConsonants = cv.consonants[1:]
        else:
            cvStartConsonants = cv.consonants

        # if this has no vowel and is the final syllable, just append
        # all of its consonants to the previous syllable
        if ((i == (len(cvs) - 1)) and (cv.vowel == "")):
            prev = syllables[-1]
            prev.endConsonant += "".join(cvStartConsonants)
            continue

        current.startConsonants = cvStartConsonants

        # grab the vowel and calculate coreVowel, which is the vowel sound
        # with no diacritics
        current.vowel = cv.vowel
        current.coreVowel = re.sub(r'[^aeiouhw]', '', cv.vowel)
        if not(re.search(r'\[[sl\?]\]', cv.vowel) == None):
            current.vowelInherentLength = re.sub(r'[^sl\?]', '', cv.vowel)
        current.vowelAccent = re.sub(r'[^=/\\]', '', cv.vowel)
        current.vowelBreathing = re.sub(r'[^\()]', '', cv.vowel)
        #print current.vowel + "; " + current.coreVowel + "; " + current.vowelAccent + "; " + current.vowelBreathing

        onlyDigammaNext = False
        # if the next cv exists and has multiple consonants, grab the first one
        if (i + 1 < len(cvs)):
            nextCV = cvs[i+1]
            newStart = ""
            if (len(nextCV.consonants) > 1):
                if (digammaDoublet(nextCV.consonants)):
                    newStart = nextCV.consonants[0]
                    current.closedByDigamma = True
                else:
                    current.endConsonant = nextCV.consonants[0]
                    newStart = nextCV.consonants[1]
            elif (len(nextCV.consonants) > 0):
                if (nextCV.consonants[0] == "v"):
                    onlyDigammaNext = True
                newStart = nextCV.consonants[0]
            # check if the next consonant is a double consonant
            if (len(newStart) > 0):
                current.doubleConsonantNext = (newStart[0] == "z") or (newStart[0] == "c") or (newStart[0] == "y")
                current.possibleShortZNext = (newStart[0:4] == "z[s]")
            # check if followed by mute+liquid
            if (len(nextCV.consonants) == 2):
                firstMute = not(re.match(r'[pbfkgxtdq]', nextCV.consonants[0]) == None)
                secondLiquid1 = not(re.match(r'[rl]', nextCV.consonants[1]) == None)
                # homer allegedly never uses n/m, so we separate that out for now;
                # perhaps a future setup can just store the combos used, e.g.
                # pr, pl, kn, and keep those as features;
                secondLiquid2 = not(re.match(r'[nm]', nextCV.consonants[1]) == None)
                current.muteLiquid1Next = firstMute and secondLiquid1
                current.muteLiquid2Next = firstMute and secondLiquid2
                current.muteLiquidNext = firstMute and (secondLiquid1 or secondLiquid2)


        current.wordEndVowel = cv.wordEndVowel
        current.lastVowelInWord = cv.lastVowelInWord
        current.pauseNext = cv.pauseNext
        if (onlyDigammaNext and cv.lastVowelInWord):
            current.vowelSpaceVowel = True
            current.hiatusByDigamma = True
        else:
            current.vowelSpaceVowel = cv.vowelSpaceVowel

        syllables.append(current)

    return syllables


# given a string containing the phonemes, a pass number, and the approach
# we are taking (student or native speaker), return the list of syllables
def getSyllables(phonemes, passNumber, approach):
    # syllabificate
    # split the sounds up; the first item will be empty, so ignore it
    splitSounds = phonemes.split(".")[1:]

    # divide the line into groupings of (0+ consonants), (1 vowel)
    cvs = getCVs(splitSounds)

    # get the list of syllables
    syllables = cvsToSyllables(cvs)

    return syllables

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Length Determination
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# make some second pass adjustments to the line to create a better guess
# for now, this is just word-terminal -e-w- -> -ew-
def secondPassAdjustments(syllables):
    newSyllables = []
    for i in range(len(syllables)):
        syl = syllables[i]
        # if this is a word terminal -w and the previous syllable was -???e-
        if (i > 0 and syllables[i].wordEndVowel and not(syllables[i-1].wordEndVowel) and syllables[i].coreVowel == "w" and len(syllables[i].startConsonants) == 0 and syllables[i-1].coreVowel == "e"):
            # overwrite the last syllable with a combined one
            combined = copy.deepcopy(syllables[i-1]);
            current = syllables[i]
            combined.doubleVowel = True
            combined.wordEndVowel = current.wordEndVowel
            combined.lastVowelInWord = current.lastVowelInWord
            combined.pauseNext = current.pauseNext
            combined.vowelSpaceVowel = current.vowelSpaceVowel
            combined.vowel += current.vowel
            combined.coreVowel += current.coreVowel
            combined.vowelInherentLength == "l"

            # if there might be correption, we don't know the quantity
            # if there is no correption, it is long
            if(current.vowelSpaceVowel):
                combined.length = SYL.UNKNOWN
            else:
                combined.length = SYL.LONG

            newSyllables[-1] = combined;
            # if this word ends with terminal -ewn genitive
        elif (i > 0 and not(syllables[i].wordEndVowel) and not(syllables[i-1].wordEndVowel) and syllables[i].coreVowel == "w" and len(syllables[i].startConsonants) == 0 and syllables[i-1].coreVowel == "e" and (syllables[i].endConsonant == "n" or (i < len(syllables) - 1 and (len(syllables[i+1].startConsonants) > 0) and syllables[i+1].startConsonants[0] == "n"))):
            # overwrite the last syllable with a combined one
            combined = copy.deepcopy(syllables[i-1]);
            current = syllables[i]
            combined.doubleVowel = True
            combined.wordEndVowel = current.wordEndVowel
            combined.lastVowelInWord = current.lastVowelInWord
            combined.pauseNext = current.pauseNext
            combined.vowelSpaceVowel = current.vowelSpaceVowel
            combined.vowel += current.vowel
            combined.coreVowel += current.coreVowel
            combined.vowelInherentLength == "l"

            combined.length = SYL.LONG

            newSyllables[-1] = combined;
        else:
            newSyllables.append(syl)
    return newSyllables

# in addition to second pass adjustments, also combine eoi into a single value
def fifthPassAdjustments(syllables):
    syllables = secondPassAdjustments(syllables)
    newSyllables = []
    for i in range(len(syllables)):
        syl = syllables[i]
        # if this is a word terminal -oi and the previous syllable was -???e-
        if (i > 0 and syllables[i].wordEndVowel and not(syllables[i-1].wordEndVowel) and syllables[i].coreVowel == "oi" and len(syllables[i].startConsonants) == 0 and syllables[i-1].coreVowel == "e"):
            # overwrite the last syllable with a combined one
            combined = copy.deepcopy(syllables[i-1]);
            current = syllables[i]
            combined.doubleVowel = True
            combined.wordEndVowel = current.wordEndVowel
            combined.lastVowelInWord = current.lastVowelInWord
            combined.pauseNext = current.pauseNext
            combined.vowelSpaceVowel = current.vowelSpaceVowel
            combined.vowel += current.vowel
            combined.coreVowel += current.coreVowel
            combined.vowelInherentLength == "l"

            # if there might be correption, we don't know the quantity
            # if there is no correption, it is long
            if(current.vowelSpaceVowel):
                combined.length = SYL.UNKNOWN
            else:
                combined.length = SYL.LONG

            newSyllables[-1] = combined;
        # if this is a word terminal -ea
        elif (i > 0 and syllables[i].wordEndVowel and not(syllables[i-1].wordEndVowel) and syllables[i].coreVowel == "a" and len(syllables[i].startConsonants) == 0 and syllables[i-1].coreVowel == "e"):
            # overwrite the last syllable with a combined one
            combined = copy.deepcopy(syllables[i-1]);
            current = syllables[i]
            combined.doubleVowel = True
            combined.wordEndVowel = current.wordEndVowel
            combined.lastVowelInWord = current.lastVowelInWord
            combined.pauseNext = current.pauseNext
            combined.vowelSpaceVowel = current.vowelSpaceVowel
            combined.vowel += current.vowel
            combined.coreVowel += current.coreVowel
            combined.vowelInherentLength == "l"

            # if there might be correption, we don't know the quantity
            # if there is no correption, it is long
            if(current.vowelSpaceVowel):
                combined.length = SYL.UNKNOWN
            else:
                combined.length = SYL.LONG

            newSyllables[-1] = combined;

        # if this is a word terminal -eas
        elif (i > 0 and not(syllables[i].wordEndVowel) and not(syllables[i-1].wordEndVowel) and syllables[i].coreVowel == "a" and len(syllables[i].startConsonants) == 0 and syllables[i-1].coreVowel == "e" and (syllables[i].endConsonant == "s" or (i < len(syllables) - 1 and (len(syllables[i+1].startConsonants) > 0) and syllables[i+1].startConsonants[0] == "s"))):
            # overwrite the last syllable with a combined one
            combined = copy.deepcopy(syllables[i-1]);
            current = syllables[i]
            combined.doubleVowel = True
            combined.wordEndVowel = current.wordEndVowel
            combined.lastVowelInWord = current.lastVowelInWord
            combined.pauseNext = current.pauseNext
            combined.vowelSpaceVowel = current.vowelSpaceVowel
            combined.vowel += current.vowel
            combined.coreVowel += current.coreVowel
            combined.vowelInherentLength == "l"

            combined.length = SYL.LONG

            newSyllables[-1] = combined;
        else:
            newSyllables.append(syl)
    return newSyllables

# return true if this is a long vowel or diphthong
def vowelLongOrDiphthong(syl, approach):
    # if the vowel is h, w, has a circumflex accent (=), it is long
    longVowel = (syl.vowelInherentLength == "l") or (syl.coreVowel == "h") or (syl.coreVowel == "w") or (syl.vowelAccent == "=")
    # if the vowel has multiple letters, it is a dipthong
    if (approach == APPROACH.NATIVE_SPEAKER):
        diphthong = (len(syl.coreVowel) > 1 and not(syl.vowelInherentLength == "?" or syl.vowelInherentLength == "s"))
    else:
        diphthong = (len(syl.coreVowel) > 1)

    return longVowel or diphthong

# given a list of syllables, information about lemmas and forms, the pass,
# and the approach (student or native speaker) give the syllables lengths
def giveSyllablesLengths(inputSyllables, lemmaInfo, formInfo, passNumber, approach):
    syllables = copy.deepcopy(inputSyllables)

    # calculate lengths
    for syl in syllables:
        # if the syllable has a final consonant or the next consonant is a
        # a double consonant (ξ, ζ, ψ), it is closed
        closed = not(syl.endConsonant == "") or (syl.doubleConsonantNext and not(syl.possibleShortZNext))
        isLongVowelOrDiphthong = vowelLongOrDiphthong(syl, approach)
        # if the vowel is a dipthong and is followed by a space, there is correption
        correption = (isLongVowelOrDiphthong) and syl.vowelSpaceVowel
        # if the vowel is e, o, TODO:~has an accute accent when before a word-ending short~, it is short
        vowelShort = (syl.vowelInherentLength == "s") or (syl.coreVowel == "e") or (syl.coreVowel == "o")

        # if the vowel is long or a dipthong (and there is no correption) or the syllable is closed, the syllable is long
        isLong = closed or ((isLongVowelOrDiphthong) and not(correption))
        # if the vowel is short and the syllable is not closed, the syllable is short
        isShort = not(closed) and vowelShort

        if (isLong):
            syl.length = SYL.LONG
        elif (isShort and (syl.possibleShortZNext or syl.closedByDigamma)):
            syl.length = SYL.UNKNOWN
        elif (isShort):
            syl.length = SYL.SHORT

    # print syllables
    if VERY_VERBOSE:
        print "Syllable Split:"
        print getSyllablesString(syllables)

    if (passNumber >= 5):
        return fifthPassAdjustments(syllables) # includes second pass stuff
    elif (passNumber == 2 or passNumber >= 4):
        return secondPassAdjustments(syllables)
    else:
        return syllables

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Scansion
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# determine if the syllables from start to end match the given foot type.
# if adjustMuteLiquids is true, collapse mute/liquid pairs from a double to
# single consonant.
# if ictusLengthening is true, allow the first syllable of a foot to be lengthened
# if it is at the end of a word (technically more common when a pause follows,
# but sometimes occurs with any word end)
def matchesFoot(syllables, start, end, footType, adjustMuteLiquids, ictusLengthening):
    if (end > len(syllables)):
        return False
    len1 = syllables[start].length
    footOneCorrect = (len1 == SYL.LONG) or (len1 == SYL.UNKNOWN)
    # apply ictus lengthening change
    if (ictusLengthening and not(footOneCorrect)):
        if(syllables[start].lastVowelInWord):
            footOneCorrect = True
            syllables[start].length = SYL.LONG
            syllables[start].ictusLengthened = True
    # a spondee is two syllables, both long
    if footType == FOOT.SPONDEE:
        rightSize = (end - start) == 2
        len2 = syllables[start+1].length
        footTwoCorrect = (len2 == SYL.LONG) or (len2 == SYL.UNKNOWN)
        return (rightSize and footOneCorrect and footTwoCorrect)
    # a dactyl is three syllables, long short short
    elif footType == FOOT.DACTYL:
        rightSize = (end - start) == 3
        len2 = syllables[start+1].length
        footTwoCorrect = (len2 == SYL.SHORT) or (len2 == SYL.UNKNOWN) or (adjustMuteLiquids and syllables[start+1].muteLiquidNext)
        len3 = syllables[start+2].length
        footThreeCorrect = (len3 == SYL.SHORT) or (len3 == SYL.UNKNOWN) or (adjustMuteLiquids and syllables[start+2].muteLiquidNext)
        return (rightSize and footOneCorrect and footTwoCorrect and footThreeCorrect)
    # the final foot is two syllables, a long and anything, and is at the end.
    elif footType == FOOT.FINAL:
        isEnd = end == len(syllables)
        rightSize = (end - start) == 2
        return (rightSize and footOneCorrect and isEnd)
    else:
        return False

# given a set of syllables, and index to start at, the foot
# we are currently examining, and the pass number (where later passes examine
# more unlikely possibilities) return a list of the order of feet
# for that given scansion and true if there is a valid scan, [], false
# otherwise.
def determineLengths(syllables, index, foot, passNum):
    # Final foot handling
    if (foot == 6):
        if (matchesFoot(syllables, index, index+2, FOOT.FINAL, False, False)):
            return [[FOOT.FINAL]], True
        else:
            if(passNum >= 2):
                if (matchesFoot(syllables, index, index+2, FOOT.FINAL, True, False)):
                    return [[FOOT.FINAL]], True
            if(passNum >= 3):
                if (matchesFoot(syllables, index, index+2, FOOT.FINAL, True, True)):
                    return [[FOOT.FINAL]], True
            return [], False


    results = []
    # guess dactyl
    if (matchesFoot(syllables, index, index+3, FOOT.DACTYL, False, False)):
        reses, correct = determineLengths(syllables, index+3, foot + 1, passNum)
        if (correct):
            for res in reses:
                res.insert(0, FOOT.DACTYL)
                results.append(res)
    # guess spondee
    if (matchesFoot(syllables, index, index+2, FOOT.SPONDEE, False, False)):
        reses, correct = determineLengths(syllables, index+2, foot + 1, passNum)
        if (correct):
            for res in reses:
                res.insert(0, FOOT.SPONDEE)
                results.append(res)
    # if on pass 2 and no results yet, try converting mute/liquids from
    # single to double syllables.
    if (passNum >= 2 and len(results) == 0):
        # guess dactyl
        if (matchesFoot(syllables, index, index+3, FOOT.DACTYL, True, False)):
            reses, correct = determineLengths(syllables, index+3, foot + 1, passNum)
            if (correct):
                for res in reses:
                    res.insert(0, FOOT.DACTYL)
                    results.append(res)
        # guess spondee
        if (matchesFoot(syllables, index, index+2, FOOT.SPONDEE, True, False)):
            reses, correct = determineLengths(syllables, index+2, foot + 1, passNum)
            if (correct):
                for res in reses:
                    res.insert(0, FOOT.SPONDEE)
                    results.append(res)
    # if on pass 3 and no results yet, allow ictus lengthening
    if (passNum >= 3 and len(results) == 0):
        # guess dactyl
        if (matchesFoot(syllables, index, index+3, FOOT.DACTYL, True, True)):
            reses, correct = determineLengths(syllables, index+3, foot + 1, passNum)
            if (correct):
                for res in reses:
                    res.insert(0, FOOT.DACTYL)
                    results.append(res)
        # guess spondee
        if (matchesFoot(syllables, index, index+2, FOOT.SPONDEE, True, True)):
            reses, correct = determineLengths(syllables, index+2, foot + 1, passNum)
            if (correct):
                for res in reses:
                    res.insert(0, FOOT.SPONDEE)
                    results.append(res)

    if (len(results) > 0):
        return results, True
    else:
        return [], False

# given a list of syllables without all lengths set, a set of the feet
# in the scansion of the line, and the pass number, fill out the lengths in
# the syllables and return a ScannedLine object
def createScannedLine(syllables, feet, passNum):
    index = 0;
    for foot in feet:
        if (foot == FOOT.DACTYL):
            syl0 = syllables[index]
            syl1 = syllables[index+1]
            syl2 = syllables[index+2]
            if (syl0.length == SYL.UNKNOWN):
                syl0.length = SYL.LONG
            if (syl1.length == SYL.UNKNOWN):
                syl1.length = SYL.SHORT
            if (syl2.length == SYL.UNKNOWN):
                syl2.length = SYL.SHORT
            if (passNum >= 2 and syl1.length == SYL.LONG and syl1.muteLiquidNext):
                syl1.length = SYL.SHORT
                syl2.startConsonants.insert(0, syl1.endConsonant)
                syl1.endConsonant = ""
            if (passNum >= 2 and syl2.length == SYL.LONG and syl2.muteLiquidNext and len(syllables) - 1 >= index + 3):
                syl2.length = SYL.SHORT
                syllables[index+3].startConsonants.insert(0, syl2.endConsonant)
                syl2.endConsonant = ""
            index += 3
        elif (foot == FOOT.SPONDEE or foot == FOOT.FINAL):
            syl0 = syllables[index]
            syl1 = syllables[index+1]
            if (syl0.length == SYL.UNKNOWN):
                syl0.length = SYL.LONG
            if (syl1.length == SYL.UNKNOWN):
                syl1.length = SYL.LONG
            index += 2
    return ScannedLine(syllables, feet)

# given a list of syllables, some of them with lengths, the pass,
# and the approach (student or native speaker), return a list of valid scans
def getScansions(syllablesWithLengths, passNumber, approach):
    (results, worked) = determineLengths(syllablesWithLengths, 0, 1, passNumber)
    # if there is one valid result, we want to fill out all the values for
    # syllable lengths
    if (len(results) >= 1):
        res = []
        for i in range(len(results)):
            res.append(createScannedLine(syllablesWithLengths, results[i], passNumber))
        return res
    else:
        return results

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Feature Extraction
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# extract whether each foot is a spondee or not
def extractSpondaicism(feet):
    # get features for feet
    feetFeatures = [];
    # we only care about first 5 feet
    for i in range(5):
        foot = feet[i]
        if (foot == FOOT.SPONDEE):
            feetFeatures.append(1)
        else:
            feetFeatures.append(0)
    #FOOT.DACTYL
    #FOOT.SPONDEE

    return feetFeatures


# TEST
#testArr = [
#    [FOOT.DACTYL, FOOT.DACTYL, FOOT.DACTYL, FOOT.DACTYL, FOOT.DACTYL],
#    [FOOT.DACTYL, FOOT.DACTYL, FOOT.DACTYL, FOOT.DACTYL, FOOT.SPONDEE],
#    [FOOT.SPONDEE, FOOT.DACTYL, FOOT.SPONDEE, FOOT.DACTYL, FOOT.SPONDEE],
#    [FOOT.SPONDEE, FOOT.SPONDEE, FOOT.DACTYL, FOOT.DACTYL, FOOT.SPONDEE],
#    [FOOT.SPONDEE, FOOT.SPONDEE, FOOT.DACTYL, FOOT.SPONDEE, FOOT.DACTYL],
#    [FOOT.DACTYL, FOOT.SPONDEE, FOOT.DACTYL, FOOT.SPONDEE, FOOT.SPONDEE],
#    [FOOT.SPONDEE, FOOT.SPONDEE, FOOT.DACTYL, FOOT.SPONDEE, FOOT.SPONDEE],
#    [FOOT.SPONDEE, FOOT.DACTYL, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE],
#    [FOOT.DACTYL, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.DACTYL],
#    [FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.DACTYL, FOOT.DACTYL],
#    [FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.DACTYL],
#    [FOOT.DACTYL, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE],
#    [FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE, FOOT.SPONDEE],
#]
#for i in range(len(testArr)):
#    test = testArr[i]
#    print test
#    print extractSpondeeRuns(test)

# extract spondee runs of various lengths;
def extractSpondeeRuns(feet):
    # two spondees, no other duplicates
    single_doubles = 0
    # SSDSS
    double_doubles = 0
    # three spondes in a row
    triples = 0
    # four spondees in a row
    quadruples = 0
    # five spondees in a row
    quintuples = 0

    feetString = ""
    for i in range(5):
        if (feet[i] == FOOT.SPONDEE):
            feetString += "S"
        else:
            feetString += "D"

    # double double
    if (feetString == "SSDSS"):
        double_doubles = 1
        return [single_doubles, double_doubles, triples, quadruples, quintuples]

    # quintuple
    if (feetString == "SSSSS"):
        quintuples = 1
        return [single_doubles, double_doubles, triples, quadruples, quintuples]

    # quadruple
    if (feetString[1:] == "SSSS" or feetString[0:4] == "SSSS"):
        quadruples = 1
        return [single_doubles, double_doubles, triples, quadruples, quintuples]


    # triple
    if (feetString[2:] == "SSS" or feetString[1:4] == "SSS" or feetString[0:3] == "SSS"):
        triples = 1
        return [single_doubles, double_doubles, triples, quadruples, quintuples]

    # double
    if (feetString[3:] == "SS" or feetString[2:4] == "SS" or feetString[1:3] == "SS" or feetString[0:2] == "SS"):
        single_doubles = 1
        return [single_doubles, double_doubles, triples, quadruples, quintuples]

    return [single_doubles, double_doubles, triples, quadruples, quintuples]


# return information about the caesurae and diaereses
#   for caesura, subcategories are
#   anyCaesura - 1 if there is any caesura in this foot
#   masculineCaesura - 1 if there is a masculine caesura in this foot
#   feminineCaesura - 1 if there is a feminine caesura in this foot
#   principalCaesura -
#      0 : after first syllable of third foot;
#      1 : after between two shorts in the third foot;
#      2 : after first syllable of fourth foot;
#
#   for diaeresis, it is just true/false for each bridge
def extractCaesuraeAndDiaereses(scannedLine):
    resultC = {}
    resultC["anyCaesura"] = []
    resultC["masculineCaesura"] = []
    resultC["feminineCaesura"] = []
    resultC["principalCaesura"] = -1

    resultD = []

    sylIndex = 0;

    # for each of first 5 feet
    for i in range(5):
        if scannedLine.feet[i] == FOOT.SPONDEE:
            thesis = scannedLine.syllables[sylIndex]
            arsis = scannedLine.syllables[sylIndex + 1]
            if (thesis.pauseNext):
                resultC["anyCaesura"].append(1)
                resultC["masculineCaesura"].append(1)
                resultC["feminineCaesura"].append(0)
            else:
                resultC["anyCaesura"].append(0)
                resultC["masculineCaesura"].append(0)
                resultC["feminineCaesura"].append(0)

            if (arsis.pauseNext):
                resultD.append(1)
            else:
                resultD.append(0)

            sylIndex += 2
        else:
            thesis = scannedLine.syllables[sylIndex]
            arsis1 = scannedLine.syllables[sylIndex + 1]
            arsis2 = scannedLine.syllables[sylIndex + 2]
            if (thesis.pauseNext and arsis1.pauseNext):
                resultC["anyCaesura"].append(1)
                resultC["masculineCaesura"].append(1)
                resultC["feminineCaesura"].append(1)
            elif (thesis.pauseNext):
                resultC["anyCaesura"].append(1)
                resultC["masculineCaesura"].append(1)
                resultC["feminineCaesura"].append(0)
            elif (arsis1.pauseNext):
                resultC["anyCaesura"].append(1)
                resultC["masculineCaesura"].append(0)
                resultC["feminineCaesura"].append(1)
            else:
                resultC["anyCaesura"].append(0)
                resultC["masculineCaesura"].append(0)
                resultC["feminineCaesura"].append(0)

            if (arsis2.pauseNext):
                resultD.append(1)
            else:
                resultD.append(0)
            sylIndex += 3

    # for 6th foot
    thesis = scannedLine.syllables[sylIndex]
    arsis = scannedLine.syllables[sylIndex + 1]
    if (thesis.pauseNext):
        resultC["anyCaesura"].append(1)
        resultC["masculineCaesura"].append(1)
        resultC["feminineCaesura"].append(0)
    else:
        resultC["anyCaesura"].append(0)
        resultC["masculineCaesura"].append(0)
        resultC["feminineCaesura"].append(0)


    # principal Caesura calculation
    #  0 : after first syllable of third foot;
    if (resultC["masculineCaesura"][2] == 1):
        resultC["principalCaesura"] = 0

    #  1 : after between two shorts in the third foot;
    elif (resultC["feminineCaesura"][2] == 1):
        resultC["principalCaesura"] = 1

    #  2 : after first syllable of fourth foot;
    elif (resultC["masculineCaesura"][3] == 1):
        resultC["principalCaesura"] = 2

    return (resultC, resultD)

# return the number of correption occurrences in this line
# and the number of times it could have occurred but didn't
def extractCorreptionCounts(scannedLine):
    happenedCount = 0
    didntCount = 0

    for i in range(len(scannedLine.syllables)):
        syl = scannedLine.syllables[i]
        # if there could have been correption, check the final result
        if (vowelLongOrDiphthong(syl, APPROACH.STUDENT) and syl.vowelSpaceVowel):
            if syl.length == SYL.LONG:
                didntCount += 1
            elif syl.length == SYL.SHORT:
                happenedCount += 1

    return [happenedCount, didntCount];

# return the number of times ictus lengthening happens
def extractIctusLengtheningCount(scannedLine):
    totalCount = 0
    spaceCount = 0
    noSpaceCount = 0


    for i in range(len(scannedLine.syllables)):
        syl = scannedLine.syllables[i]
        if (syl.ictusLengthened):
            totalCount += 1
            if (syl.pauseNext):
                spaceCount += 1
            else:
                noSpaceCount += 1
    return [totalCount, spaceCount, noSpaceCount]

# return the number of times mute+liquid as a single consonant happens vs
# doesn't happend
def extractMuteLiquidCounts(scannedLine):
    happenedCount = 0
    didntCount = 0

    happenedCount1 = 0
    didntCount1 = 0

    happenedCount2 = 0
    didntCount2 = 0

    for i in range(len(scannedLine.syllables)):
        syl = scannedLine.syllables[i]
        if (syl.muteLiquidNext):
            if syl.length == SYL.LONG:
                didntCount += 1
            elif syl.length == SYL.SHORT:
                happenedCount += 1
        if (syl.muteLiquid1Next):
            if syl.length == SYL.LONG:
                didntCount1 += 1
            elif syl.length == SYL.SHORT:
                happenedCount1 += 1
        if (syl.muteLiquid2Next):
            if syl.length == SYL.LONG:
                didntCount2 += 1
            elif syl.length == SYL.SHORT:
                happenedCount2 += 1

    return [[happenedCount, didntCount], [happenedCount1, didntCount1], [happenedCount2, didntCount2]];

# returns whether digammas were observed
def extractDigammaCounts(scannedLine):
    # closed syl only
    happenedCount1 = 0
    didntCount1 = 0

    #hiatus only
    happenedCount2 = 0
    didntCount2 = 0

    for i in range(len(scannedLine.syllables)):
        syl = scannedLine.syllables[i]
        if (syl.closedByDigamma):
            if syl.length == SYL.LONG:
                happenedCount1 += 1
            elif syl.length == SYL.SHORT:
                didntCount1 += 1
        if (syl.hiatusByDigamma):
            if syl.length == SYL.LONG:
                happenedCount2 += 1
            elif syl.length == SYL.SHORT:
                didntCount2 += 1

    happenedCount = happenedCount1 + happenedCount2
    didntCount = didntCount1 + didntCount2

    return [[happenedCount, didntCount], [happenedCount1, didntCount1], [happenedCount2, didntCount2]];


# extract whether the line follows each of Meyer's three laws
def extractMeyersLaws(scannedLine, caesurae, diaereses):
    firstLaw = 1
    secondLaw = 1
    thirdLaw = 1

    #1: Words which begin in the first foot do not end between the shorts of
    #   the second foot, or at the end of that foot

    # if a word from the first foot continues into the second foot
    # and does not end at the masculine caesurae
    if not(diaereses[0] == 1) and not(caesurae["masculineCaesura"][1] == 1):
        # if the word ends at the feminine caesura or end of line, it breaks
        # the rule
        if ((caesurae["feminineCaesura"][1] == 1) or (diaereses[1] == 1)):
            firstLaw = 0


    #2: disyllables scanning short-long are avoided immediately before the
    #   caesura
    principalCaesura = caesurae["principalCaesura"]

    # if we have a disyllable leading up to a caesura, with the word break
    # in the middle of two shorts in the previous foot, when we have a
    # disyllable (short, long) before the principal caesura and violated
    # meyer's second law

    # cannot happen if principalCaesura is feminine in third foot
    if principalCaesura == 0:
        if (caesurae["feminineCaesura"][1] == 1):
            secondLaw = 0
    elif principalCaesura == 2:
        if (caesurae["feminineCaesura"][2] == 1):
            secondLaw = 0

    #3: avoidance of word end following the third and simultaneously the fifth
    #   princeps (thesis of the foot)
    if ((caesurae["masculineCaesura"][2] == 1) and (caesurae["masculineCaesura"][4] == 1) and not(caesurae["anyCaesura"][3] == 1 or caesurae["feminineCaesura"][2] == 1 or diaereses[2] == 1 or diaereses[3] == 1)):
        thirdLaw = 0

    return [firstLaw, secondLaw, thirdLaw]


# extract features from a scanned line
def extractFeatures(scannedLine):
    # will ultimately have "feet",
    features = {}

    # whether each foot is spondaic
    features["feet"] = extractSpondaicism(scannedLine.feet)

    # spondaic runs per line
    features["spondeeRuns"] = extractSpondeeRuns(scannedLine.feet)

    # caesura and diaeresis information
    (c, d) = extractCaesuraeAndDiaereses(scannedLine)
    features["caesura"] = c
    features["diaeresis"] = d

    # presence of correption
    features["correptionCount"] = extractCorreptionCounts(scannedLine)

    # ictus lengthening
    features["ictusCount"] = extractIctusLengtheningCount(scannedLine)

    # mute liquid single syllable
    features["muteLiquidCount"] = extractMuteLiquidCounts(scannedLine)

    # digammaCount
    features["digammaCount"] = extractDigammaCounts(scannedLine)

    # apocape, syncope?? TODO

    # nu movable for meter TODO

    # meyer's 3 laws
    features["MeyersLaws"] = extractMeyersLaws(scannedLine, features["caesura"], features["diaeresis"])

    return features;


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Reporting Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# get the number of successfully scanned lines
def getSuccessRate(myResults):
    size = len(myResults)
    success = 0
    for i in range(size):
        myResult = myResults[i]
        if (myResult["Scan Result"] == 1):
            success += 1
    return success


# calculate and print the number of successfully scanned lines
def printSuccessRate(myResults):
    size = len(myResults)
    success = getSuccessRate(myResults)
    if (size == 0):
        print("Success on %d out of %d. (%.2f%%)" % (success, size, (0)))
    else:
        print("Success on %d out of %d. (%.2f%%)" % (success, size, (100.0*success/size)))

# print line-by-line results
# feetOnly is true if we only want to print the feet results; if we want the
# whole line result, it is false.
def printLineResults(myResults, feetOnly):
    size = len(myResults)
    for i in range(size):
        myLine = myResults[i]
        if (myLine["Scan Result"] == 1):
            if (feetOnly):
                print str(i) + ": Feet: " + ",".join(myLine["Obj"].feet)
            else:
                print str(i) + ": " + myLine["Obj"].toString()
        else:
            print str(i) + ": failed."

# print all of the feature results
def printFeatureResults(myResults):
    size = len(myResults)

    for i in range(size):
        myResult = myResults[i]
        if (myResult["Scan Result"] == 1):
            features = myResult["Features"]
            print features
            #feetFeatures = features["feet"]



# get the text-wide spondaicism features
def getSpondaicism(lineScansions):
    size = len(lineScansions)

    # result counting
    totalCount = 0
    feetTotalCount = [0, 0, 0, 0, 0]

    for i in range(size):
        lineScan = lineScansions[i]
        if (lineScan["Scan Result"] == 1):
            features = lineScan["Features"]
            feetFeatures = features["feet"]

            # total count
            totalCount += 1
            for j in range(5):
                feetTotalCount[j] += feetFeatures[j]

    return feetTotalCount

# get overall counts for spondaic runs
def getSpondaicRuns(lineScansions):
    size = len(lineScansions)

    # result counting

    # single double, double_doubles, triples, quadruples, and quintuples
    # respectively
    totalCounts = [0, 0, 0, 0, 0]

    for i in range(size):
        lineScan = lineScansions[i]
        if (lineScan["Scan Result"] == 1):
            features = lineScan["Features"]["spondeeRuns"]

            for j in range(5):
                totalCounts[j] += features[j]

    return totalCounts

# get overall counts for caesura information
def getCaesuraCounts(lineScansions):
    size = len(lineScansions)

    result = {}
    anyCaesuraTotal = [0, 0, 0, 0, 0, 0]
    masculineCaesuraTotal = [0, 0, 0, 0, 0, 0]
    feminineCaesuraTotal = [0, 0, 0, 0, 0, 0]
    principalCounts = [0, 0, 0]


    for i in range(size):
        lineScan = lineScansions[i]
        if (lineScan["Scan Result"] == 1):
            features = lineScan["Features"]["caesura"]

            for j in range(6):
                anyCaesuraTotal[j] += features["anyCaesura"][j]
                masculineCaesuraTotal[j] += features["masculineCaesura"][j]
                feminineCaesuraTotal[j] += features["feminineCaesura"][j]

            principal = features["principalCaesura"]
            if (principal >= 0):
                principalCounts[principal] += 1

    result["anyCaesura"] = anyCaesuraTotal
    result["masculineCaesura"] = masculineCaesuraTotal
    result["feminineCaesura"] = feminineCaesuraTotal
    result["principalCaesura"] = principalCounts
    return result

# get overall counts for diaeresis counts
def getDiaeresisCounts(lineScansions):
    size = len(lineScansions)

    # the five breaks between feet respectively
    totalCounts = [0, 0, 0, 0, 0]

    for i in range(size):
        lineScan = lineScansions[i]
        if (lineScan["Scan Result"] == 1):
            features = lineScan["Features"]["diaeresis"]

            for j in range(5):
                totalCounts[j] += features[j]

    return totalCounts

# get overall counts for correption
def getCorreption(lineScansions):
    size = len(lineScansions)

    totalCounts = [0, 0]

    for i in range(size):
        lineScan = lineScansions[i]
        if (lineScan["Scan Result"] == 1):
            features = lineScan["Features"]["correptionCount"]

            for j in range(2):
                totalCounts[j] += features[j]

    return totalCounts

# get overall counts for ictus lengthening
def getIctusLengthening(lineScansions):
    size = len(lineScansions)

    totalCount = 0
    spaceCount = 0
    noSpaceCount = 0

    for i in range(size):
        lineScan = lineScansions[i]
        if (lineScan["Scan Result"] == 1):
            counts = lineScan["Features"]["ictusCount"];
            totalCount += counts[0]
            spaceCount += counts[1]
            noSpaceCount += counts[2]

    return [totalCount, spaceCount, noSpaceCount]

# get overall counts for mute-liquid working as a single value
def getMuteLiquid(lineScansions):
    size = len(lineScansions)

    totalCounts = [[0, 0], [0, 0], [0, 0]]

    for i in range(size):
        lineScan = lineScansions[i]
        if (lineScan["Scan Result"] == 1):
            features = lineScan["Features"]["muteLiquidCount"]

            for j in range(len(features)):
                subCategory = features[j]
                for k in range(len(subCategory)):
                    totalCounts[j][k] += subCategory[k]

    return totalCounts

# get overall counts for digamma observance
def getDigamma(lineScansions):
    size = len(lineScansions)

    totalCounts = [[0, 0], [0, 0], [0, 0]]

    for i in range(size):
        lineScan = lineScansions[i]
        if (lineScan["Scan Result"] == 1):
            features = lineScan["Features"]["digammaCount"]

            for j in range(len(features)):
                subCategory = features[j]
                for k in range(len(subCategory)):
                    totalCounts[j][k] += subCategory[k]

    return totalCounts


# get overall counts for Meyer's laws
def getMeyersLaws(lineScansions):
    size = len(lineScansions)

    totalCounts = [0, 0, 0]

    for i in range(size):
        lineScan = lineScansions[i]
        if (lineScan["Scan Result"] == 1):
            features = lineScan["Features"]["MeyersLaws"]

            for j in range(3):
                totalCounts[j] += features[j]

    return totalCounts

# function for getting individual feature results for a single text, either
# the overall text or a single book
def getFeatureResultsSingleText(lineScansions, textName, subName):
    features = {"TextName": textName, "SubName": subName}
    features["NumLines"] = len(lineScansions)
    features["NumSuccessful"] = getSuccessRate(lineScansions)
    features["Spondaicism"] = getSpondaicism(lineScansions)
    features["SpondaicRuns"] = getSpondaicRuns(lineScansions)
    features["CaesuraCounts"] = getCaesuraCounts(lineScansions)
    features["DiaeresisCounts"] = getDiaeresisCounts(lineScansions)
    features["Correption"] = getCorreption(lineScansions)
    features["IctusLengthening"] = getIctusLengthening(lineScansions)
    features["MuteLiquid"] = getMuteLiquid(lineScansions)
    features["Digamma"] = getDigamma(lineScansions)
    features["MeyersLaws"] = getMeyersLaws(lineScansions)

    # digamma hiatus frequency; both how often it happens, how often it should TODO
    # overall apocape, syncope?? TODO
    # overall nu movable for meter? TODO

    return features



# given line-by-line results, generate overall feature results
# either per book or for the text as a whole.
def getFeatureResults(lineScansions, textName, divide_by_book):
    if(divide_by_book):
        numBooks = int(lineScansions[len(lineScansions)-1]["Line"]["book"])
        # from http://stackoverflow.com/questions/30293071/python-find-same-values-in-a-list-and-group-together-a-new-list
        bookScansions = [list(j) for i, j in groupby(lineScansions, lambda x: x["Line"]["book"])]
        result = []
        result.append(getFeatureResultsSingleText(lineScansions, textName, "Overall"))
        for i in range(numBooks):
            name = "Book " + str(i+1)
            result.append(getFeatureResultsSingleText(bookScansions[i], textName, name))

        return result #map(getFeatureResultsSingleText, book_scansions)
    else:
        return [getFeatureResultsSingleText(lineScansions, textName, "Overall")]

# write the feature results to an external file
def saveFeatureResults(featureResults, textName, approach):
    outFileName = generalUtils.getTextFeatureDataOdikonFn(textName, approach)
    generalUtils.safeWrite(outFileName, json.dumps(featureResults))


# report on all extracted features
def reportOnFeatures(featureResults):
    for i in range(len(featureResults)):
        result = featureResults[i]
        totalCount = result["NumSuccessful"]

        print "Feature Report For " + result["TextName"] + " " + result["SubName"]
        tab = "  "
        print tab + "Spondaicism:"
        for i in range(5):
            spondaic = result["Spondaicism"][i]
            if (totalCount == 0):
                print tab + tab + "Foot %d: %d/%d (%.2f%%)" % ((i+1), spondaic, totalCount, (0))
            else:
                print tab + tab + "Foot %d: %d/%d (%.2f%%)" % ((i+1), spondaic, totalCount, (100.0*spondaic/totalCount))


        print tab + "Spondaic Runs:"
        if (totalCount == 0):
            print tab + tab + "No Lines"
        else:
            names = ["Double", "Double Double", "Triple", "Quadruple", "Quintuple"]
            for i in range(5):
                sr = result["SpondaicRuns"][i]
                print tab + tab + "%s Spondees: %d/%d (%.2f%%)" % (names[i], sr, totalCount, (100.0*sr/totalCount))


        print tab + "Caesurae:"
        if (totalCount == 0):
            print tab + tab + "No Lines"
        else:
            print tab + tab + "Any Caesurae:"
            for i in range(6):
                ac = result["CaesuraCounts"]["anyCaesura"][i]
                print tab + tab + tab + "In foot %d: %d/%d (%.2f%%)" % (i+1, ac, totalCount, (100.0*ac/totalCount))

            print tab + tab + "Masculine Caesurae:"
            for i in range(6):
                mc = result["CaesuraCounts"]["masculineCaesura"][i]
                print tab + tab + tab + "In foot %d: %d/%d (%.2f%%)" % (i+1, mc, totalCount, (100.0*mc/totalCount))

            print tab + tab + "Feminine Caesurae:"
            for i in range(6):
                fc = result["CaesuraCounts"]["feminineCaesura"][i]
                print tab + tab + tab + "In foot %d: %d/%d (%.2f%%)" % (i+1, fc, totalCount, (100.0*fc/totalCount))

            print tab + tab + "Principal Caesurae:"
            names = ["Third Foot (Masculine)", "Third Foot (Feminine)", "Fourth Foot"]
            for i in range(3):
                pc = result["CaesuraCounts"]["principalCaesura"][i]
                print tab + tab + tab + "%s: %d/%d (%.2f%%)" % (names[i], pc, totalCount, (100.0*pc/totalCount))



        print tab + "Diaereses:"
        if (totalCount == 0):
            print tab + tab + "No Lines"
        else:
            for i in range(5):
                diaeresis = result["DiaeresisCounts"][i]
                print tab + tab + "Diaeresis between foot %d and %d: %d/%d (%.2f%%)" % (i+1, i+2, diaeresis, totalCount, (100.0*diaeresis/totalCount))


        print tab + "Correption:"
        if (totalCount == 0):
            print tab + tab + "No Lines"
        else:
            correptionHappened = result["Correption"][0]
            correptionMayHave = result["Correption"][1]
            total = correptionHappened + correptionMayHave
            if (total > 0):
                print tab + tab + "Correption happened in %d out of %d possible occurrences (%.2f%%)" % (correptionHappened, total, (100.0*correptionHappened/total))
            else:
                print tab + tab + "No instances of possible correption."

            print tab + tab + "Correption Per Line: %.2f" % (1.0*correptionHappened/totalCount)


        print tab + "Ictus Lengthening:"
        if (totalCount == 0):
            print tab + tab + "No Lines"
        else:
            il = result["IctusLengthening"]
            print tab + tab + "With following space: %d" % (il[1])
            print tab + tab + "With no following space: %d" % (il[2])
            print tab + tab + "Total: %d" % (il[0])
            print tab + tab + "Per Line: %.2f" % (1.0*il[0]/totalCount)

        muteLiquidList = ["", " (r/l)", " (m/n)"]
        for i in range(len(muteLiquidList)):
            mlType = muteLiquidList[i]
            print tab + "Mute + Liquid" + mlType + " as a single syllable:"
            if (totalCount == 0):
                print tab + tab + "No Lines"
            else:
                mlHappened = result["MuteLiquid"][i][0]
                mlMayHave = result["MuteLiquid"][i][1]
                total = mlHappened + mlMayHave
                if (total > 0):
                    print tab + tab + "Happened in %d out of %d possible occurrences (%.2f%%)" % (mlHappened, total, (100.0*mlHappened/total))
                else:
                    print tab + tab + "No instances of this feature."
                print tab + tab + "Per Line: %.2f" % (1.0*mlHappened/totalCount)

        digamList = ["Total", "Closed Syl", "Hiatus"]
        for i in range(len(digamList)):
            digamType = digamList[i]
            print tab + digamType + " digamma observance:"
            if (totalCount == 0):
                print tab + tab + "No Lines"
            else:
                digamHappened = result["Digamma"][i][0]
                digamMayHave = result["Digamma"][i][1]
                total = digamHappened + digamMayHave
                if (total > 0):
                    print tab + tab + "Happened in %d out of %d possible occurrences (%.2f%%)" % (digamHappened, total, (100.0*digamHappened/total))
                else:
                    print tab + tab + "No instances of this feature."
                print tab + tab + "Per Line: %.2f" % (1.0*digamHappened/totalCount)

        print tab + "Meyer's Laws:"
        if (totalCount == 0):
            print tab + tab + "No Lines"
        else:
            names = ["First", "Second", "Third"]
            for i in range(3):
                ml = result["MeyersLaws"][i]
                print tab + tab + "Meyer's %s Law: %d/%d (%.2f%%)" % (names[i], ml, totalCount, (100.0*ml/totalCount))


# number of spondaic runs of each type
# caesura counts overall; location of principal caesura overall;
# correption frequency
# digamma hiatus frequency; both how often it happens, how often it should TODO
# overall ictus lengthening
# overall mute liquid
# overall apocape, syncope?? TODO
# overall nu movable for meter? TODO
# counts for Meyer's laws of Alexandrian hexameter verse



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~ Scansion Comparisons
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# TODO: unify with stuff in process.py

# given a string like "--|--|-uu|--|-uu|-x", extract the feet as a list of
# DACTLY, SPONDEE, FINAL objects.
# returns success and the list of feet
def extractFeetFromString(s):
    split = s.split("|")
    if (len(split) != 6):
        return False, []
    feet = []
    for s in split:
        if (s == "--"):
            feet.append(FOOT.SPONDEE)
        elif (s == "-uu"):
            feet.append(FOOT.DACTYL)
        elif (s == "-x"):
            feet.append(FOOT.FINAL)
        else:
            return False, []
    #FOOT.DACTYL
    return True, feet

# takes a list of scansions, returns if they are all equal
def sameScansions(scansions):
    if (len(scansions) == 0):
        return True
    length = len(scansions[0])
    # make sure they all have the same length
    for scansion in scansions:
        if (not(len(scansion) == length)):
            return False

    # make sure they have the same feet
    for scansion in scansions:
        for i in range(length):
            baseFoot = scansions[0][i]
            myFoot = scansion[i]
            if (not(baseFoot == myFoot)):
                return False;

    return True

# given an old list of results, compare it to the scansion from another file
def compareScansions(oldResults):
    thesaurus_file = open("data/thesaurusComScansion/Book1.txt", 'r')
    thesaurus_contents = thesaurus_file.read()
    thesaurus_file.close()
    thesaurusResults = json.loads(thesaurus_contents)
    differ = 0
    for i in range(len(thesaurusResults)):
        linesMatch = False

        tLine = thesaurusResults[i]
        tRunSuccess = tLine["Scan Result"] == 1
        tFeetSuccess, tFeet = extractFeetFromString(tLine["Scan"])
        tSuccess = tRunSuccess and tFeetSuccess

        mLine = oldResults[i]
        mSuccess = mLine["Scan Result"] == 1
        mFeet = []
        if (mSuccess):
            mFeet = mLine["Obj"].feet



        s = "Line: %d.\n" % (i+1)
        # if both successfully grabbed a line
        if (tSuccess and mSuccess):
            if (sameScansions([tFeet, mFeet])):
                s += "  Same"
                linesMatch = True
            else:
                differ += 1
                s += "  Thesaurus: Scan: %s.\n" % ",".join(tFeet)
                s += "  Me       : Scan: %s.\n" % ",".join(mFeet)
        else:
            if (tSuccess):
                s += "  Thesaurus: Scan: %s.\n" % ",".join(tFeet)
            else:
                s += "  Thesaurus failed.\n"
            if (mSuccess):
                s += "  Me       : Scan: %s.\n" % ",".join(mFeet)
            else:
                s += "  Mine failed.\n"


        #s += "  Thesaurus: Success: %d. Scan: %s.\n" % (tLine["Scan Result"], ",".join(tFeet))
        #s += "  Me       : Success: %d." % mLine["Scan Result"]
        #if (mLine["Scan Result"] == 1):
        #    s += " Scan: %s." % ",".join(mLine["Obj"].feet)
        #s += "\n"
        if (not(linesMatch)):
            print s
    print "They differ on %d out of %d. (%.2f%%)" % (differ, len(thesaurusResults), (100.0*differ/len(thesaurusResults)))
