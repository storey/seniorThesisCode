# -*- coding: utf-8 -*-
# This file contains the list of rules, function testers for those rules, and
# test data for the rules.

import re
from ..shared import utils as generalUtils

DIALECT = generalUtils.DIALECT

# --- helper functions --

# Remove diacritics and past augments from a present or imperfect form
def presentStemPrune(form, tense):
    res = form
    if (tense == "imperf"):
        if (form[0:2] == "e)"):
            res = form[2:]
    return generalUtils.removeDiacritics(res)

# return true if this is an alpha contract
def isAContract(lemma):
    l = generalUtils.removeDiacritics(lemma)
    activeEnd = l[-2:]
    deponentEnd = l[-5:]
    return (activeEnd == "aw" or deponentEnd == "aomai")

# return true if lemma corresponds to a mi verb
def isMiVerb(lemma):
    # removes diacritics and digits from the text
    cleanForm = re.sub(r'\)|\(|/|=|\\|&|\+|\||\'|[\d]', '', lemma)
    if (cleanForm[-2:] == "mi"):
        return True
    return False

# return true if the tense uses secondary endings
def isSecondaryEndings(tense):
    return (tense == "imperf" or tense == "aor")

# return true if this parse is a participle whose feminine nominative would
# have a long h in attic
def isLongAPpl(formData):
    if (formData["pos"] == "part" and ("voice" in formData)):
        voice = formData["voice"]
        return (voice == "mp" or voice == "mid")

# return true if this parse is a participle whose feminine nominative would
# have a short a in attic
def isShortAPpl(formData):
    if (formData["pos"] == "part" and ("voice" in formData) and
      ("tense" in formData)):
        voice = formData["voice"]
        tense = formData["tense"]
        return ((voice == "pass" and tense == "aor") or voice == "act")

# return true if this lemma is not ei)mi/ or one of its compounds.
# we lose compounds of ei)=mi, "to go", as a casualty, but catching less
# is better than getting nothing.
def notEimi(lemma):
    cleanLemma = re.sub(r'[\d]', '', generalUtils.removeDiacritics(lemma))
    if (len(cleanLemma) > 4):
        end = cleanLemma[-4:]
    else:
        end = cleanLemma
    return (not(lemma == "ei)mi/") and not(end == "eimi"))


# return true if the character is a vowel
isVowelRegex = re.compile("[aeiouwh]")
def isVowel(c):
    if not((re.search(isVowelRegex, c)) == None):
        return True
    return False

#--------------------------------------------------



# takes two lists, the first of dialects whose features are shown by this
# token/rule pair and the second who definitely *do not* match this feature/rule
# pair.
# for each dialect slot, 1 is a positive match, 0 is agnostic, -1 is a negative
# match.
# for now, res[0] is Attic, res[1] is Doric
def getReturnResult(positiveDialects, negativeDialects):
    res = generalUtils.getNArray(generalUtils.NUM_DIALECTS, 0)
    if (positiveDialects[0] == DIALECT.ANY):
        return res
    for d in positiveDialects:
        res[d] = 1
    for d in negativeDialects:
        res[d] = -1
    return res



#--------------------------------------------------
# rule testers

# Attic-ionic e(/ws for lesbian a)=s, boeotian, west greek a(=s (Buck 41.4, pp. 37)
def Rule_SW_1(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "e(/ws"):
        if (form == "e(/ws"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        elif (form == "a(=s" or form == "a(/s"): #second from perseus
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        # lesbian a)=s is ignored

    return getReturnResult([DIALECT.ANY], [])

# Attic-Ionic lews, news, ilews for la_o/s, na_o/s, ilaos
# (Buck 41.4, pp. 37; Benner 77, pp. 364)
def Rule_SW_2(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "lao/s"):
        form_start = form[0:2]
        if (form_start == "le"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        elif (form_start == "la"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "nao/s"):
        form_start = form[0:2]
        if (form_start == "ne"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        elif (form_start == "na"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "i)/laos"):
        form_start = generalUtils.removeDiacritics(form)[0:3]
        if (form_start == "ile"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        elif (form_start == "ila"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])

    return getReturnResult([DIALECT.ANY], [])

# Attic-Ionic s/ss/tt alternations (Buck 82, pp. 70)
def Rule_SW_3(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "o(/sos"):
        form_start = generalUtils.removeDiacritics(form)[0:3]
        if (form_start == "oss"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "ott"): # boeotian
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        else: # o(s-; attic-ionic, Arcadian
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    if (lemma == "o(po/sos"):
        form_start = generalUtils.removeDiacritics(form)[0:5]
        if (form_start == "oposs"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "opott"): # boeotian
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        else: # o(pos-; attic-ionic, Arcadian
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    if (lemma == "me/sos"):
        form_start = generalUtils.removeDiacritics(form)[0:4]
        if (form_start == "mess"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "mett"): # boeotian
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        else: # mes-; attic-ionic, Arcadian
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])

    return getReturnResult([DIALECT.ANY], [])

# Attic-Ionic h(meis; ammes is aeolic (Buck 119.2, .5, pp. 98)
def Rule_SW_4(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (pos == "pron" and (lemma == "e)gw/" or lemma == "su/") and
      ("number" in formData) and ("case" in formData)):
        number = formData["number"]
        case = formData["case"]
        if (lemma == "e)gw/" and number == "pl"):
            if (case == "nom"):
                if (form == "h(mei=s"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "a)/mmes"): #form == "a(me/s" or - doric
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            if (case == "dat"):
                if (form == "h(mi=n"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "a)/mmin" or form == "a)/mmi"): #form == "a(mi/n" or - doric
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            if (case == "acc"):
                if (form == "h(me/as" or form == "h(ma=s"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "a)/mme"): # doric a(me/
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        if (lemma == "su/" and number == "pl"):
            if (case == "nom"):
                if (form == "u(mei=s"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "u)/mmes"): # doric u(me/s
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            if (case == "dat"):
                if (form == "u(mi=n"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "u)/mmin" or form == "u)/mmi"): # doric u(mi/n
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            if (case == "acc"):
                if (form == "u(me/as" or form == "u(ma=s"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "u)/mme"): # u(me/ doric
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Attic-Ionic ai) = ei) Buck (134.1, pp. 105)
def Rule_SW_5(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "ei)"):
        if (form == "ei)"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        if (form == "ai)"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "ei)/qe"):
        if (form == "ei)/qe"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        if (form == "ai)/qe"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "ai)/qe"):
        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Ionic h)/n for attic e)a_/n or a_)/n (Buck 134.1b, pp. 105)
def Rule_SW_6(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "e)a/n"):
        if (form == "h)/n"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    return getReturnResult([DIALECT.ANY], [])

# Particle a)/n (Buck 134.2, pp. 105)
def Rule_SW_7(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "a)/n"):
        if (form == "a)/n"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        # ke in lesbian, thessalian, cyprian; ka in west greek and boeotain
        if (form == "ka" or form == "ke"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Attic-Ionic e(/teros = a(/teros (Buck 13a, pp. 24)
def Rule_SW_8(info):
    formData = info[0]
    lemma = formData["lemma"]
    if (lemma == "a(/teros"):
        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "e(/teros"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    return getReturnResult([DIALECT.ANY], [])

# Attic-Ionic Dekomai = dexomai (Buck 66, pp. 60)
def Rule_SW_9(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "de/xomai" and ("tense" in formData)):
        tense = formData["tense"]
        if (tense == "pres" or tense == "imperf"):
            form_start = (presentStemPrune(form, tense))[0:3]
            if (form_start == "dex"):
                return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
            elif (form_start == "dek"):
                return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Attic-Ionic o)/numa = o)/noma (Buck 22c, pp. 27)
def Rule_SW_10(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "o)/noma"):
        form_start = generalUtils.removeDiacritics(form)[0:3]
        if (form_start == "ono"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        elif (form_start == "onu"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Ionic e)/neika for Attic e)/nika (Buck 144a, pp. 116)
def Rule_SW_11(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "fe/rw"):
        if("mood" in formData):
            mood = formData["mood"]
            if (not (mood == "inf" or mood == "imperat") and
              ("tense" in formData)):
                tense = formData["tense"]
                if (tense == "aor"):
                    form_start = generalUtils.removeDiacritics(form)[1:4]
                    if (form_start == "nei"): # either e- or h-neika
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])

    return getReturnResult([DIALECT.ANY], [])

# Pou, o(/pou, etc (Buck 132.1, pp. 102)
# subrule 1
def Rule_SW_12a(info):
    formData = info[0]
    lemma = formData["lemma"]
    if (lemma == "pou=" or lemma == "o(/pou" or lemma == "au)tou=" or
        lemma == "o(mou=" or lemma == "a(mou=" or lemma == "dh/pou"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])

    return getReturnResult([DIALECT.ANY], [])

