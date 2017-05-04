# -*- coding: utf-8 -*-
# utility functions that are shared by our different tools
from urllib2 import Request, urlopen, build_opener, URLError, HTTPError
from socket import error as socketError
import xml.etree.ElementTree as ET
import os
import re
import json
import sys
import copy
import errno



# empty class for creating constants
class Constant:
    pass

# constants for table printing
TABLE_PRINT = Constant()
TABLE_PRINT.ASCII = "ascii"
TABLE_PRINT.HTML = "html"

# dictionary names
DICTIONARY_NAMES = Constant()
DICTIONARY_NAMES.LSJ = "lsj"
DICTIONARY_NAMES.MiddleLiddell = "middle_liddell"
DICTIONARY_NAMES.Slater = "slater"
DICTIONARY_NAMES.Autenrieth = "autenrieth"

# vowel length
VOWEL_LEN = Constant()
VOWEL_LEN.SHORT = "s"
VOWEL_LEN.LONG = "l"
VOWEL_LEN.UNKNOWN = "?"

# parts of speech
POS = Constant()
POS.ADJECTIVE = "adj"
POS.NOUN = "noun"
POS.VERB = "verb"

# types of endings
ENDING_TYPES = Constant()
ENDING_TYPES.INDECLINABLE = "indecl"
ENDING_TYPES.ADVERB = "adv"
ENDING_TYPES.PREPOSITION = "prep"
ENDING_TYPES.CONJUNCTION = "conj"
ENDING_TYPES.ADJECTIVE = Constant()
ENDING_TYPES.ADJECTIVE.TWO_TERMINATION = "twoTerminationAdjective"
ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_A_CONTRACT = "twoTerminationAdjectiveAlphaContract"
ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_O_CONTRACT = "twoTerminationAdjectiveOmicronContract"
ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A = "threeTerminationAdjectiveAlpha"
ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H = "threeTerminationAdjectiveEta"
ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A_E_CONTRACT = "threeTerminationAdjectiveAlphaEpsilonContract"
ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H_E_CONTRACT = "threeTerminationAdjectiveEtaEpsilonContract"
ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_HS = "thirdDeclensionAdjectiveHS"
ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_WN = "thirdDeclensionAdjectiveWN"
ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US = "thirdDeclensionAdjectiveUS"
ENDING_TYPES.ADJECTIVE.POUS_FOOT = "footyAdjective"
ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA = "mixedAdjectiveEisEssa"
ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA_O_CONTRACT = "mixedAdjectiveEisEssaOmicronContract"
ENDING_TYPES.ADJECTIVE.MIXED_AS_AINA = "mixedAdjectiveAsAina"
ENDING_TYPES.ADJECTIVE.MIXED_HN_EINA = "mixedAdjectiveHnEina"
ENDING_TYPES.ADJECTIVE.MIXED_WS_UIA_OS = "adjectiveWsUiaOs"
ENDING_TYPES.ADJECTIVE.WS_W = "adjectiveWsW"
ENDING_TYPES.ADJECTIVE.IS_I = "adjective in -is/-i"
ENDING_TYPES.ADJECTIVE.PAS = "adjectivePas"
ENDING_TYPES.ADJECTIVE.AUTOU_COMPOUNDS = "adjectiveAutouType"
ENDING_TYPES.ADJECTIVE.OSDE_H = "adjective-osde, -hde"
ENDING_TYPES.ADJECTIVE.OSDE_A = "adjective-osde, -ade"
ENDING_TYPES.ADJECTIVE.EIS = "adjectiveEisMia"
ENDING_TYPES.ADJECTIVE.O = "adjectiveO,H,TO"
ENDING_TYPES.ADJECTIVE.ODE = "adjectiveOde"
ENDING_TYPES.ADJECTIVE.OS = "adjectiveOs"
ENDING_TYPES.ADJECTIVE.TIS = "adjectiveTis"
ENDING_TYPES.ADJECTIVE.MEGAS = "adjectiveMegas"
ENDING_TYPES.ADJECTIVE.PLEIWN = "adjectivePleiwn"
ENDING_TYPES.ADJECTIVE.POLUS = "adjectivePolus"
ENDING_TYPES.ADJECTIVE.DUO = "adjectiveDuo"
ENDING_TYPES.NOUN = Constant()
ENDING_TYPES.NOUN.FIRST_A_UNKNOWN = "firstDeclensionAlpha"
ENDING_TYPES.NOUN.FIRST_A_LONG = "firstDeclensionLongAlpha"
ENDING_TYPES.NOUN.FIRST_A_SHORT = "firstDeclensionShortAlpha"
ENDING_TYPES.NOUN.FIRST_H = "firstDeclensionEta"
ENDING_TYPES.NOUN.SECOND_OS = "secondDeclensionOS"
ENDING_TYPES.NOUN.SECOND_oOS = "secondDeclensionoOS"
ENDING_TYPES.NOUN.SECOND_HS = "secondDeclensionHS"
ENDING_TYPES.NOUN.SECOND_AS = "secondDeclensionAS"
ENDING_TYPES.NOUN.SECOND_ON = "secondDeclensionON"
ENDING_TYPES.NOUN.SECOND_oON = "secondDeclensionoON"
ENDING_TYPES.NOUN.THIRD_CONSONANT = "thirdDeclensionConsonantStem"
ENDING_TYPES.NOUN.THIRD_EPSILON = "thirdDeclensionEpsilonStem"
ENDING_TYPES.NOUN.THIRD_IOTA = "thirdDeclensionIotaStem"
ENDING_TYPES.NOUN.THIRD_SIGMA_MF = "thirdDeclensionSigmaStemMasc/Fem"
ENDING_TYPES.NOUN.THIRD_SIGMA_N = "thirdDeclensionSigmaStemNeuter"
ENDING_TYPES.NOUN.THIRD_DIGAMMA = "thirdDeclensionDigammaStem"
ENDING_TYPES.NOUN.THIRD_IS_FEM = "thirdDeclension-i/sFeminine"
ENDING_TYPES.NOUN.THIRD_OUS = "thirdDeclensionOu=sGenitive"
ENDING_TYPES.NOUN.THIRD_ES_OUS_TO = "thirdDeclension-es, -ous, to/"
ENDING_TYPES.NOUN.THIRD_I_TO = "thirdDeclension-i, to/"
ENDING_TYPES.NOUN.THIRD_HDU_TYPE = "thirdDeclensionU/"
ENDING_TYPES.NOUN.THIRD_WS_S = "nounWsW"
ENDING_TYPES.NOUN.POUS = "nounPous"
ENDING_TYPES.NOUN.ASTU = "nounAstu"
ENDING_TYPES.NOUN.BOUS = "nounBous"
ENDING_TYPES.NOUN.GERAS = "nounGeras"
ENDING_TYPES.NOUN.GHRAS = "nounGhras"
ENDING_TYPES.NOUN.DORU = "nounDoru"
ENDING_TYPES.NOUN.DRUS = "nounDrus"
ENDING_TYPES.NOUN.HMEROKALLES = "nounH(merokalle/s"
ENDING_TYPES.NOUN.IQUS = "nounI)qu/s"
ENDING_TYPES.NOUN.IS = "nounI)/s"
ENDING_TYPES.NOUN.KREAS = "nounKreas"
ENDING_TYPES.NOUN.KWAS = "nounKwas"
ENDING_TYPES.NOUN.LAGWS = "nounLagws"
ENDING_TYPES.NOUN.DAKRU = "nounDakru"
ENDING_TYPES.NOUN.NAUS = "nounNaus"
ENDING_TYPES.NOUN.PELAKUS = "nounPelakus"
ENDING_TYPES.NOUN.PUQW = "nounPuqw"
ENDING_TYPES.NOUN.XEIR = "nounXeir"
ENDING_TYPES.NOUN.XREW = "nounXrew/"
ENDING_TYPES.NOUN.XREWN = "nounXrew/n"
ENDING_TYPES.NOUN.ZEUS = "nounZeu/s"
ENDING_TYPES.PRONOUN = Constant()
ENDING_TYPES.PRONOUN.EGW = "pronounEgw"
ENDING_TYPES.PRONOUN.MIN = "pronounMin"
ENDING_TYPES.PRONOUN.SFEIS = "pronounSfeis"
ENDING_TYPES.VERB = Constant()
ENDING_TYPES.VERB.THEMATIC = "thematicVerb"
ENDING_TYPES.VERB.A_CONTRACT = "aContractVerb"
ENDING_TYPES.VERB.E_CONTRACT = "eContractVerb"
ENDING_TYPES.VERB.O_CONTRACT = "oContractVerb"
ENDING_TYPES.VERB.DEPONENT = "deponentVerb"
ENDING_TYPES.VERB.DEPONENT_OMAI = "deponentVerbEimai"
ENDING_TYPES.VERB.DEPONENT_EIMAI = "deponentVerbEimai"
ENDING_TYPES.VERB.DEPONENT_A_MAI = "deponentVerbA_mai"
ENDING_TYPES.VERB.DEPONENT_AsMAI = "deponentVerbA^mai"
ENDING_TYPES.VERB.DEPONENT_HMAI = "deponentVerbHmai"
ENDING_TYPES.VERB.DEPONENT_EMAI = "deponentVerbEmai"
ENDING_TYPES.VERB.DEPONENT_WMAI = "deponentVerbWmai"
ENDING_TYPES.VERB.A_CONTRACT_DEPONENT = "aContractDeponent"
ENDING_TYPES.VERB.E_CONTRACT_DEPONENT = "eContractDeponent"
ENDING_TYPES.VERB.O_CONTRACT_DEPONENT = "oContractDeponent"
ENDING_TYPES.VERB.UMI = "verbEndingInUmi"
ENDING_TYPES.VERB.ATHEMATIC = "athematicVerb"
ENDING_TYPES.VERB.EIMI = "athematicVerbEimi"
ENDING_TYPES.VERB.ISTHMI = "athematicVerbIsthmi"
ENDING_TYPES.VERB.DIDWMI = "athematicVerbDidwmi"
ENDING_TYPES.VERB.IHMI = "athematicVerbIhmi"
ENDING_TYPES.VERB.TIQHMI = "athematicVerbTiqhmi"
ENDING_TYPES.VERB.INFINITIVE = "verbInfinitive"
ENDING_TYPES.VERB.OIDA = "verbOida"
ENDING_TYPES.VERB.GEGWNA = "verbGe/gwna"
ENDING_TYPES.VERB.EOIKA = "verbE)/oika"
ENDING_TYPES.VERB.FHMI = "verbFhmi"
ENDING_TYPES.VERBAL_ADJECTIVE = "verbalAdjective"
ENDING_TYPES.PARTICIPLE = Constant()
ENDING_TYPES.PARTICIPLE.WN = "participleWn"
ENDING_TYPES.OTHER = "other"


def defaultEndingFunc(ending, parseData):
    return False, [], ending

def firstSecondLongAEndingFunc(ending, parseData):
    if (parseData["lemma"] == "ui(o/s"): # todo: don't just default to this for os/on?
        if ending == "as":
            return True, [VOWEL_LEN.SHORT], ending
    if ending == "a" and "gender" in parseData: #TODO gender broken
        if parseData["gender"] == "neut":
            return True, [VOWEL_LEN.SHORT], ending
        elif parseData["gender"] == "fem":
            return True, [VOWEL_LEN.LONG], ending
    if ending == "as" or ending == "an" or ending == "a|":
        return True, [VOWEL_LEN.LONG], ending
    if ending[0:4] == "h|si" or ending[0:4] == "a|si" or ending[0:4] == "oisi":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
    return False, [], ending

def firstSecondShortAEndingFunc(ending, parseData):
    if ending == "a" or ending == "an":
        return True, [VOWEL_LEN.SHORT], ending
    elif ending == "as" or ending == "a|":
        return True, [VOWEL_LEN.LONG], ending
    if ending[0:4] == "h|si" or ending[0:4] == "a|si" or ending[0:4] == "oisi":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
    return False, [], ending

def secondHsEndingFunc(ending, parseData):
    if "case" in parseData and parseData["case"] == "voc":
        if ending == "a":
            return True, [VOWEL_LEN.SHORT], ending
    return firstSecondLongAEndingFunc(ending, parseData)

def adjHsEndingFunc(ending, parseData):
    if ending[0:3] == "esi" or ending[0:4] == "essi":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    if ending[0:2] == "si":
        return True, [VOWEL_LEN.SHORT], ending
    return False, [], ending


def thirdDeclEndings(ending, parseData):
    if parseData["lemma"] == "a)nh/r":
        if (ending == "a)nhr" or ending == "a)ndri" or ending == "a)ndra" or ending == "a)ndras" or ending == "a)ndros" or ending == "a)ndres"):
            return True, [VOWEL_LEN.UNKNOWN, VOWEL_LEN.SHORT], ending
        elif (ending[0:8] == "a)ndrasi" or ending[0:8] == "a)ndresi"):
            return True, [VOWEL_LEN.UNKNOWN, VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
        elif (ending == "a)ndrwn"):
            return True, [VOWEL_LEN.UNKNOWN, VOWEL_LEN.LONG], ending
    elif parseData["lemma"] == "mh/thr":
        if (ending == "mater" or ending == "matri" or ending == "mhtri"):
            return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
        elif (ending == "materi" or ending == "mhteri" or ending == "materos" or ending == "matera" or ending == "matera"):
            return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    if ending == "i" or ending == "a" or ending == "as" or ending[0:2] == "si":
        return True, [VOWEL_LEN.SHORT], ending
    if ending[0:4] == "essi":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    return False, [], ending

def thirdIotaEndings(ending, parseData):
    if ending == "is" or ending == "i" or ending == "in":
        return True, [VOWEL_LEN.SHORT], ending
    if ending[0:3] == "esi" or ending[0:4] == "essi":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    return False, [], ending

def thirdDigammaEndings(ending, parseData):
    if ending == "a":
        return True, [VOWEL_LEN.LONG], ending
    if ending == "ea" or ending == "eas":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.LONG], ending
    if ending[0:4] == "eusi":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
    return False, [], ending

def adjUsEndingFunc(ending, parseData):
    match, endings, newEnding = firstSecondShortAEndingFunc(ending, parseData)
    if match:
        return True, endings, newEnding

    if ending == "us" or ending == "un" or ending == "u":
        return True, [VOWEL_LEN.SHORT], ending
    if ending == "ea" or ending[0:3] == "esi":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    return False, [], ending

def verbEndingFunc(ending, parseData):
    if parseData["pos"] == "part":
        baseLen = []
        rest = ""
    else:
        if "tense" in parseData and parseData["tense"] == "aor":
            if ending == "a" or ending == "as" or ending == "an":
                return True, [VOWEL_LEN.SHORT], ending
            if ending == "amen" or ending == "ate" or ending == "ato" or ending == "anto":
                return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
            if ending == "hsan":
                return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
        elif "tense" in parseData and parseData["tense"] == "perf":
            if ending == "a" or ending == "as":
                return True, [VOWEL_LEN.LONG], ending
            if ending == "amen" or ending == "ate":
                return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
            if ending[0:3] == "asi":
                return True, [VOWEL_LEN.LONG, VOWEL_LEN.LONG], ending
        elif "tense" in parseData and parseData["tense"] == "plup":
            if ending == "esan":
                return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending

        if ending == "ion": #TODO
            return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
        if ending[0:3] == "wsi" or ending[0:4] == "h|si" or ending == "wmi" or ending == "h|sqa" or ending == "oimi" or ending == "aimi" or ending == "eian" or ending[0:3] == "wsi" or ending == "meqa" or ending == "onta":
            return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
        if ending == "omeqa":
            return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
        if ending == "wmeqa" or ending == "w|meqa" or ending == "oimeqa":
            return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
        if ending == "eihsan" or ending == "eihsi" or ending == "eih|si":
            return True, [VOWEL_LEN.LONG, VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
    return False, [], ending

def eContractVerbEndingFunc(ending, parseData):
    if "tense" in parseData and (parseData["tense"] == "pres" or parseData["tense"] == "imperf"):
        if ending[0:5] == "eoisi":
            return True, [VOWEL_LEN.SHORT, VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
        return False, [], ending

    return verbEndingFunc(ending, parseData)

def aContractVerbEndingFunc(ending, parseData):
    if "tense" in parseData and (parseData["tense"] == "pres" or parseData["tense"] == "imperf"):
        if ending == "a" or ending == "as" or ending == "a|" or ending == "a|s" or ending == "an" or ending == "aq'" or ending == "at'":
            return True, [VOWEL_LEN.LONG], ending
        if ending == "atai":
            return True, [VOWEL_LEN.LONG, VOWEL_LEN.LONG], ending
        if ending == "ate" or ending == "ato" or ending == "asqe" or ending == "asa":
            return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
        return False, [], ending

    return verbEndingFunc(ending, parseData)

def minEndingFunc(ending, parseData):
    if ending == "min" or ending == "nin":
        return True, [VOWEL_LEN.SHORT], ending
    return False, [], ending

def tisEndingFunc(ending, parseData):
    if ending == "is" or ending == "i":
        return True, [VOWEL_LEN.SHORT], ending
    if ending == "inos" or ending == "ini" or ending == "ina" or ending == "ines" or ending == "inas" or ending[0:4] == "isi":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    if ending == "inwn":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.LONG], ending
    return False, [], ending

def umiEndingFunc(ending, parseData):
    if ending == "us" or ending == "un" or ending == "u":
        return True, [VOWEL_LEN.LONG], ending
    if ending == "us'" :
        return True, [VOWEL_LEN.UNKNOWN], ending
    if ending == "unt'" or ending == "ut'" or ending == "uq'" or ending == "usq'":
        return True, [VOWEL_LEN.SHORT], ending
    if ending == "umi" or ending[0:3] == "usi":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
    if ending == "umen" or ending == "ute" or ending == "usqe" or ending == "usan" or ending == "uso" or ending == "uto" or ending == "ute" or ending == "umeq'":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    if ending == "umai" or ending == "usai" or ending == "utai" or ending == "untai" or ending == "umhn" or ending == "utw" or ending == "untwn" or ending == "usqw" or ending == "usqwn" or ending == "unai" or ending == "usqai":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.LONG], ending
    if ending[0:4] == "uasi":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
    if ending == "umeqa":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    return False, [], ending