# Pou, o(/pou, etc (Buck 132.2, pp. 102)
# subrule 2
def Rule_SW_12b(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "pei=2"):
        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "toutei/"):
        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "tau/th|"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    if (lemma == "thnei="):
        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "e)kei="):
        if (form == "thnei="):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        else:
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    if (lemma == "au)tei="):
        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "au)tou="):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    return getReturnResult([DIALECT.ANY], [])

# Pou, o(/pou, etc (Buck 132.1, pp. 102)
# subrule 9
def Rule_SW_12c(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "e)/nqen"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "e)/swqen"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "o(/qen"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "o(po/qen"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "po/qen"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "pro/sqen"):
        if (form == "pro/sqen"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        elif (form == "pro/sqa"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Pou, o(/pou, etc (Buck 132.1, pp. 102)
# subrule 11
def Rule_SW_12d(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "o(/te" or lemma == "o(/te2"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    if (lemma == "to/te"):
        if (form == "to/te"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        if (form == "to/ka"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "tote/" or lemma == "tote/2"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    if (lemma == "pote/" or lemma == "pote/2" or lemma == "po/te"):
        stripped_form = generalUtils.removeDiacritics(form)
        if (stripped_form == "pote"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        if (stripped_form == "poka"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    if (lemma == "o(po/te"):
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    return getReturnResult([DIALECT.ANY], [])

# Ionic ei for attic e (Buck 54, pp. 49)
def Rule_SW_13(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "ce/nos"):
        form_start = generalUtils.removeDiacritics(form)[0:3]
        if (form_start == "cen"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "cei"): # ionic
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "e)/natos"):
        form_start = generalUtils.removeDiacritics(form)[0:2]
        if (form_start == "en"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "ei"): # ionic
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "e(/neka"):
        form_start = generalUtils.removeDiacritics(form)[0:2]
        if (form_start == "en"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "ei"): # ionic
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "mo/nos"):
        form_start = generalUtils.removeDiacritics(form)[0:3]
        if (form_start == "mon"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "mou"): # ionic
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "ko/rh"):
        form_start = generalUtils.removeDiacritics(form)[0:3]
        if (form_start == "kor"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "kou"): # ionic
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "o(/ros"):
        form_start = generalUtils.removeDiacritics(form)[0:2]
        if (form_start == "or"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "ou"): # ionic
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "o(/los"): # common greek
        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    elif (lemma == "ou)=los"): # ionic
        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "i)/sos" and ("case" in formData and "number" in formData)):
        case = formData["case"]
        num = formData["number"]
        if (num == "sg" and (case == "nom" or case == "acc")):
            form_start = form[0:3]
            if (form_start == "i)/"): # common greek or ionic before long vowels;
                return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (form_start == "i)="): # ionic
                return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "deirh/"):
        form_start = generalUtils.removeDiacritics(form)[0:3]
        if (form_start == "der"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "dei"): # ionic
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    elif (lemma == "ou)do/s"): # ionic
        form_start = generalUtils.removeDiacritics(form)[0:2]
        if (form_start == "od"): # common greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        elif (form_start == "ou"): # ionic
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])

    return getReturnResult([DIALECT.ANY], [])


# Ionic, Homeric bo/lomai = bou/lomai (Buck 75.b, pp. 65)
def Rule_SW_14(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "bou/lomai"):
        form_start = generalUtils.removeDiacritics(form)[0:3]
        if (form_start == "bol"):
            return getReturnResult([DIALECT.IONIC, DIALECT.HOMERIC], [DIALECT.AEOLIC])
    return getReturnResult([DIALECT.ANY], [])

# Ionic i_(ros, i_)ros in addition to i(ero/s (Buck 13.1, pp. 24)
def Rule_SW_15(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "i(ero/s"):
        form_start = generalUtils.removeDiacritics(form)[0:2]
        if (form_start == "ie"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        elif (form_start == "ir"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        elif (form_start == "ia"):
            return getReturnResult([DIALECT.AEOLIC], [])
    return getReturnResult([DIALECT.ANY], [])


# Ionic kei=nos = ekei=nos (Buck 125.1, pp. 101)
def Rule_SW_16(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "e)kei=nos"):
        form_start = generalUtils.removeDiacritics(form)[0:2]
        if (form_start == "ke"):
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
        elif (form_start == "kh"):
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Ionic cuno/s = attic koinos (Buck 135.7, pp. 108)
def Rule_SW_17(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "su/n"):
        if (form[0] == "c"):
            return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
        else:
            return getReturnResult([DIALECT.IONIC, DIALECT.AEOLIC], [DIALECT.HOMERIC])
    elif (lemma == "cuno/s"): # Ionic, Homeric
        return getReturnResult([DIALECT.IONIC, DIALECT.HOMERIC], [DIALECT.AEOLIC])
    elif (lemma == "koino/s"): # common Greek
        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC, DIALECT.HOMERIC])
    return getReturnResult([DIALECT.ANY], [])


# Ionic kartero/s = attic kratero/s (Buck 49.2a, pp. 44)
def Rule_SW_18(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "kratero/s"):
        return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
    elif (lemma == "kartero/s"):
        return getReturnResult([DIALECT.IONIC, DIALECT.AEOLIC], [DIALECT.HOMERIC])

    return getReturnResult([DIALECT.ANY], [])

# dhmiourgo/s variants (Buck 167, pp. 133)
def Rule_SW_19(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "dhmiourgo/s"):
        formStart = generalUtils.removeDiacritics(form)[0:6]
        if (formStart == "dhmioe"): # Homeric
            return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
        if (formStart == "dhmior"): # Ionic
            return getReturnResult([DIALECT.IONIC], [DIALECT.HOMERIC, DIALECT.AEOLIC])

        # attic dhmiourgo/s


    return getReturnResult([DIALECT.ANY], [])

# Ionic e)qu/s = attic eu)qu/s (Buck glossary, pp. 361)
def Rule_SW_20(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "eu)qu/s"):
        formStart = generalUtils.removeDiacritics(form)[0:2]
        if (formStart == "eu"): # Common Greek
            return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        if (formStart == "iq"): # Ionic, Boetian
            return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    return getReturnResult([DIALECT.ANY], [])

# Aeolic i)/a for attic mi/a (Buck 114.I, pp. 94)
def Rule_SW_21(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "ei(=s"):
        gender = formData["gender"]
        if (gender == "fem"):
            formStart = generalUtils.removeDiacritics(form)[0:1]
            if (formStart == "m"): # mi/a Common Greek
                return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
            if (formStart == "i"): # i)/a Ionic, Boetian
                return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [DIALECT.IONIC])
    # should have mhdemi/a v. mhdei+/a;; oudemi/a v. oudei+/a, but Morpheus doesn't recognize
    return getReturnResult([DIALECT.ANY], [])

# Homeric forms of gonu, doru, zeus, naus (Benner 97, 98, 101, pp.  367-368)
def Rule_SW_22(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "go/nu"):
        start = generalUtils.removeDiacritics(form)[0:3]
        if (start == "gou"):
            return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
    if (lemma == "do/ru"):
        start = generalUtils.removeDiacritics(form)[0:3]
        if (start == "dou"):
            return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
    if (lemma == "*zeu/s"):
        start = generalUtils.removeDiacritics(form)[0:2]
        if (start == "zh"):
            return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
    if (lemma == "nau=s"):
        start = generalUtils.removeDiacritics(form)[0:2]
        if (start == "nh"):
            return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])

    return getReturnResult([DIALECT.ANY], [])

# Homeric Pollus/Polus (Benner 105-106, pp. 369-370)
def Rule_SW_23(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "polu/s"):
        start = generalUtils.removeDiacritics(form)[0:4]
        if (form == "pollo/s" or form == "pollo/n"):
            return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
        if (start == "pole"):
            return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])

    return getReturnResult([DIALECT.ANY], [])