def zeusEndingFunc(ending, parseData):
    if ending == "zeus" or ending == "dios" or ending == "dii" or ending == "dia" :
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    if ending == "zeu" or ending == "di" or ending == "zhn":
        return True, [VOWEL_LEN.LONG], ending
    if ending == "zhnos" or ending == "zhni" or ending == "zhna":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
    return False, [], ending

def xeirEndingFunc(ending, parseData):
    if ending == "xeir":
        return True, [VOWEL_LEN.LONG], ending
    if ending == "xeiros" or ending == "xeiri" or ending[0:6] == "xeirsi" or ending == "xeira" or ending == "xeire" or ending == "xeires" or ending == "xeiras":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], ending
    if ending == "xeirwn" or ending == "xeiroin":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.LONG], ending
    if ending[0:5] == "xersi":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    return False, [], ending

def egoEndingFunc(ending, parseData):
    if ending == "h(min" or ending == "h(mas":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.UNKNOWN], ending
    return False, [], ending


def polusEndingFunc(ending, parseData):
    if ending == "u" or ending == "un":
        return True, [VOWEL_LEN.SHORT], ending
    if ending == "ea":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], ending
    return firstSecondLongAEndingFunc(ending, parseData)

def oidaEndingFunc(ending, parseData):
    ending = ending.replace(")", "")
    if ending == "oida" or ending == "oidqa" or ending == "h|san":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT], "v" + ending
    elif ending == "hdesan":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], "v" + ending
    elif ending == "hdhsqa":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.LONG, VOWEL_LEN.SHORT], "v" + ending
    elif ending == "idmen" or ending == "ismen" or ending == "iste" or ending == "isqi":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.SHORT], "v" + ending
    elif ending == "istw" or ending == "istwn":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.LONG], "v" + ending
    elif ending[0:5] == "isasi" or ending == "ismen" or ending == "iste":
        return True, [VOWEL_LEN.SHORT, VOWEL_LEN.LONG, VOWEL_LEN.SHORT], "v" + ending
    elif ending == "eideihsan":
        return True, [VOWEL_LEN.LONG, VOWEL_LEN.LONG, VOWEL_LEN.LONG, VOWEL_LEN.SHORT], "v" + ending
    return False, [], ending

ENDING_DIVISIONS = {
"": defaultEndingFunc,
ENDING_TYPES.INDECLINABLE: defaultEndingFunc,
ENDING_TYPES.ADVERB: defaultEndingFunc,
ENDING_TYPES.PREPOSITION: defaultEndingFunc,
ENDING_TYPES.CONJUNCTION: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.TWO_TERMINATION: firstSecondLongAEndingFunc,
ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_A_CONTRACT: firstSecondLongAEndingFunc,
ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_O_CONTRACT: firstSecondLongAEndingFunc,
ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A: firstSecondLongAEndingFunc,
ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H: firstSecondLongAEndingFunc,
ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A_E_CONTRACT: firstSecondLongAEndingFunc,
ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H_E_CONTRACT: firstSecondLongAEndingFunc,
ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_HS: adjHsEndingFunc,
ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_WN: thirdDeclEndings,
ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US: adjUsEndingFunc,
ENDING_TYPES.ADJECTIVE.POUS_FOOT: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA_O_CONTRACT: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.MIXED_AS_AINA: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.MIXED_HN_EINA: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.MIXED_WS_UIA_OS: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.WS_W: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.IS_I: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.PAS: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.AUTOU_COMPOUNDS: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.OSDE_H: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.OSDE_A: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.EIS: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.O: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.ODE: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.OS: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.TIS: tisEndingFunc,
ENDING_TYPES.ADJECTIVE.MEGAS: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.PLEIWN: defaultEndingFunc,
ENDING_TYPES.ADJECTIVE.POLUS: polusEndingFunc,
ENDING_TYPES.ADJECTIVE.DUO: defaultEndingFunc,
ENDING_TYPES.NOUN.FIRST_A_UNKNOWN: defaultEndingFunc,
ENDING_TYPES.NOUN.FIRST_A_LONG: firstSecondLongAEndingFunc,
ENDING_TYPES.NOUN.FIRST_A_SHORT: firstSecondShortAEndingFunc,
ENDING_TYPES.NOUN.FIRST_H: firstSecondLongAEndingFunc,
ENDING_TYPES.NOUN.SECOND_OS: firstSecondLongAEndingFunc,
ENDING_TYPES.NOUN.SECOND_oOS: firstSecondLongAEndingFunc,
ENDING_TYPES.NOUN.SECOND_HS: secondHsEndingFunc,
ENDING_TYPES.NOUN.SECOND_AS: firstSecondLongAEndingFunc,
ENDING_TYPES.NOUN.SECOND_ON: firstSecondLongAEndingFunc,
ENDING_TYPES.NOUN.SECOND_oON: firstSecondLongAEndingFunc,
ENDING_TYPES.NOUN.THIRD_CONSONANT: thirdDeclEndings,
ENDING_TYPES.NOUN.THIRD_EPSILON: defaultEndingFunc,
ENDING_TYPES.NOUN.THIRD_IOTA: thirdIotaEndings,
ENDING_TYPES.NOUN.THIRD_SIGMA_MF: adjHsEndingFunc,
ENDING_TYPES.NOUN.THIRD_SIGMA_N: adjHsEndingFunc,
ENDING_TYPES.NOUN.THIRD_DIGAMMA: thirdDigammaEndings,
ENDING_TYPES.NOUN.THIRD_IS_FEM: defaultEndingFunc,
ENDING_TYPES.NOUN.THIRD_OUS: defaultEndingFunc,
ENDING_TYPES.NOUN.THIRD_ES_OUS_TO: defaultEndingFunc,
ENDING_TYPES.NOUN.THIRD_I_TO: defaultEndingFunc,
ENDING_TYPES.NOUN.THIRD_HDU_TYPE: adjUsEndingFunc,
ENDING_TYPES.NOUN.THIRD_WS_S: defaultEndingFunc,
ENDING_TYPES.NOUN.POUS: defaultEndingFunc,
ENDING_TYPES.NOUN.ASTU: defaultEndingFunc,
ENDING_TYPES.NOUN.BOUS: defaultEndingFunc,
ENDING_TYPES.NOUN.GERAS: defaultEndingFunc,
ENDING_TYPES.NOUN.GHRAS: defaultEndingFunc,
ENDING_TYPES.NOUN.DORU: defaultEndingFunc,
ENDING_TYPES.NOUN.DRUS: defaultEndingFunc,
ENDING_TYPES.NOUN.HMEROKALLES: defaultEndingFunc,
ENDING_TYPES.NOUN.IQUS: defaultEndingFunc,
ENDING_TYPES.NOUN.IS: defaultEndingFunc,
ENDING_TYPES.NOUN.KREAS: defaultEndingFunc,
ENDING_TYPES.NOUN.KWAS: defaultEndingFunc,
ENDING_TYPES.NOUN.LAGWS: defaultEndingFunc,
ENDING_TYPES.NOUN.DAKRU: defaultEndingFunc,
ENDING_TYPES.NOUN.NAUS: defaultEndingFunc,
ENDING_TYPES.NOUN.PELAKUS: defaultEndingFunc,
ENDING_TYPES.NOUN.PUQW: defaultEndingFunc,
ENDING_TYPES.NOUN.XEIR: xeirEndingFunc,
ENDING_TYPES.NOUN.XREW: defaultEndingFunc,
ENDING_TYPES.NOUN.XREWN: defaultEndingFunc,
ENDING_TYPES.NOUN.ZEUS: zeusEndingFunc,
ENDING_TYPES.PRONOUN.EGW: egoEndingFunc,
ENDING_TYPES.PRONOUN.MIN: minEndingFunc,
ENDING_TYPES.PRONOUN.SFEIS: defaultEndingFunc,
ENDING_TYPES.VERB.THEMATIC: verbEndingFunc,
ENDING_TYPES.VERB.A_CONTRACT: aContractVerbEndingFunc,
ENDING_TYPES.VERB.E_CONTRACT: eContractVerbEndingFunc,
ENDING_TYPES.VERB.O_CONTRACT: verbEndingFunc,
ENDING_TYPES.VERB.DEPONENT: defaultEndingFunc,
ENDING_TYPES.VERB.DEPONENT_OMAI: defaultEndingFunc,
ENDING_TYPES.VERB.DEPONENT_EIMAI: defaultEndingFunc,
ENDING_TYPES.VERB.DEPONENT_A_MAI: defaultEndingFunc,
ENDING_TYPES.VERB.DEPONENT_AsMAI: defaultEndingFunc,
ENDING_TYPES.VERB.DEPONENT_HMAI: defaultEndingFunc,
ENDING_TYPES.VERB.DEPONENT_EMAI: defaultEndingFunc,
ENDING_TYPES.VERB.DEPONENT_WMAI: defaultEndingFunc,
ENDING_TYPES.VERB.A_CONTRACT_DEPONENT: aContractVerbEndingFunc,
ENDING_TYPES.VERB.E_CONTRACT_DEPONENT: verbEndingFunc,
ENDING_TYPES.VERB.O_CONTRACT_DEPONENT: verbEndingFunc,
ENDING_TYPES.VERB.UMI: umiEndingFunc,
ENDING_TYPES.VERB.ATHEMATIC: defaultEndingFunc,
ENDING_TYPES.VERB.EIMI: defaultEndingFunc,
ENDING_TYPES.VERB.ISTHMI: defaultEndingFunc,
ENDING_TYPES.VERB.DIDWMI: defaultEndingFunc,
ENDING_TYPES.VERB.IHMI: defaultEndingFunc,
ENDING_TYPES.VERB.TIQHMI: defaultEndingFunc,
ENDING_TYPES.VERB.INFINITIVE: defaultEndingFunc,
ENDING_TYPES.VERB.OIDA: oidaEndingFunc,
ENDING_TYPES.VERB.GEGWNA: defaultEndingFunc,
ENDING_TYPES.VERB.EOIKA: defaultEndingFunc,
ENDING_TYPES.VERB.FHMI: defaultEndingFunc,
ENDING_TYPES.VERBAL_ADJECTIVE: defaultEndingFunc,
ENDING_TYPES.PARTICIPLE.WN: defaultEndingFunc,
ENDING_TYPES.OTHER: defaultEndingFunc,
}


# whether or not to print every token that is run through Perseus' Morpheus
VERBOSE_PERSEUS = False


# enumeration for stem types.
ADJ_3_TERMINATION = "type_1_2_os/a/on_adjective"
ADJ_2ND_DECL = "type_2nd_decl_adjective"
ADJ_US = "type_us_eia_u_adjective"
ADJ_EIS_ESSA = "type_eis_essa_en_adjective"
H_A_STEM = "alpha_stem_-h"
SHORT_A_STEM = "alpha_stem_short_-a"
EIR_A_STEM = "alpha_stem_eir_-a"
EIR_SHORT_A_STEM = "alpha_stem_eir_short_-a"
W_STEM = "digamma_stem"
I_STEM = "iota_stem"
O_STEM = "omicron_stem"
S_STEM = "sigma_stem"
NO_TYPE = "no_special_type"



# enumeration for dialect types.

DIALECT = Constant()
DIALECT.NONE = -2
DIALECT.ANY = -1
DIALECT.IONIC = 0
DIALECT.AEOLIC = 1
DIALECT.HOMERIC = 2

DIALECT_NAMES = [
"Ionic",
"Aeolic",
"Homeric"
]

MORPHEUS_DIALECT_NAMES = [
"ionic",
"aeolic",
"epic"
]

NUM_DIALECTS = 3

if (False):
    DIALECT.ATTIC = 0
    DIALECT.DORIC = 1

    DIALECT_NAMES = [
    "Attic",
    "Doric"
    ]

    NUM_DIALECTS = 2

# get a dialect name given the index corresponding to the dialect
def getDialectName(i):
    if (i == -1):
        return "Any"
    if (i == -2):
        return "None"
    return DIALECT_NAMES[i]

# get the morpheus name associated with the dialect
def getMorpheusDialectName(i):
    return MORPHEUS_DIALECT_NAMES[i]

# convert an array of dialect information into a single integer
def convertDialectArrayToInt(arr):
    totalSum = 0
    current = 1
    for i in range(len(arr)):
        val = arr[i] + 1
        totalSum += current * val
        current *= 3
    return totalSum

# convert an integer into an array of dialect information
def convertIntToDialectArray(val):
    arr = []
    curr = val
    for i in range(NUM_DIALECTS):
        arr.append((curr % 3) - 1)
        curr = curr / 3
    return arr

# given a combination of dialect possibilities, return a string
def getComboName(n):
    arr = convertIntToDialectArray(n)
    vals = []
    for i in range(len(arr)):
        dialectName = getDialectName(i)
        val = arr[i]
        s = ""
        if not(val == 0):
            if (val == 1):
                s += "Definitely "
            elif (val == -1):
                s += "Definitely Not "
            s += dialectName
            vals.append(s)

    if len(vals) == 0:
        return "Any Dialect"
    else:
        return ", ".join(vals)


# return an array of n of the given value
def getNArray(n, val):
    arr = []
    for i in range(n):
        arr.append(copy.deepcopy(val))
    return arr



# get the filename containing the uncleaned text of a text given the text's name
def getTextFn(textName):
    return "texts/" + textName + ".txt";
# get the filename containing the cleaned text of a text given the text's name
def getTextCleanFn(textName):
    return "intermediateFiles/" + textName + "/clean_text.txt"
# get the filename containing the form info of a text given the text's name
def getTextFormDataFn(textName):
    return "intermediateFiles/" + textName + "/formData.json"
# get the filename containing the lemmas of a text given the text's name
def getTextLemmasFn(textName):
    return "intermediateFiles/" + textName + "/lemmas.json"
# get the filename containing the lemma data of a text given the text's name
def getTextLemmaDataFn(textName):
    return "intermediateFiles/" + textName + "/lemmaData.json"
# get the directory for the feature data
def getTextFeatureDataDir():
    return "intermediateFiles/feature_data/"
# get the filename for the text feature data
def getTextFeatureDataOdikonFn(textName, approach):
    return getTextFeatureDataDir() + "odikon_" + approach + "/" + textName + ".json"
def getTextFeatureDataTamnonFn(textName):
    return getTextFeatureDataDir() + "tamnon/"+ textName + ".json"
# get the filename for the ground truth scan data
def getTextTrueScanDataFn(textName):
    return "scanData/" + textName + "_scansion.txt"