# Homeric ptolis (Benner 104, pp. 369)
def Rule_SW_24(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "po/lis"):
        start = generalUtils.removeDiacritics(form)[0:2]
        if (start == "pt"):
            return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# return true if this form should be examined by rule NE_1a
def proper_NE_1a_lemma(formData, lem_extra):
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (lemma == "o(/s" or lemma == "o("):
        return True
    if (pos == "noun"):
        return (lem_extra == generalUtils.H_A_STEM or lem_extra == generalUtils.EIR_A_STEM)
    elif (pos == "adj" and lem_extra == generalUtils.ADJ_3_TERMINATION):
        if (False): # this only matters for Attic
            ier = generalUtils.removeDiacritics(lemma)[-3]
            is_ier = (ier == "e" or ier == "i" or ier == "r")
            return not(is_ier)
        return True
    elif (isLongAPpl(formData)):
        return True
    elif (lemma == "polu/s"):
        return True
    return False

# Attic-ionic h for a_; a_ stems (Ionic even after e, i, r) (Buck 8, pp. 21)
def Rule_NE_1a(info):
    formData = info[0]
    lemmaInfo = info[1]
    form = formData["form"]
    cleanForm = generalUtils.removeDiacritics(form)
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (proper_NE_1a_lemma(formData, lemmaInfo)
      and ("gender" in formData) and ("number" in formData)):
        gender = formData["gender"]
        number = formData["number"]
        if (gender == "fem" and number == "sg" and ("case" in formData)):
            case = formData["case"]
            if (case == "nom" or case == "voc"):
                if (cleanForm[-1:] == "h"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-1:] == "a"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (case == "gen"):
                if (cleanForm[-2:] == "hs"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-2:] == "as"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (case == "dat"):
                if (cleanForm[-2:] == "hi" or cleanForm[-1:] == "h"):
                    return getReturnResult([DIALECT.IONIC,], [DIALECT.AEOLIC])
                elif (cleanForm[-2:] == "ai" or cleanForm[-1:] == "a"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (case == "acc"):
                if (cleanForm[-2:] == "hn"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-2:] == "an"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Attic-ionic h for a_; a_ stems (Ionic even after e, i, r) (Buck 8, pp. 21)
def Rule_NE_1b(info):
    formData = info[0]
    lemmaInfo = info[1]
    form = formData["form"]
    cleanForm = generalUtils.removeDiacritics(form)
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (((pos == "noun" and (lemmaInfo == generalUtils.SHORT_A_STEM or lemmaInfo == generalUtils.EIR_SHORT_A_STEM)) or
      isShortAPpl(formData)) or (pos == "adj" and (lemmaInfo == generalUtils.ADJ_US
      or lemmaInfo == generalUtils.ADJ_EIS_ESSA)) and ("gender" in formData) and
      ("number" in formData)):
        gender = formData["gender"]
        number = formData["number"]
        if (gender == "fem" and number == "sg" and ("case" in formData)):
            case = formData["case"]
            if (case == "nom"):
                if (cleanForm[-1:] == "h"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
            if (case == "gen"):
                if (cleanForm[-2:] == "hs"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-2:] == "as"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (case == "dat"):
                if (cleanForm[-2:] == "hi" or cleanForm[-1:] == "h"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-1:] == "ai" or cleanForm[-1:] == "a"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (case == "acc"): #technically this is a stem alteration, but it fits here
                if (cleanForm[-2:] == "hn"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
    return getReturnResult([DIALECT.ANY], [])

# Genitive singular masculine alpha stems (Buck 41.4, pp. 37; Benner 65, pp. 363)
def Rule_NE_2(info):
    formData = info[0]
    lemmaInfo = info[1]
    form = formData["form"]
    cleanForm = generalUtils.removeDiacritics(form)
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (pos == "noun" and ((lemmaInfo == generalUtils.H_A_STEM or lemmaInfo == generalUtils.EIR_A_STEM)
      and ("gender" in formData) and ("number" in formData))):
        gender = formData["gender"]
        number = formData["number"]
        if (gender == "masc" and number == "sg" and ("case" in formData)):
            case = formData["case"]
            if (case == "nom"):
                if (cleanForm[-2:] == "hs"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-2:] == "as"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (case == "gen"):
                # cleanForm[-2:] == "ou") -  # attic
                if (cleanForm[-1:] == "w"): # ionic
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                if (cleanForm[-2:] == "ao"): # ionic
                    return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
                elif (cleanForm[-1:] == "a"): # West greek, Lesbian, Thessalian
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (case == "dat"):
                if (cleanForm[-2:] == "hi" or cleanForm[-1:] == "h"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-2:] == "ai" or cleanForm[-1:] == "a"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (case == "acc"):
                if (cleanForm[-2:] == "hn"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-2:] == "an"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Plural a_-stems, (Buck 41.4, pp. 37; Benner 65, pp. 363)
def Rule_NE_3(info):
    formData = info[0]
    lemmaInfo = info[1]
    form = formData["form"]
    cleanForm = generalUtils.removeDiacritics(form)
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (((pos == "noun" and (lemmaInfo == generalUtils.H_A_STEM or
      lemmaInfo == generalUtils.EIR_A_STEM or
      lemmaInfo == generalUtils.EIR_SHORT_A_STEM or
      lemmaInfo == generalUtils.SHORT_A_STEM)) or (pos == "adj" and
      (lemmaInfo == generalUtils.ADJ_3_TERMINATION or lemmaInfo == generalUtils.ADJ_US
       or lemmaInfo == generalUtils.ADJ_EIS_ESSA) and ("gender" in formData)
      and formData["gender"] == "fem") or (lemma == "o(/s") or
      (pos == "part" and ("gender" in formData) and formData["gender"] == "fem"))
      and ("case" in formData) and ("number" in formData)):
        number = formData["number"]
        case = formData["case"]
        if (case == "gen" and number == "pl"):
            if (form[-4:] == "a/wn"):
                return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [DIALECT.IONIC])
            elif (form[-3:] == "w=n" or cleanForm[-2:] == "wn"): # includes e/wn
                return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
            elif (form[-3:] == "a=n" or cleanForm[-2:] == "an"): #second cuz p. sux
                return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# For nouns ending in -eus (Buck 43, 111, pp. 41, 92; Benner 86, pp. 366)
def Rule_NE_4(info):
    formData = info[0]
    lemmaInfo = info[1]
    form = formData["form"]
    cleanForm = generalUtils.removeDiacritics(form)
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (pos == "noun" and lemmaInfo == generalUtils.W_STEM
      and ("case" in formData) and ("number" in formData)):
        number = formData["number"]
        case = formData["case"]
        if (number == "sg"):
            if (case == "gen"):
                # Attic only: if (cleanForm[-3:] == "ews"):
                if (cleanForm[-3:] == "eos"): # ionic, west greek
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
                elif (cleanForm[-3:] == "hos"): # aeolic, homer
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [DIALECT.IONIC])
            elif (case == "dat"):
                if (cleanForm[-2:] == "ei"): # ionic, west greek
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
                elif (cleanForm[-2:] == "hi"): # aeolic, homer
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [DIALECT.IONIC])
            elif (case == "acc"):
                if (cleanForm[-2:] == "ea"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
                elif (cleanForm[-2:] == "ha"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [DIALECT.IONIC])
                # -h= in doric
        elif (number == "pl"):
            # nom plural h=s is attic
            if (case == "nom"):
                if (cleanForm[-3:] == "eis"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.IONIC], [DIALECT.HOMERIC])
                elif (cleanForm[-3:] == "hes"):
                    return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
            elif (case == "gen"):
                if (cleanForm[-3:] == "ewn"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.IONIC], [DIALECT.HOMERIC])
                elif (cleanForm[-3:] == "hwn"):
                    return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
            elif (case == "acc"):
                if (cleanForm[-3:] == "eas"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.IONIC], [DIALECT.HOMERIC])
                elif (cleanForm[-3:] == "has"):
                    return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
    return getReturnResult([DIALECT.ANY], [])