# get the filename for the evaluation of the given text with the given approach
def getScanEvalOutputFn(textName, approach):
    return "evalResults/" + textName + "_" + approach + "_scansion.txt"
# get the filename for the latex table for evaluation of the given text
def getScanEvalTableOutputFn(approach):
    return "evalResults/" + approach + "_scansion_eval_latex_table.txt"
# get the filename containing the links to all the dictionary entries
def getDictionaryEntriesFn(dictName):
    return "dictionaries/entries/" + dictName + ".json";
# get the filename containing the raw data from the dictionary
def getRawDictionaryFn(dictName):
    return "dictionaries/raw/" + dictName + ".json";
# get the filename containing the processed data dictionary
def getProcessedDictionaryFn(dictName):
    return "dictionaries/processed/" + dictName + ".json";
# get the filename containing the dictionary's supplementary data
def getSupplementaryDictionaryFn(dictName):
    return "supplementaryDictionaries/" + dictName + "_supplementary.json";

# get the filename containing the overall results of a text given the text's name
def getTextOverallResultsFn(textName):
    return "tamnonResults/" + textName + "/overall.txt"
# get the filename containing the dialect results of a text given the text's name
def getTextDialectResultsFn(textName):
    return "tamnonResults/" + textName + "/dialects.txt"
# get the filename containing the rules results of a text given the text's name
def getTextRuleResultsFn(textName):
    return "tamnonResults/" + textName + "/rules.txt"
# get the filename containing the token results of a text given the text's name
def getTextTokenResultsFn(textName):
    return "tamnonResults/" + textName + "/tokens.txt"
# get the filename containing the evaluation results of a text given the text's name
def getTextEvaluationResultsFn(textName):
    return "evalResults/tamnonByText/" + textName + ".txt"
# get the filename containing all the results of a text given the text's name
def getTextAllResultsFn(textName):
    return "tamnonResults/" + textName + "/all.txt"
# get the filename containing the feature results of a text given the text's name
def getTextReatureResultsTamnonIntermediateFn(textName):
    return "intermediateFiles/" + textName + "/tamnonIntermediateFeatureData.json"
# get the filename containing all the results of a text given the text's name
def getTextGraphFn(textName, pct_or_count, max_or_min, sortd):
    return "graphResults/%s/graphs/%s_%s_%s_ruleResults_pct_graph.pdf" % (textName, pct_or_count, sortd, max_or_min)

# get the directory for the final results output
def getFinalResultsOutputDir(dataSet):
    return "results/" + dataSet + "/"


# get the filename containing the feature results of all the texts
def getFeatureMatrixFn():
    return getTextFeatureDataDir() + "combined/featureMatrix.json"



# check if the given file path exists, and if not create it.
# based on Krumelur's answer to
# http://stackoverflow.com/questions/12517451/python-automatically-creating-directories-with-file-output
def check_and_create_path(filename):
    if (not os.path.exists(os.path.dirname(filename))):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

# write content to the file at filename. Make the directory path to the given
# file if it does not exist.
def safeWrite(filename, content):
    check_and_create_path(filename)
    out_file = open(filename, "w")
    out_file.write(content)
    out_file.close()

# get the content from a given file by reading it
# parseJSON is true if we should parse the contents as JSON first
def getContent(inFileName, parseJSON):
    inFile = open(inFileName, 'r')
    inContents = inFile.read()
    inFile.close()
    if parseJSON:
        return json.loads(inContents)
    else:
        return inContents


# ==============================================================================
# ==============================================================================
# ==============================================================================


# get the line, lemma, and form data for a given text
def getScanData(textName):
    lineFileName = getTextCleanFn(textName)
    lemmaFileName = getTextLemmaDataFn(textName)
    formFileName = getTextFormDataFn(textName)
    dictFileName = getProcessedDictionaryFn(DICTIONARY_NAMES.LSJ)
    suppDictFileName = getSupplementaryDictionaryFn(DICTIONARY_NAMES.LSJ)
    lines = getContent(lineFileName, True)
    lemma = getContent(lemmaFileName, True)
    formData = getContent(formFileName, True)
    dictionary = getContent(dictFileName, True)["dict"]
    suppDictionary = getContent(suppDictFileName, True)["dict"]

    for key in suppDictionary:
        dictionary[key] = suppDictionary[key]

    formRes = {}
    for form in formData:
        key = form[0]
        val = form[1]
        formRes[key] = val


    # certain sections of the Hymns are in couplets, so half the lines are hexameter.
    lines2 = []
    if (textName == "CallimachusHymns"):
        for line in lines:
            if not(line["book"] == 5 and (line["line"] % 2 == 0)):
                lines2.append(line)
    else:
        lines2 = lines
    lines = lines2
    return (lines, lemma, formRes, dictionary)

# get the scan data that should be produced for each line
def getTargetScanData(textName):
    fileName = getTextTrueScanDataFn(textName)
    return getContent(fileName, False).split("\n")

# switch a capitalized token to lowercase
def decapitalizeToken(w):
    tokenLC = w.lower()
    # Beta code has a fun quirk where diacritic marks are added to the *
    # if the first letter is capitalized, so A)/lkhstis is *)/alkhstis.
    # So if we naively remove the *, we end up with improperly formatted
    # forms and must instead be a bit clever.
    if (len(tokenLC) >= 2 and tokenLC[0] == '*' and re.match(r'\)|\(|/|=|\\|&|\+|\||\'', tokenLC[1])):
        # split into star, first diacritic marks, rest of string
        split = re.split(r'((\)|\(|/|=|\\|&|\+|\||\')+)', tokenLC, 1)
        return split[3][0] + split[1] + split[3][1:]
    else:
        return re.sub(r'\*', "", tokenLC)

# given words that potentially begin with something like =(w,
# fix it to the proper w=(; for words with =( (the improper order) fix them
# to (=
initialAccentProblemRegex = re.compile("^[\s]*([=/\\\\\)\(]+)([aehiowur])([^=/\\\\\)\(]|$)")
accentFlipRegex = re.compile("([=/\\\\])([\)\(])")
badParenStartRegex = re.compile("^\(([a-z])")
badParenEndRegex = re.compile("([bcdfgjklmnpqrstvxyz][iu]|[a-z][abcdefghjklmnopqrstvwxyz])\(")
def fixTokenAccents(text):
    if not(re.search(initialAccentProblemRegex, text) == None):
        s1 = re.sub(initialAccentProblemRegex, r'\2\1\3', text)
    else:
        s1 = text
    if not(re.search(accentFlipRegex, text) == None):
        s2 = re.sub(accentFlipRegex, r'\2\1', s1)
    else:
        s2 = s1
    if not(re.search(badParenStartRegex, text) == None):
        s3 = re.sub(badParenStartRegex, r'\1', s2)
    else:
        s3 = s2
    if not(re.search(badParenEndRegex, text) == None):
        s4 = re.sub(badParenEndRegex, r'\1', s3)
    else:
        s4 = s3
    return s4

# Morpheus converts the \ accent to an / automatically, so for proper
# recognition of original forms we must also do so. We also want all
# capitals in beta code to be switched to lower case.
# Morpheus also automatically removes the second accent on tokens who have
# an accent added due to following enclitics, so we should remove those as well.
def fixToken (w) :
    lowerBeta = decapitalizeToken(w)
    lowerBeta = fixTokenAccents(lowerBeta)
    # if there are two accents and the second is /, remove it. Unless it is
    # dia/doxa/, which as to be recognized with both, because that is how
    # Morpheus sees it.
    if (lowerBeta == "dia/doxa/"):
        oneAccent = lowerBeta
    else:
        split = re.split(r'(/|=)', lowerBeta)
        if (len(split) > 3 and split[3] == "/"):
            oneAccent = split[0] + split[1] + split[2] + split[4]
        else:
            oneAccent = lowerBeta
    return re.sub(r'\\', '/', oneAccent)

# remove newlines from text
def removeNewlines(text):
    return re.sub(r'\n', " ", text)

# the original text but is not present.
# remove dubious sections from text
def removeDubious(text):
    return re.sub(r'(†.*?†)|(\[.*?\])|(<.*?>)', "", text)

# remove non-beta code characters
def removeNonBetaCode(text):
    # technically & should be in here, but I've found that the perseus
    # texts never mark macrons but it will leave in some ugly splitting
    # characters.
    return re.sub(r'[^A-Za-z)(/=\\+|\'\s*]', " ", text)

# fix strange spacing
def fixSpacing(text):
    # take groups of spaces and convert them to a single space
    groupSpaces = re.sub(r'\s+', " ", text)
    # removes spaces at the start and end of the text
    noStartSpace = re.sub(r'^\s+', "", groupSpaces)
    return re.sub(r'\s+$', "", noStartSpace)


# Clean up the input data (that has been copied from Perseus)
# Text in daggers generally makes no sense and is assumed to have been
# transmitted poorly. Text in square brackets is assumed to have been
# added from another location in the text or a later actor.
# Text in angle brackets contain a token that is presumed to have existed in
def cleanUpData (d) :
    # remove extra fluff from my notation, like line numbers and section names.
    noFluff = re.sub(r'\?|(\d+\-(\d+|ff|fin).*?\n)|\d', "", d)
    # remove notation of which character is speaking
    noActors = re.sub(r'(\n\*[^\s]*([ ]*|([ ]+(a|b|\*a|\*b)))\n)', "\n", noFluff)
    # take "--" and turn it into " --" to make sure we don't accidently
    # treat them as wrapping token.
    noExtraWrap = re.sub(r'\-\-', " --", noActors)
    # recombine tokens that have been wrapped
    fixWrapping = re.sub(r'\-[ ]*\n', "", noExtraWrap)
    # remove newlines
    noNewLines = removeNewlines(fixWrapping)
    # remove various "non-original" text.
    #noDubious = removeDubious(noNewlines) # the rare dubious sections are allowed for this analysis
    # remove non-beta-code characters and punctuation.
    allBetaCode = removeNonBetaCode(noNewLines)#noDubious)
    # fix spacing
    noEndSpace = fixSpacing(allBetaCode)
    final = noEndSpace
    return final


# decapitalize a line, plus a place for future word-by-word operations.
def handleTokens(l):
    split = re.split(r' ', l)
    newSplit = map(decapitalizeToken, split)
    return " ".join(newSplit)

# handle line-wide change operations
def handleLine(l):
    # remove a strange Perseus ?? notation;
    l = re.sub(r'\(\?\?\)', "a(", l)
    l = removeNewlines(l)
    l = removeNonBetaCode(l)
    l = fixSpacing(l)
    # need a space at the end for proper handling
    l += " "
    return l

# Given input text, clean it up, fix all the tokens, and return a list of the
# tokens and a sorted set of the unique tokens
def cleanAndFixLines(lines):
    tokens = []
    size = len(lines)
    for i in range(size):
        line = lines[i]
        text = line["text"]
        decap = handleTokens(text)
        noPunct = handleLine(decap)
        finalText = noPunct;
        line["text"] = finalText
        tokens.extend(finalText.split(" "))

    # this makes some changes to the text we don't want for scanning, but
    # do want for lemma scanning, so we do it later.
    standardizedTokens = map(fixToken, tokens)

    sortedUniqTokens = sorted(set(standardizedTokens))

    return (lines, standardizedTokens, sortedUniqTokens)

# Given input text, clean it up, fix all the tokens, and return a list of the
# tokens and a sorted set of the unique tokens
def cleanAndFixBlock(text):
    cleanText = cleanUpData(text)
    tokens = cleanText.split(" ")

    standardizedTokens = map(fixToken, tokens)

    sortedUniqTokens = sorted(set(standardizedTokens))

    return (standardizedTokens, sortedUniqTokens)

# get an html page
def getHtmlPage (url):
    opener = build_opener()
    tries = 0
    max_tries = 5
    while tries < max_tries:
        if (tries != 0):
            print "~~~~~TRYING AGAIN~~~~~"
        try:
            response = opener.open(url)
            return response.read()
        except HTTPError as e:
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
        except URLError as e:
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
        tries += 1
    raise Exception('Failed to get data from the server.')

# grab the TEI file at the given URL from Perseus; the result should be in
# betacode.
def get_TEI_XML (url):
    opener = build_opener()
    opener.addheaders.append(("Cookie", "disp.prefs=\"greek.display=PerseusBetaCode\"")) #|default.scheme=book:card|default.type=book
    tries = 0
    max_tries = 5
    while tries < max_tries:
        if (tries != 0):
            print "~~~~~TRYING AGAIN~~~~~"
        try:
            response = opener.open(url)
            #response = urlopen(req)
            xml = response.read()
            return xml
        except HTTPError as e:
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
        except URLError as e:
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
        tries += 1
    raise Exception('Failed to get data from the server.')

# Python's XML parser doesn't like Perseus including raw text and subchildren
# in the same element, so this extracts it from the line xml element
def getLineTextXML(xml):
    t = xml.text
    if (t):
        return t
    else:
        elementText = ET.tostring(xml)
        elementText = re.sub(r'<note.*?/note>', r'', elementText)
        lineText = re.sub(r'<[^>]*>', r'', elementText)
        return lineText

# parse the TEI data
def parse_TEI (xml, textName, book, byCard, cardStart):
    # grab all of the lines in the document
    data = ET.fromstring(xml)
    lines = []
    xmlLines = []
    if (byCard):
        lineStart = cardStart
    else:
        lineStart = 1

    lineNum = lineStart
    for lineXML in data.iter('l'):
        xmlLines.append(lineXML)
        lineText = getLineTextXML(lineXML)
        # print dubious , skip lines that have it
        m = re.search(r'(†.*?†)|(\[.*?\])|(<.*?>)', lineText)
        if not(m == None):
            print lineText[m.start():m.end()]
            #continue
        line = {"text": lineText, "poem": textName, "book": book, "line": lineNum}
        lines.append(line)
        lineNum += 1

    # aka no lines were parsed
    if (lineNum == lineStart):
        for lineXML in data.iter('p'):
            paragraphText = ET.tostring(lineXML)
            #remove notes
            paragraphText = re.sub(r'<note.*?/note>', r'', paragraphText)
            split = paragraphText.split("<lb")
            for line in split:
                if (line.startswith("<p")):
                    fixedLine = line
                else:
                    fixedLine = "<lb" + line;
                lineText = re.sub(r'<[^>]*>', r'', fixedLine)

                # print dubious , skip lines that have it
                m = re.search(r'((†|&#8224;).*?(†|&#8224;))|(\[.*?\])|(<.*?>)', lineText)
                if not(m == None):
                    print lineText[m.start():m.end()]
                    #continue
                # this fixes an issue with perseus where there is a weird 3 hanging out
                lineText = re.sub(r'\d', r'', lineText)
                # if the text has content
                if ((len(lineText) > 0) and not(lineText.isspace())):
                    line = {"text": lineText, "poem": textName, "book": book, "line": lineNum}
                    lines.append(line)
                    lineNum += 1


    return lines

# The Perseus XML requests cannot properly read diacritics, so we filter them
# out and only accept responses that match our original token with its
# diacritics.
def removeDiacritics(w) :
    return re.sub(r'\)|\(|/|=|\\|&|\+|\||\'|\d', '', w)