# Singular endings of iota-stems; (Buck 109, pp. 91; Benner 103, pp. 369)
def Rule_NE_5(info):
    formData = info[0]
    lemmaInfo = info[1]
    form = formData["form"]
    cleanForm = generalUtils.removeDiacritics(form)
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (pos == "noun" and lemmaInfo == generalUtils.I_STEM
      and ("case" in formData) and ("number" in formData)):
        number = formData["number"]
        case = formData["case"]
        if (number == "sg"):
            if (case == "gen"):
                if (cleanForm[-3:] == "ews"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
                elif (cleanForm[-3:] == "ios"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [])
                elif (cleanForm[-3:] == "hos"):
                    return getReturnResult([DIALECT.HOMERIC], [])
            elif (case == "dat"):
                if (cleanForm[-2:] == "ei"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-1:] == "i"):
                    return getReturnResult([DIALECT.AEOLIC], [])
        elif (number == "pl"):
            if (case == "nom" or case == "voc"):
                if (cleanForm[-3:] == "eis"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
                elif (cleanForm[-3:] == "ies"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [])
                elif (cleanForm[-3:] == "hes"):
                    return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
            elif (case == "gen"):
                if (cleanForm[-3:] == "ewn"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-3:] == "iwn"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [])
            elif (case == "dat"):
                # this has to come first because "-esi" below woudl catch "-iesi"
                if (cleanForm[-3:] == "isi" or cleanForm[-4:] == "iesi"):
                    return getReturnResult([DIALECT.AEOLIC], [])
                elif (cleanForm[-3:] == "esi" or cleanForm[-4:] == "esin"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-5:] == "iessi" or cleanForm[-6:] == "iessin"):
                    return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
                #second from Pindar
            elif (case == "acc"):
                if (cleanForm[-3:] == "eis"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
                elif (cleanForm[-2:] == "is" or cleanForm[-3:] == "ias"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [])
                elif (cleanForm[-3:] == "has"):
                    return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])