# given a dictionary to store lemmas, return a function that can be
# used with map to find parses for each token and store extra info about lemmas.
def getPerseusData (lemmaDict, printFailures):
    # given a token, return a tuple with the base token and a list of the lemma
    # results returned by Perseus with their data in a dictionary
    def fun (BaseToken):
        if (VERBOSE_PERSEUS):
            print BaseToken
        noDiacritics = removeDiacritics(BaseToken)
        baseURL = "http://www.perseus.tufts.edu/hopper/xmlmorph?lang=greek&lookup="
        url = baseURL + noDiacritics
        opener = build_opener()
        # we have to include this cookie so that we get results in betacode
        # (which is easy to parse) rather than unicode greek (harder to parse).
        opener.addheaders.append(("Cookie", "disp.prefs=\"greek.display=PerseusBetaCode\""))
        tries = 0
        max_tries = 5

        # we make a large number of calls, so often one or two will not go
        # through; to make sure this doesn't break everything, we try
        # multiple times before quitting.
        while tries < max_tries:
            if (tries != 0):
                print "~~~~~TRYING AGAIN~~~~~"
            try:
                response = opener.open(url)
                xml = response.read()
                analyses = ET.fromstring(xml)
                results = []
                numAnalyses = 0
                # given the response, convert it into a python dictionary
                # and store the lemmas found in the list of lemmas.
                for analysis in analyses:
                    numAnalyses += 1
                    if (analysis[0].text == BaseToken):
                        subDict = {}
                        for child in analysis:
                            subDict[child.tag] = child.text
                        lem = subDict["lemma"]
                        if (lem in lemmaDict):
                            lemmaDict[subDict["lemma"]].append(subDict["pos"])
                        else:
                            lemmaDict[subDict["lemma"]] = [subDict["pos"]]

                        results.append(subDict)
                if (numAnalyses == 0):
                    if (printFailures):
                        print ("No results for \"" + BaseToken + "\"")
                elif (len(results) == 0):
                    if (printFailures):
                        print numAnalyses, (" results but no matches for \"" + BaseToken + "\"")
                return (BaseToken, results)
            except HTTPError as e:
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
            except URLError as e:
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            except socketError as e:
                print "Socket Error: failed to reach server:"
                print sys.exc_info()[0]
            except:
                print "Unexpected error:", sys.exc_info()[0]
                raise
            tries += 1
        print "~~~~~Gave Up~~~~~"
        return (BaseToken, [])

    return fun

hasCircumflexRegex = re.compile('=')
hasAcuteRegex = re.compile('/')
# return true if the lemma is a short alpha stem
def isShortAlphaStem(lemma):
    # remove all consonants
    s = re.sub(r'[bcdfgjklmnpqrstvxyz]+', r'', decapitalizeToken(lemma))
    # if we have something like εΐ (ei+/), it is not a dipthong so split
    # the two vowels with a split symbol
    s = re.sub(r'([aeiouhw])\+', r'.\1', s)
    # modify dipthongs so the next step won't split them
    s = re.sub(r'((?:a|e|o|u)i|(?:a|o|e|h|w)u)', r'[\1]', s)
    s = re.sub(r'(a|e|o|u)i', r'.\1!', s)
    s = re.sub(r'(a|o|e|h|w)u', r'.\1@', s)
    # split all letters
    s = re.sub(r'(\w)', r'.\1', s)
    # unencode dipthongs
    s = re.sub(r'(a|e|o|u)!', r'.\1i', s)
    s = re.sub(r'(a|o|e|h|w)@', r'.\1u', s)
    # remove multiple splits
    s = re.sub(r'\.+', '.', s)
    split = re.split(r'\.', s)
    if (len(split) >= 2 and (re.search(hasCircumflexRegex, split[-2]) != None) or (len(split) >= 3 and re.search(hasAcuteRegex, split[-3]) != None)):
        return True
    else:
        return False

# bring the accent in a stem forwards one
def bringStemAccentForward(stem):
    if (re.search(r'/', stem) != None):
        stem = re.sub(r'/', '', stem)
        stem = re.sub(r'^(.*[aeiouwh])([^aeiouwh]*)', r'\1/\2', stem)
    else:
        stem = re.sub(r'=', '/', stem)
    return stem