# Homeric, Aeolic dative plural in -essi (Buck 107.3, pp. 89)
def Rule_NE_6(info):
    formData = info[0]
    lemmaInfo = info[1]
    form = formData["form"]
    cleanForm = generalUtils.removeDiacritics(form)
    lemma = formData["lemma"]
    if ("case" in formData and "number" in formData):
        case = formData["case"]
        number = formData["number"]
        if (number == "pl" and case == "dat"):
                if (cleanForm[-4:] == "essi" or cleanForm[-5:] == "essin"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Homeric second declension endings (Benner 73-74, pp. 364)
def Rule_NE_7(info):
    formData = info[0]
    lemmaInfo = info[1]
    form = formData["form"]
    cleanForm = generalUtils.removeDiacritics(form)
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (((pos == "noun" and lemmaInfo == generalUtils.O_STEM)
      or (pos == "adj" and (lemmaInfo == generalUtils.ADJ_3_TERMINATION or lemmaInfo == generalUtils.ADJ_2ND_DECL))
      or (pos == "part") or (lemma == "o(/s" or lemma == "o("))
      and ("number" in formData) and ("case" in formData)):
        number = formData["number"]
        case = formData["case"]
        if (number == "sg" and case == "gen"):
            if (cleanForm[-3:] == "oio" or cleanForm[-2:] == "oo"):
                return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
            elif (cleanForm[-2:] == "ou"):
                return getReturnResult([DIALECT.AEOLIC, DIALECT.IONIC], [DIALECT.HOMERIC])
        elif (number == "dual" and (case == "gen" or case == "dat")):
            if (cleanForm[-4:] == "oiin"):
                return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
            else:
                return getReturnResult([DIALECT.AEOLIC, DIALECT.IONIC], [DIALECT.HOMERIC])
        elif (number == "pl" and case == "dat"):
            if (cleanForm[-4:] == "oisi" or cleanForm[-5:] == "oisin"):
                return getReturnResult([DIALECT.HOMERIC], [DIALECT.AEOLIC, DIALECT.IONIC])
            elif (cleanForm[-3:] == "ois"):
                return getReturnResult([DIALECT.AEOLIC, DIALECT.IONIC], [DIALECT.HOMERIC])

    return getReturnResult([DIALECT.ANY], [])


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Ionic mi-verbs inflected like contracts (Buck 160, pp. 125)
def Rule_VE_1(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if (lemma == "di/dwmi"): #didoi=s, didoi=sqa, didoi=, didou=si
        if ("number" in formData and "person" in formData
          and "mood" in formData and "tense" in formData
          and "voice" in formData):
            number = formData["number"]
            person = formData["person"]
            mood = formData["mood"]
            tense = formData["tense"]
            voice = formData["voice"]
            if (number == "sg" and person == "2nd" and tense == "pres"
              and mood == "ind" and voice == "act"):
                if (form == "didoi=s" or form == "didoi=sqa"):
                    return getReturnResult([DIALECT.HOMERIC, DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "di/dws"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.HOMERIC, DIALECT.IONIC])
            if (number == "sg" and person == "3rd" and tense == "pres"
              and mood == "ind" and voice == "act"):
                if (form == "didoi="):
                    return getReturnResult([DIALECT.HOMERIC, DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "di/dwsi" or form == "di/dwsin"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.HOMERIC, DIALECT.IONIC])
            elif (number == "pl" and person == "3rd" and tense == "pres"
              and mood == "ind" and voice == "act"):
                if (form == "didou=si" or form == "didou=sin"):
                    return getReturnResult([DIALECT.HOMERIC, DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "dido/asi" or form == "dido/asin"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.HOMERIC, DIALECT.IONIC])
    elif (lemma == "ti/qhmi"): #tiqei=si (3pl), tiqei= (3sg)
        if ("number" in formData and "person" in formData
          and "mood" in formData and "tense" in formData
          and "voice" in formData):
            number = formData["number"]
            person = formData["person"]
            mood = formData["mood"]
            tense = formData["tense"]
            voice = formData["voice"]
            if (number == "sg" and person == "3rd" and tense == "pres"
              and mood == "ind" and voice == "act"):
                if (form == "tiqei="):
                    return getReturnResult([DIALECT.HOMERIC, DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "ti/qhsi" or form == "ti/qhsin"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.HOMERIC, DIALECT.IONIC])
            elif (number == "pl" and person == "3rd" and tense == "pres"
              and mood == "ind" and voice == "act"):
                if (form == "tiqei=si" or form == "tiqei=sin"):
                    return getReturnResult([DIALECT.HOMERIC, DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "tiqe/asi" or form == "tiqe/asin"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.HOMERIC, DIALECT.IONIC])
    elif (lemma == "i(/hmi"):
        if ("number" in formData and "person" in formData
          and "mood" in formData and "tense" in formData
          and "voice" in formData):
            number = formData["number"]
            person = formData["person"]
            mood = formData["mood"]
            tense = formData["tense"]
            voice = formData["voice"]
            if (number == "pl" and person == "3rd" and tense == "pres"
              and mood == "ind" and voice == "act"):
                if (form == "i(ei=si"):
                    return getReturnResult([DIALECT.HOMERIC, DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (form == "i(a=si"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.HOMERIC, DIALECT.IONIC])
    #generalUtils.removeDiacritics(
    return getReturnResult([DIALECT.ANY], [])



# Third plural middle (Buck 139.2, pp. 113)
def Rule_VE_2(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    if ("number" in formData and "person" in formData
      and "mood" in formData and "tense" in formData
      and "voice" in formData):
        number = formData["number"]
        person = formData["person"]
        mood = formData["mood"]
        tense = formData["tense"]
        voice = formData["voice"]
        if (number == "pl" and person == "3rd" and (voice == "mp" or voice == "mid" or voice == "pass")
          and (tense == "perf" or tense == "plup" or mood == "opt" or
          (isMiVerb(lemma) and (tense == "pres" or tense == "imperf")))):
            cleanForm = generalUtils.removeDiacritics(form)
            if (len(cleanForm) >= 5 and isVowel(cleanForm[-5])):
                if (cleanForm[-4:] == "atai"): # ionic only
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-4:] == "ntai"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            if (len(cleanForm) >= 4 and isVowel(cleanForm[-4])):
                if (cleanForm[-3:] == "ato"): # ionic only
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (cleanForm[-3:] == "nto"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])

    #generalUtils.removeDiacritics(
    return getReturnResult([DIALECT.ANY], [])

# Alpha Contract Endings (Buck 41.1, pp. 37);
# a + e -> a_ in Attic-Ionic, h in West Greek, Boetian, probably other Aeolic.
def Rule_VE_3(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (pos == "verb" and isAContract(lemma) and ("mood" in formData) and
      ("tense" in formData) and ("voice" in formData)):
        tense = formData["tense"]
        mood = formData["mood"]
        voice = formData["voice"]
        no_diacritics = generalUtils.removeDiacritics(form)
        oneEnd = no_diacritics[-1:]
        twoEnd = no_diacritics[-2:]
        threeEnd = no_diacritics[-3:]
        fourEnd = no_diacritics[-4:]
        if (tense == "pres" and (mood == "ind" or mood == "subj") and
          ("number" in formData) and ("person" in formData)):
            number = formData["number"]
            person = formData["person"]
            if (voice == "act"):
                if (number == "sg" and person == "2nd"):
                    myEnd = twoEnd
                    if (myEnd == "as"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "hs"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
                elif (number == "sg" and person == "3rd"):
                    myEnd = oneEnd
                    if (myEnd == "a"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "h"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
                elif (number == "pl" and person == "2nd"):
                    myEnd = threeEnd
                    if (myEnd == "ate"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "hte"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (voice == "mp"):
                if (number == "sg" and person == "2nd"):
                    myEnd = oneEnd
                    if (myEnd == "a"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "h"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
                elif (number == "sg" and person == "3rd"):
                    myEnd = fourEnd
                    if (myEnd == "atai"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "htai"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
                elif (number == "pl" and person == "2nd"):
                    myEnd = fourEnd
                    if (myEnd == "asqe"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "hsqe"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        if (tense == "imperf" and mood == "ind" and
          ("number" in formData) and ("person" in formData)):
            number = formData["number"]
            person = formData["person"]
            if (voice == "act"):
                if (number == "sg" and person == "2nd"):
                    myEnd = twoEnd
                    if (myEnd == "as"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "hs"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
                elif (number == "sg" and person == "3rd"):
                    myEnd = oneEnd
                    if (myEnd == "a"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "h"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
                elif (number == "pl" and person == "2nd"):
                    myEnd = threeEnd
                    if (myEnd == "ate"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "hte"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (voice == "mp"):
                if (number == "sg" and person == "3rd"):
                    myEnd = threeEnd
                    if (myEnd == "ato"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "hto"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
                elif (number == "pl" and person == "2nd"):
                    myEnd = fourEnd
                    if (myEnd == "asqe"):
                        return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                    elif (myEnd == "hsqe"):
                        return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
        if (tense == "pres" and mood == "inf"):
            if (voice == "act"):
                myEnd = twoEnd
                if (myEnd == "an"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (myEnd == "hn"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
            elif (voice == "mp"):
                myEnd = no_diacritics[-5:]
                if (myEnd == "asqai"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC])
                elif (myEnd == "hsqai"):
                    return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Third plural secondary of athematics (Buck 138.5, pp. 111)
def Rule_VE_4(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (pos == "verb" and isMiVerb(lemma) and notEimi(lemma)
      and ("mood" in formData)):
        mood = formData["mood"]
        if (not (mood == "inf" or mood == "imperat") and
          ("tense" in formData) and ("person" in formData) and
          ("number" in formData)):
            tense = formData["tense"]
            number = formData["number"]
            person = formData["person"]
            if (number == "pl" and person == "3rd" and isSecondaryEndings(tense)):
                f = generalUtils.removeDiacritics(form)
                if (f[-3:] == "san"):
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
                elif (not (f[-5:] == "ousin") and f[-1:] == "n"):
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [DIALECT.IONIC])
    return getReturnResult([DIALECT.ANY], [])

# Infinitives in -nai (Buck 154.1, pp. 122)
# See also Benner 137 (pp. 379) for Homeric.
def Rule_VE_5(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    pos = formData["pos"]
    if (pos == "verb" and isMiVerb(lemma) and ("mood" in formData) and
      ("voice" in formData)):
        voice = formData["voice"]
        mood = formData["mood"]
        if (mood == "inf"):
            end = generalUtils.removeDiacritics(form)[-3:]
            if (end == "nai"):
                longEnd = generalUtils.removeDiacritics(form)[-5:]
                if (longEnd == "menai"):
                    # Lesbian, Homeric
                    return getReturnResult([DIALECT.AEOLIC, DIALECT.HOMERIC], [DIALECT.IONIC])
                else:
                    # Attic-Ionic
                    return getReturnResult([DIALECT.IONIC], [DIALECT.AEOLIC, DIALECT.HOMERIC])
            elif (end == "men"):
                # Boeotian, Thessalian
                return getReturnResult([DIALECT.AEOLIC], [DIALECT.IONIC, DIALECT.HOMERIC])

    return getReturnResult([DIALECT.ANY], [])

# Homeric Verb Endings (Bennery 136, pp. 378; 137, pp. 379; 142, pp. 380-381)
def Rule_VE_6(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    pos = formData["pos"]
    cleanForm = generalUtils.removeDiacritics(form)

    if (pos == "verb" and "number" in formData and "person" in formData
      and "mood" in formData and "tense" in formData
      and "voice" in formData):
        number = formData["number"]
        person = formData["person"]
        mood = formData["mood"]
        tense = formData["tense"]
        voice = formData["voice"]
        if (number == "sg" and person == "1st" and mood == "subj"
          and voice == "act"): #subjunctives in -mi
            if (cleanForm[-2:] == "mi"):
                return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
        elif (number == "sg" and person == "2nd" and voice == "act"
          and not(isMiVerb(lemma) or lemma == "oi)=da")):
            if (cleanForm[-3:] == "sqa"):
                return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
        elif (number == "sg" and person == "3rd" and mood == "subj"
          and voice == "act"): # subjunctives in -si(n)
            if (cleanForm[-2:] == "si" or cleanForm[-3:] == "sin"):
                return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
        elif (tense == "aor" and number == "pl" and person == "3rd"
          and voice == "pass" and mood == "ind"):
            if (cleanForm[-2:] == "en"):
                return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
        elif (tense == "plup" and number == "sg" and mood == "ind"
          and voice == "act" ): #  and person == "3rd"
            if (person == "1st"):
                if (cleanForm[-2:] == "ea"):
                    return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
            elif (person == "3rd"):
                if (cleanForm[-3:] == "een" or cleanForm[-3:] == "ein" or cleanForm[-2:] == "ee" or cleanForm[-2:] == "ei"):
                    return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])
        elif (number == "pl" and person == "1st" and (voice == "mp" or voice == "mid" or voice == "pass")):
            if (cleanForm[-5:] == "mesqa"):
                return getReturnResult([DIALECT.HOMERIC], [DIALECT.IONIC, DIALECT.AEOLIC])


    return getReturnResult([DIALECT.ANY], [])


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Attic-Ionic Nu Movable (Buck 102, pp. 84)
def Rule_NM_1(info):
    formData = info[0]
    form = formData["form"]
    lemma = formData["lemma"]
    pos = formData["pos"]
    if ((pos == "noun" or pos == "adj" or pos == "part") and ("case" in formData) and ("number" in formData)):
        case = formData["case"]
        number = formData["number"]
        if (case == "dat" and number == "pl"):
            cleanForm = generalUtils.removeDiacritics(form)
            if (cleanForm[-3:] == "sin"):
                # this one can appear in non Attic/Ionic from an early time
                return getReturnResult([DIALECT.IONIC, DIALECT.HOMERIC], [])
    # these two are attic-ionic only
    if (pos == "verb" and ("mood" in formData)):
        mood = formData["mood"]
        if (not (mood == "inf" or mood == "imperat")  and
          ("person" in formData) and ("number" in formData)):
            number = formData["number"]
            person = formData["person"]
            cleanForm = generalUtils.removeDiacritics(form)
            if (person == "3rd" and number == "sg"):
                if (cleanForm[-2:] == "en"):
                    return getReturnResult([DIALECT.IONIC, DIALECT.HOMERIC], [DIALECT.AEOLIC])
            elif (person == "3rd" and number == "pl"):
                if (cleanForm[-3:] == "sin"):
                    return getReturnResult([DIALECT.IONIC, DIALECT.HOMERIC], [DIALECT.AEOLIC])
    return getReturnResult([DIALECT.ANY], [])


# list of rules. Each rule contains a function to test for that rule (defined
# above), a rule name, a shorthand for the rule, and a list of forms that
# the rule should categorize as Attic/Doric/Either.

rulesList = [
{"Tester": Rule_SW_1, "ruleName": "SW.1: a(=s = e(/ws", "Short_Name": "SW.1",
  "Test_Forms": {
    DIALECT.IONIC: [["e(/ws", -1]],
    DIALECT.AEOLIC: [["a(=s", -1], ["a(/s", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_2, "ruleName": "SW.2: -aos vs -ews", "Short_Name": "SW.2",
  "Test_Forms": {
    DIALECT.IONIC: [["lew/s", -1], ["i(/lews", -1], ["new/s", -1], ["i(/lew|", -1], ["i(/lews", -1]],
    DIALECT.AEOLIC: [["laou=", -1], ["lao/s", -1], ["nao/s", -1], ["naou=", -1], ["i(/laos", -1], ["i(/laon", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_3, "ruleName": "SW.3: S/SS/TT variants", "Short_Name": "SW.3",
  "Test_Forms": {
    DIALECT.IONIC: [["o(/sos", -1], ["o(/sou", -1], ["o(po/sos", -1], ["o(po/sw|", -1], ["me/sos", -1], ["me/son", -1]],
    DIALECT.AEOLIC: [["o(/ssos", -1], ["o(/ssou", -1], ["o(po/ssos", -1], ["o(po/ssw", -1], ["me/ssos", -1], ["me/sson", -1], ["o(/ttos", -1], ["o(po/ttos", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_4, "ruleName": "SW.4: Forms of the plural personal pronoun", "Short_Name": "SW.4",
  "Test_Forms": {
    DIALECT.IONIC: [["h(mei=s", -1], ["h(mi=n", -1], ["h(me/as", -1], ["h(ma=s", -1], ["u(mei=s", -1], ["u(mi=n", -1], ["u(me/as", -1], ["u(ma=s", -1]],
    DIALECT.AEOLIC: [["a)/mmes", -1], ["a)/mmin", -1], ["a)/mme", -1], ["u)/mmes", -1], ["u)/mmin", -1], ["u)/mme", -1], ["a)/mmi", -1], ["u)/mmi", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["e)gw/", -1], ["su/", -1]]
  }
},
{"Tester": Rule_SW_5, "ruleName": "SW.5: The conjunction ei)", "Short_Name": "SW.5",
  "Test_Forms": {
    DIALECT.IONIC: [["ei)", -1], ["ei)/qe", -1]],
    DIALECT.AEOLIC: [["ai)", -1], ["ai)/qe", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_6, "ruleName": "SW.6: The particle e)a_/n", "Short_Name": "SW.6",
  "Test_Forms": {
    DIALECT.IONIC: [["h)/n", -1]],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_7, "ruleName": "SW.7: The particle a)/n", "Short_Name": "SW.7",
  "Test_Forms": {
    DIALECT.IONIC: [["a)/n", -1]],
    DIALECT.AEOLIC: [["ka", -1], ["ke", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY:  [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_8, "ruleName": "SW.8: a(/teros = e(/teros", "Short_Name": "SW.8",
  "Test_Forms": {
    DIALECT.IONIC: [["e(/teros", -1], ["e(/teron", -1]],
    DIALECT.AEOLIC: [["a(/teros", -1], ["a(/teron", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_9, "ruleName": "SW.9: de/komai = de/xomai", "Short_Name": "SW.9",
  "Test_Forms": {
    DIALECT.IONIC: [["de/xomai", -1], ["e)de/xeto", -1]],
    DIALECT.AEOLIC: [["de/komai", -1], ["e)de/keto", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_10, "ruleName": "SW.10: o)/numa = o)/nomai", "Short_Name": "SW.10",
  "Test_Forms": {
    DIALECT.IONIC: [["o)/noma", -1], ["o)no/mata", -1]],
    DIALECT.AEOLIC: [["o)/numa", -1]] ,
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_11, "ruleName": "SW.11: Forms of e)/nika", "Short_Name": "SW.11",
  "Test_Forms": {
    DIALECT.IONIC: [["e)/neika", -1], ["h)/neika", -1], ["h)/neikan", -1]],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_12a, "ruleName": "SW.12a: Adverbs ending in -ou", "Short_Name": "SW.12a",
  "Test_Forms": {
    DIALECT.IONIC: [["pou=", -1], ["o(/pou", -1], ["au)tou=", -1], ["o(mou=", -1], ["a(mou=", -1], ["dh/pou", -1]],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_12b, "ruleName": "SW.12b: Adverbs ending in -ei", "Short_Name": "SW.12b",
  "Test_Forms": {
    DIALECT.IONIC: [["tau/th|", -1], ["e)kei=", -1], ["au)tou=", -1]],
    DIALECT.AEOLIC: [["pei=", -1], ["toutei/", -1], ["thnei=", -1], ["au)tei=", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_12c, "ruleName": "SW.12c: Adverbs ending in -qen", "Short_Name": "SW.12c",
  "Test_Forms": {
    DIALECT.IONIC: [["e)/nqen", -1], ["e)/swqen", -1], ["o(/qen", -1], ["o(po/qen", -1], ["po/qen", -1], ["pro/sqen", -1]],
    DIALECT.AEOLIC: [["pro/sqa", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY:  [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_12d, "ruleName": "SW.12d: Adverbs ending in -ka vs -te", "Short_Name": "SW.12d",
  "Test_Forms": {
    DIALECT.IONIC: [["to/te", -1], ["tote/", -1], ["po/te", -1], ["pote/", -1], ["o(po/te", -1]],
    DIALECT.AEOLIC: [["to/ka", -1], ["po/ka", -1], ["poka/", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY:  [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_13, "ruleName": "SW.13: Ionic -ei- for attic -e-", "Short_Name": "SW.13",
  "Test_Forms": {
    DIALECT.IONIC: [["cei=nos", -1], ["cei=non", -1], ["ei)/natos", -1], ["ei)/naton", -1], ["ei(/neka", -1], ["mou=nos", -1], ["mou=non", -1], ["ou)=ros", -1], ["ou)=ron", -1], ["ou)=los", -1], ["i)=sos", -1], ["i)=son", -1], ["dei/rh", -1], ["deirh/n", -1], ["ou)do/s", -1], ["ou)do/n", -1]],
    DIALECT.AEOLIC: [["ce/nos", -1], ["ce/non", -1], ["e)/natos", -1], ["e)/naton", -1], ["e(/neka", -1], ["mo/nos", -1], ["mo/non", -1], ["o(/ros", -1], ["o(/ron", -1], ["o(/los", -1], ["o(/lou", -1], ["i)/sos", -1], ["i)/son", -1], ["de/ra", -1], ["de/ran", -1], ["o)do/s", -1], ["o)do/n", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["i)/sou", -1]]
  }
},
{"Tester": Rule_SW_14, "ruleName": "SW.14: dei/lomai = bou/lomai", "Short_Name": "SW.14",
  "Test_Forms": {
    DIALECT.IONIC: [["bo/lomai", -1], ["bo/letai", -1]],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [["bo/lomai", -1], ["bo/letai", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["bou/lomai", -1], ["bou/letai", -1]]
  }
},
{"Tester": Rule_SW_15, "ruleName": "SW.15: i(aro/s = i(ero/s", "Short_Name": "SW.15",
  "Test_Forms": {
    DIALECT.IONIC: [["i(ero/s", -1], ["i(erou=", -1], ["i(eroi/", -1], ["i(ro/s", -1], ["i(=ros", -1], ["i(rou=", -1]],
    DIALECT.AEOLIC: [["i(aro/s", -1], ["i(arou=", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_16, "ruleName": "SW.16: Forms of ekei=nos", "Short_Name": "SW.16",
  "Test_Forms": {
    DIALECT.IONIC: [["kei=nos", -1], ["kei=non", -1]],
    DIALECT.AEOLIC: [["kh=nos", -1], ["kh=non", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["e)kei=nos", -1], ["e)kei=non", -1]]
  }
},
{"Tester": Rule_SW_17, "ruleName": "SW.17: Forms of koinos", "Short_Name": "SW.17",
  "Test_Forms": {
    DIALECT.IONIC: [["su/n", -1], ["cuno/s", -1], ["cunou=", -1]],
    DIALECT.AEOLIC: [["su/n", -1], ["koino/s", -1], ["koinou=", -1]],
    DIALECT.HOMERIC: [["cu/n", -1], ["cuno/s", -1], ["cunou=", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_18, "ruleName": "SW.18: Forms of kratero/s", "Short_Name": "SW.18",
  "Test_Forms": {
    DIALECT.IONIC: [["kartero/s", -1], ["karterou=", -1]],
    DIALECT.AEOLIC: [["kartero/s", -1], ["karterou=", -1]],
    DIALECT.HOMERIC: [["kratero/s", -1], ["kraterou=", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_19, "ruleName": "SW.19: Forms of dhmiourgo/s", "Short_Name": "SW.19",
  "Test_Forms": {
    DIALECT.IONIC: [["dhmiorgo/s", -1]],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [["dhmioergo/s", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_20, "ruleName": "SW.20: Forms of eu)qu/s", "Short_Name": "SW.20",
  "Test_Forms": {
    DIALECT.IONIC: [["i)qu/s", -1], ["i)qei=a", -1]],
    DIALECT.AEOLIC: [["eu)qu/s", -1], ["eu)qei=a", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_SW_21, "ruleName": "SW.21: Forms of mi/a", "Short_Name": "SW.21",
  "Test_Forms": {
    DIALECT.IONIC: [["mi/a", -1], ["mia=s", -1]],
    DIALECT.AEOLIC: [["i)/a", -1], ["i)a/s", -1]],
    DIALECT.HOMERIC: [["i)/a", -1], ["i)a/s", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["ei(=s", -1]]
  }
},
{"Tester": Rule_SW_22, "ruleName": "SW.22: Homeric forms of gonu, doru, zeus, naus", "Short_Name": "SW.22",
  "Test_Forms": {
    DIALECT.IONIC: [],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [["gouno/s", -1], ["gou/natos", -1], ["douro/s", -1], ["dou/ratos", -1], ["douri/", -1], ["dou/rati", -1], ["dou=re", -1], ["dou=ra", -1], ["dou/rata", -1], ["dou/rwn", -1], ["dou/ressi", -1], ["dou/rasi", -1], ["zhno/s", -1], ["zhni/", -1], ["zh=na", -1], ["nhu=s", -1], ["nho/s", -1], ["nhi/", -1], ["nh=a", -1], ["nh=es", -1], ["nhw=n", -1], ["nh/essi", -1], ["nhusi/", -1], ["nh=as", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["go/nu", -1], ["do/ru", -1], ["zeu/s", -1], ["dio/s", -1], ["dii/", -1], ["di/a", -1], ["zeu=", -1], ["neo/s", -1], ["ne/es", -1], ["new=n", -1], ["ne/as", -1]]
  }
},
{"Tester": Rule_SW_23, "ruleName": "SW.23: Homeric forms of polus", "Short_Name": "SW.23",
  "Test_Forms": {
    DIALECT.IONIC: [],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [["pollo/s", -1], ["pole/os", -1], ["pole/wn", -1], ["pole/essin", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["pollh=s", -1], ["polloi/", -1], ["pollw=|", -1], ["polu/s", -1]]
  }
},
{"Tester": Rule_SW_24, "ruleName": "SW.24: Homeric ptolis", "Short_Name": "SW.24",
  "Test_Forms": {
    DIALECT.IONIC: [],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [["pto/lis", -1], ["pto/lios", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_NE_1a, "ruleName": "NE.1a: Endings of singular feminine long alpha-stems", "Short_Name": "NE.1a",
  "Test_Forms": {
    DIALECT.IONIC: [["gnw/mh", -1], ["gnw/mhs", -1], ["gnw/mh|", -1], ["gnw/mhn", -1], ["paideuome/nh", -1], ["paideuome/nhs", -1], ["pepaideume/nh", -1], ["pepaideume/nhs", -1], ["h(=s", -1], ["h(/n", -1], ["a)gorh/n", -1], ["a)pria/thn", -1], ["au)dh/", -1], ["au)th/", -1], ["bi/hn", -1], ["boulh/", -1], ["canqh=s", -1], ["daimoni/h", -1], ["deciterh=|", -1], ["deinh/", -1], ["duwdeka/th", -1], ["e)i+/shs", -1], ["fa/nh", -1], ["fare/trhn", -1], ["fi/lh", -1], ["fqi/hn", -1], ["h)eri/h", -1], ["h)gaqe/h|", -1], ["i)/dh|", -1], ["kalh=|", -1], ["klaggh/", -1], ["klisi/hn", -1], ["kou/rhn", -1], ["kouridi/hs", -1], ["kradi/hn", -1], ["o)mi/xlh", -1], ["oi)/h", -1], ["au)dh/", 2], ["au)dh/", 3], ["i)/dh|", 5], ["oi)/h", 2]],
    DIALECT.AEOLIC: [["gnw/ma", -1], ["gnw/mas", -1], ["gnw/ma|", -1], ["gnw/man", -1], ["pepaideume/na", -1], ["pepaideume/nas", -1], ["a(=s", -1], ["a(/n", -1], ["a)ci/a", -1], ["do/menai", 2], ["polla/", 0]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["h)rige/neia", 0]]
  }
},
{"Tester": Rule_NE_1b, "ruleName": "NE.1b: Endings of singular feminine short alpha-stems", "Short_Name": "NE.1b",
  "Test_Forms": {
    DIALECT.IONIC: [["qala/tths", -1], ["qala/tth|", -1], ["paideuou/shs", -1], ["a)naidei/hn", -1], ["kni/shs", -1], ["kni/sh", -1], ["kni/sh|", -1], ["barei/hs", -1]],
    DIALECT.AEOLIC: [["qala/ssas", -1], ["qala/ssa|", -1], ["gefu/ras", -1], ["telhe/ssas", 1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["qa/latta", -1], ["qa/lattan", -1], ["paideuqei=sa", -1]]
  }
},
{"Tester": Rule_NE_2, "ruleName": "NE.2: Singulars of masculine alpha stems", "Short_Name": "NE.2",
  "Test_Forms": {
    DIALECT.IONIC: [["poli/ths", -1], ["poli/tew", -1], ["poli/tw", -1], ["poli/thi", -1], ["poli/thn", -1], ["neani/hs", -1], ["ai)xmhth/n", -1], ["ba/thn", -1], ["i)/thn", -1], ["kradi/hn", 1]],
    DIALECT.AEOLIC: [["poli/tas", -1], ["poli/ta=", -1], ["poli=tai", -1], ["polita=n", -1], ["neani/as", -1]],
    DIALECT.HOMERIC: [["poli/tao", -1], ["neani/a=o", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_NE_3, "ruleName": "NE.3: Plurals of alpha stems", "Short_Name": "NE.3",
  "Test_Forms": {
    DIALECT.IONIC: [["politw=n", -1], ["a)gorw=n", -1], ["mhxanw=n", -1], ["r(htorikw=n", -1], ["qalassw=n", -1], ["moirw=n", -1], ["paideuome/nwn", -1], ["pepaideume/nwn", -1], ["w(=n", -1]],
    DIALECT.AEOLIC: [["polita=n", -1], ["a)gora=n", -1], ["maxana/n", -1], ["qa/lassan", -1], ["moira=n", -1], ["lipou=san", -1], ["a(=n", -1], ["ai)xmhta/wn", 0], ["baqei=an", 1]],
    DIALECT.HOMERIC: [["polita=n", -1], ["a)gora=n", -1], ["maxana/n", -1], ["qa/lassan", -1], ["moira=n", -1], ["lipou=san", -1], ["a(=n", -1], ["ai)xmhta/wn", 0], ["baqei=an", 1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_NE_4, "ruleName": "NE.4: Forms of digammma stems", "Short_Name": "NE.4",
  "Test_Forms": {
    DIALECT.IONIC: [["basile/os", -1], ["basilei=", -1], ["basile/a", -1], ["basilei=s", -1], ["basile/wn", -1], ["basile/as", -1]],
    DIALECT.AEOLIC: [["basilh=os", -1], ["basilh=i", -1], ["basilh=a", -1], ["basilei=s", -1], ["basile/wn", -1], ["basile/as", -1], ["ou)rei=s", -1]],
    DIALECT.HOMERIC: [["basilh=os", -1], ["basilh=i", -1], ["basilh=a", -1], ["basilh=es", -1], ["basilh/wn", -1], ["basilh=as", -1], ["ou)rh=es", -1], ["a)xillh=os", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["basileu=si", -1]]
  }
},
{"Tester": Rule_NE_5, "ruleName": "NE.5: forms of iota stems", "Short_Name": "NE.5",
  "Test_Forms": {
    DIALECT.IONIC: [["po/lews", -1], ["po/lei", -1], ["po/leis", -1], ["polei=s", -1], ["po/lewn", -1], ["po/lesi", -1]],
    DIALECT.AEOLIC: [["po/lios", -1], ["po/li", -1], ["po/lies", -1], ["poli/wn", -1], ["po/lisi", -1], ["poli/esi", -1], ["po/lis", -1]],
    DIALECT.HOMERIC: [["po/lios", -1], ["po/lhos", -1], ["po/lies", -1], ["po/lhes", -1], ["poli/wn", -1], ["poli/essi", -1], ["poli/essin", -1], ["po/lhas", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_NE_6, "ruleName": "NE.6: Dative plural in -essi", "Short_Name": "NE.6",
  "Test_Forms": {
    DIALECT.IONIC: [],
    DIALECT.AEOLIC: [["po/dessi", -1]],
    DIALECT.HOMERIC: [["po/dessi", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_NE_7, "ruleName": "NE.7: Homeric second declension endings", "Short_Name": "NE.7",
  "Test_Forms": {
    DIALECT.IONIC: [["lo/gou", -1], ["o(dou=", -1], ["lo/gois", -1], ["o(doi=s", -1]],
    DIALECT.AEOLIC: [["lo/gou", -1], ["o(dou=", -1], ["lo/gois", -1], ["o(doi=s", -1]],
    DIALECT.HOMERIC: [["lo/goio", -1], ["o(doi=o", -1], ["lo/goisi", -1], ["a(li/oio", 4], ["derkome/noio", -1], ["a(li/oio", 8], ["toi=o", -1], ["a)ndrofo/noio", 0]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1]]
  }
},
{"Tester": Rule_VE_1, "ruleName": "VE.1: Ionic mi-verbs inflected like contracts", "Short_Name": "VE.1",
  "Test_Forms": {
    DIALECT.IONIC: [["i(ei=si", -1], ["didoi=s", -1], ["didoi=sqa", -1], ["didoi=", -1], ["didou=si", -1], ["didou=sin", -1], ["tiqei=", -1], ["tiqei=si", -1]],
    DIALECT.AEOLIC: [["i(a=si", -1], ["di/dws", -1], ["di/dwsi", -1], ["di/dwsin", -1], ["dido/asi", -1], ["dido/asin", -1], ["ti/qhsi", -1], ["tiqe/asi", -1]],
    DIALECT.HOMERIC: [["i(ei=si", -1], ["didoi=s", -1], ["didoi=sqa", -1], ["didoi=", -1], ["didou=si", -1], ["didou=sin", -1], ["tiqei=", -1], ["tiqei=si", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["di/dwmi", -1]]
  }
},
{"Tester": Rule_VE_2, "ruleName": "VE.2: Third person middle forms", "Short_Name": "VE.2",
  "Test_Forms": {
    DIALECT.IONIC: [["tiqe/atai", -1], ["beblh/atai", -1], ["puqoi/ato", 0], ["puqoi/ato", 1]], # , ["dune/atai", -1] (better mi verb grabbing?)
    DIALECT.AEOLIC: [["ti/qentai", -1], ["be/blhntai", -1], ["paideu/ointo", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["gegra/fatai", -1]]
  }
},
{"Tester": Rule_VE_3, "ruleName": "VE.3: Alpha contract endings", "Short_Name": "VE.3",
  "Test_Forms": {
    DIALECT.IONIC: [["tima=|s", -1], ["tima=|", -1], ["tima=te", -1], ["tima=|", -1], ["tima=tai", -1], ["tima=sqe", -1], ["e)ti/mas", -1], ["e)ti/ma", -1], ["e)tima=te", -1], ["e)tima=to", -1], ["tima=n", -1], ["tima=sqai", -1], ["te/xna|", -1], ["e)texna=to", -1]],
    DIALECT.AEOLIC: [["timh=|s", -1], ["timh=|", -1], ["timh=|", -1], ["timhtai/", -1], ["timh=n", -1], ["te/xnh|", -1]],
    DIALECT.HOMERIC: [],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["po/lis", -1], ["timw=men", -1]]
  }
},
{"Tester": Rule_VE_4, "ruleName": "VE.4: Athematic 3rd plural secondary ending", "Short_Name": "VE.4",
  "Test_Forms": {
    DIALECT.IONIC: [["e)/dosan", -1], ["i(/stasan", -1]],
    DIALECT.AEOLIC: [["e)/don", -1], ["i(/stan", -1]],
    DIALECT.HOMERIC: [["e)/don", -1], ["i(/stan", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["po/lis", -1], ["di/dwmi", -1], ["'n", -1], ["en", -1], ["e)/peisin", -1], ["e)kpeta/sousin", -1]]
  }
},
{"Tester": Rule_VE_5, "ruleName": "VE.5: Active infinitive endings (-men vs -nai vs -menai)", "Short_Name": "VE.5",
  "Test_Forms": {
    DIALECT.IONIC: [["dido/nai", -1], ["tiqe/nai", -1]],
    DIALECT.AEOLIC: [["dido/men", -1], ["ti/qemen", -1], ["dido/menai", -1]],
    DIALECT.HOMERIC: [["dido/menai", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["po/lis", -1], ["di/dwmi", -1]]
  }
},
{"Tester": Rule_VE_6, "ruleName": "VE.6: Homeric verb endings", "Short_Name": "VE.6",
  "Test_Forms": {
    DIALECT.IONIC: [],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [["e)qe/lwmi", -1], ["a)ga/gwmi", -1], ["e)qe/lh|sqa", -1], ["dw=|si", -1], ["fa/anqen", -1], ["tra/fen", -1], ["h)/|deen", -1], ["h)/|dei", -1], ["h)/|dea", -1], ["metafraso/mesqa", -1], ["i(laso/mesqa", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["oi)=sqa", -1], ["e)/fhsqa", -1], ["di/dwsi", -1]]
  }
},
{"Tester": Rule_NM_1, "ruleName": "NM.1: Nu Movable (simple)", "Short_Name": "NM.1",
  "Test_Forms": {
    DIALECT.IONIC: [["paideu/ousin", -1], ["po/lisin", -1], ["e)pai/deusen", -1], ["w)/moisin", -1], ["pe/mpousin", -1], ["proqe/ousin", 0], ["proqe/ousin", 2], ["proqe/ousin", 3], ["proqe/ousin", 5], ["w)/moisin", 0], ["w)/moisin", 1], ["w)/moisin", 3]],
    DIALECT.AEOLIC: [],
    DIALECT.HOMERIC: [["paideu/ousin", -1], ["po/lisin", -1], ["e)pai/deusen", -1]],
    DIALECT.ANY: [["xe/ras", -1], ["paideu/w", -1], ["paideu/ete", -1], ["po/lin", -1], ["u(po/", -1], ["po/lis", -1]]
  }
}
]

if (False):
    rulesList = [
    {"Tester": Rule_NE_7, "ruleName": "NE.1b: Endings of singular feminine long alpha-stems", "Short_Name": "NE.1a",
      "Test_Forms": {
        DIALECT.IONIC: [],
        DIALECT.AEOLIC: [],
        DIALECT.HOMERIC: [["pontopo/roio", 0]],
        DIALECT.ANY: []
      }
    }]
# barei/hs  for NE_1b ["barei/hs", -1]
#example rule
if False:
    #,
    {"Tester": Rule_NE_1b, "ruleName": "", "Short_Name": "",
      "Test_Forms": {
        DIALECT.IONIC: [],
        DIALECT.AEOLIC: [],
        DIALECT.HOMERIC: [],
        DIALECT.ANY: []
      }
    }

# information in an individual parse.
# parse:
# "dialect" : dialect
# "form" : the form as it appears
# "pos": part of speech
# "expanded form": ??
# "feature": ???
# "lemma": the actual lemma

# pos = verb:
# "mood", "number" "person" "tense" "voice"

# pos = adjective:
# "case" "gender" "number"

# pos = noun:
# "case" "gender" "number"