# given a list of lemmas, run through them to determine stem-type information
# by running additional queries to Morpheus to determine whether the form
# is of a given stem type or not.
def getLemmaInfo(lemmas):
    sortedLemmas = sorted(lemmas.keys())

    lemmaResults = {}
    for lemma in sortedLemmas:
        noCapsLem = re.sub(r'\d', '', decapitalizeToken(lemma))
        val = lemmas[lemma]
        pos = sorted(set(val))
        cleanLem = removeDiacritics(lemma)
        myType = NO_TYPE
        getPdata = getPerseusData({}, False)
        # is this a feminine long-alpha stem?
        if (cleanLem[-1] == "h" and "noun" in pos): #fem alpha stripped_form
            genitiveForm = ""
            if (re.sub(r'\d', '', lemma)[-1] == "h"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-1] + "hs"
            elif (re.sub(r'\d', '', lemma)[-2:] == "h/"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-2] + "h=s"
            if (not(genitiveForm == "")):
                (_, forms) = getPdata(genitiveForm)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["gender"] == "fem" and form["case"] == "gen" and
                      form["number"] == "sg"):
                        myType = H_A_STEM
        # is this a feminine long-alpha stem with e/i/r before the alpha?
        elif ((cleanLem[-2:] == "ra" or cleanLem[-2:] == "ia" or
          cleanLem[-2:] == "ea") and "noun" in pos): #fem alpha stripped_form
            pluralForm = ""
            genitiveNeeded = True
            if (re.sub(r'\d', '', lemma)[-1] == "a"):
                pluralForm = decapitalizeToken(noCapsLem)[0:-1] + "ai"
                genitiveForm = bringStemAccentForward(decapitalizeToken(noCapsLem)[0:-1]) + "as"
            elif (re.sub(r'\d', '', lemma)[-2:] == "a/"):
                pluralForm = decapitalizeToken(noCapsLem)[0:-2] + "ai/"
                genitiveForm = decapitalizeToken(noCapsLem)[0:-2] + "a=s"
            if (not(pluralForm == "")):
                (_, forms) = getPdata(pluralForm)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["gender"] == "fem" and form["case"] == "nom" and
                      form["number"] == "pl"):
                        if (isShortAlphaStem(lemma)):
                            myType = EIR_SHORT_A_STEM
                            genitiveNeeded = False
                        else:
                            myType = EIR_A_STEM
                            genitiveNeeded = False
            if (genitiveNeeded and not(genitiveForm == "")):
                (_, forms) = getPdata(genitiveForm)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["gender"] == "fem" and form["case"] == "gen" and
                      form["number"] == "sg"):
                        if (isShortAlphaStem(lemma)):
                            myType = EIR_SHORT_A_STEM
                        else:
                            myType = EIR_A_STEM
        # is this a feminine short alpha stem?
        elif (cleanLem[-1:] == "a" and "noun" in pos): #fem short alpha
        #bringStemAccentForward(
            pluralForm = re.sub(r'\*', '', noCapsLem[0:-1]) + "ai"
            genitiveForm = bringStemAccentForward(decapitalizeToken(noCapsLem)[0:-1]) + "as"
            needGenitive = True
            (_, forms) = getPdata(pluralForm)
            for form in forms:
                if (form["lemma"] == lemma and form["gender"] == "fem" and
                  form["case"] == "nom" and form["number"] == "pl"):
                    myType = SHORT_A_STEM
                    needGenitive = False
            if (needGenitive):
                (_, forms) = getPdata(genitiveForm)
                for form in forms:
                    if (form["lemma"] == lemma and form["gender"] == "fem" and
                      form["case"] == "gen" and form["number"] == "sg"):
                        myType = SHORT_A_STEM
                        needGenitive = False

        # is this a masculine alpha stem?
        elif (cleanLem[-2:] == "hs" and "noun" in pos): #masc alpha stem
            genitiveForm = ""
            accusative_form = ""
            if (re.sub(r'\d', '', lemma)[-2:] == "hs"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-2] + "ou"
                accusative_form = decapitalizeToken(noCapsLem)[0:-2] + "hn"
            elif (re.sub(r'\d', '', lemma)[-3:] == "h/s"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-3] + "ou="
                accusative_form = decapitalizeToken(noCapsLem)[0:-3] + "h/n"
            needAccusative = True
            if (not(genitiveForm == "")):
                (_, forms) = getPdata(genitiveForm)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["gender"] == "masc" and form["case"] == "gen" and
                      form["number"] == "sg"):
                        myType = H_A_STEM
                        needAccusative = False
            if (needAccusative and not(accusative_form == "")):
                (_, forms) = getPdata(accusative_form)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["gender"] == "masc" and form["case"] == "acc" and
                      form["number"] == "sg"):
                        myType = H_A_STEM
        # is this a masculine alpha stem with e/i/r before the ending?
        elif ((len(cleanLem) >= 3) and (cleanLem[-3:] == "ras" or
          cleanLem[-3:] == "ias" or cleanLem[-3:] == "eas") and "noun" in pos):
            genitiveForm = ""
            if (re.sub(r'\d', '', lemma)[-2:] == "as"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-2] + "ou"
                accusative_form = decapitalizeToken(noCapsLem)[0:-2] + "hn"
            elif (re.sub(r'\d', '', lemma)[-3:] == "a/s"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-3] + "ou="
                accusative_form = decapitalizeToken(noCapsLem)[0:-3] + "h/n"
            needAccusative = True
            if (not(genitiveForm == "")):
                (_, forms) = getPdata(genitiveForm)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["gender"] == "masc" and form["case"] == "gen" and
                      form["number"] == "sg"):
                        myType = EIR_A_STEM
                        needAccusative = False
            if (needAccusative and not(accusative_form == "")):
                (_, forms) = getPdata(accusative_form)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["gender"] == "masc" and form["case"] == "acc" and
                      form["number"] == "sg"):
                        myType = EIR_A_STEM
        # is this a digamma stem? (basileus type)
        elif (cleanLem[-3:] == "eus" and "noun" in pos):
            genitiveForm = decapitalizeToken(lemma)[0:-4] + "e/ws"
            (_, forms) = getPdata(genitiveForm)
            for form in forms:
                if (form["lemma"] == lemma and ("case" in form) and
                  ("number" in form) and form["number"] == "sg" and
                  form["case"] == "gen"):
                    myType = W_STEM
        # is this a iota stem? (polis type)
        elif (cleanLem[-2:] == "is" and "noun" in pos):
            genitiveForm = ""
            if (re.sub(r'\d', '', lemma)[-2:] == "is"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-2] + "ews"
            elif (re.sub(r'\d', '', lemma)[-3:] == "i/s"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-3] + "e/ws"
            if (not(genitiveForm == "")):
                (_, forms) = getPdata(genitiveForm)
                for form in forms:
                    if (form["lemma"] == lemma and ("case" in form) and
                      ("number" in form) and form["number"] == "sg" and
                      form["case"] == "gen"):
                        myType = I_STEM
        # is this a 3-termination adjective?
        elif (cleanLem[-2:] == "os" and "adj" in pos):
            genitiveForm = ""
            keepGoing = True
            if (re.sub(r'\d', '', lemma)[-2:] == "os"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-2] + "ai"
                gf2Base = decapitalizeToken(noCapsLem)[0:-2]
                gf2Base = bringStemAccentForward(gf2Base)
                genitiveForm2 = gf2Base + "hs"
                genitiveForm3 = decapitalizeToken(noCapsLem)[0:-2] + "oi"
            elif (re.sub(r'\d', '', lemma)[-3:] == "o/s"):
                genitiveForm = decapitalizeToken(noCapsLem)[0:-3] + "ai/"
                genitiveForm2 = decapitalizeToken(noCapsLem)[0:-3] + "h=s"
                genitiveForm3 = decapitalizeToken(noCapsLem)[0:-3] + "oi/"
            if (not(genitiveForm == "")):
                (_, forms) = getPdata(genitiveForm)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["number"] == "pl" and form["case"] == "nom" and
                      form["gender"] == "fem"):
                        myType = ADJ_3_TERMINATION
                        keepGoing = False
            if (keepGoing and not(genitiveForm2 == "")):
                (_, forms) = getPdata(genitiveForm2)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["number"] == "sg" and form["case"] == "gen" and
                      form["gender"] == "fem"):
                        myType = ADJ_3_TERMINATION
                        keepGoing = False
            if (keepGoing):
                # is this some other 2nd decl  adjective]
                pluralForm = ""
                if (re.sub(r'\d', '', lemma)[-2:] == "os"):
                    pluralForm = decapitalizeToken(noCapsLem)[0:-2] + "oi"
                    genitiveForm = bringStemAccentForward(decapitalizeToken(noCapsLem)[0:-2]) + "ou"
                elif (re.sub(r'\d', '', lemma)[-3:] == "o/s"):
                    pluralForm = decapitalizeToken(noCapsLem)[0:-3] + "oi/"
                    genitiveForm = decapitalizeToken(noCapsLem)[0:-3] + "ou="
                if (not(pluralForm == "")):
                    (_, forms) = getPdata(pluralForm)
                    for form in forms:
                        if (form["lemma"] == lemma and
                          ("case" in form) and ("number" in form) and
                          form["number"] == "pl" and form["case"] == "nom"):
                            myType = ADJ_2ND_DECL
                            keepGoing = False
                if (keepGoing and not(genitiveForm == "")):
                    (_, forms) = getPdata(genitiveForm)
                    for form in forms:
                        if (form["lemma"] == lemma and
                          ("case" in form) and ("number" in form) and
                          form["number"] == "sg" and form["case"] == "gen"):
                            myType = ADJ_2ND_DECL
                            keepGoing = False
        # Is this a baru/s type adjective
        elif (lemma[-3:] == "u/s" and "adj" in pos):
            fem_form = re.sub(r'\*', '', noCapsLem[0:-3]) + "ei=a"
            if (not(fem_form == "")):
                (_, forms) = getPdata(fem_form)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["number"] == "sg" and form["case"] == "nom" and
                      form["gender"] == "fem"):
                        myType = ADJ_US
        elif (cleanLem[-3:] == "eis" and "adj" in pos):
            genitiveForm = re.sub(r'\*|/', '', noCapsLem[0:-3]) + "e/ssas"
            if (not(genitiveForm == "")):
                (_, forms) = getPdata(genitiveForm)
                for form in forms:
                    if (form["lemma"] == lemma and ("gender" in form) and
                      ("case" in form) and ("number" in form) and
                      form["number"] == "sg" and form["case"] == "gen" and
                      form["gender"] == "fem"):
                        myType = ADJ_EIS_ESSA
        # second declension noun
        elif (cleanLem[-2:] == "os" and "noun" in pos):
            if (re.sub(r'\d', '', lemma)[-2:] == "os"):
                genitiveForm_1 = bringStemAccentForward(decapitalizeToken(noCapsLem)[0:-2]) + "ou"
            elif (re.sub(r'\d', '', lemma)[-3:] == "o/s"):
                genitiveForm_1 = decapitalizeToken(noCapsLem)[0:-3] + "ou="
            form1Worked = False
            if (not(genitiveForm_1 == "")):
                (_, forms) = getPdata(genitiveForm_1)
                for form in forms:
                    if (form["lemma"] == lemma and ("case" in form) and
                      ("number" in form) and form["number"] == "sg" and
                      form["case"] == "gen"):
                        myType = O_STEM
                        form1Worked = True
            if not(form1Worked):
                if (re.sub(r'\d', '', lemma)[-2:] == "os"):
                    genitiveForm_2 = decapitalizeToken(noCapsLem)[0:-2] + "ous"
                elif (re.sub(r'\d', '', lemma)[-3:] == "o/s"):
                    genitiveForm_2 = decapitalizeToken(noCapsLem)[0:-3] + "ou=s"
                form1Worked = False
                if (not(genitiveForm_2 == "")):
                    (_, forms) = getPdata(genitiveForm_2)
                    for form in forms:
                        if (form["lemma"] == lemma and ("case" in form) and
                          ("number" in form) and form["number"] == "sg" and
                          form["case"] == "gen"):
                            myType = S_STEM

        # set the type.
        lemmaResults[lemma] = myType
    return lemmaResults

# get the form and lemma data for the given set of (unique) tokens
# include whether to get the information from perseus or from files
# and the filenames to get the form and lemma data
def getFormAndLemmaData(tokenList, fromPerseus, formDataFn, lemmaDataFn):
    # if we get it from Perseus' Morpheus, just run queries for each token
    if (fromPerseus):
        lemmas = {}
        formData = map(getPerseusData(lemmas, True), tokenList)

        lemmaData = getLemmaInfo(lemmas)
    # if we have preprocessed, get the information from the given files.
    else:
        formDataFile = open(formDataFn, 'r')
        formDataContents = formDataFile.read()
        formDataFile.close()
        formData = json.loads(formDataContents)

        lemmaDataFile = open(lemmaDataFn, 'r')
        lemmaDataContents = lemmaDataFile.read()
        lemmaDataFile.close()
        lemmaData = json.loads(lemmaDataContents)

    # reconstruct the form data dictionary (which is corrupted by the
    # conversion to json and back)
    formDataDict = {}
    for fi in formData:
        form = fi[0]
        formInfo = fi[1]
        if (form in tokenList):
            formDataDict[form] = formInfo
    return (formDataDict, lemmaData)
