# -*- coding: utf-8 -*-
# this file contains the code for processing the raw dictionary entry.
from ..shared import utils
import xml.etree.ElementTree as ET
import json
import re
import copy

VERBOSE = False#True
VERY_VERBOSE = False

# handle some improper encoding from Perseus
def getStringSafe(entry):
    enc = entry.encode('utf-8')
    try:
        return ET.fromstring(enc), True
    except ET.ParseError:
        try:
            newEnc = re.sub(r'key="([^"]*)<([^"]*)>([^"]*)"', r'key="\1\2\3"', enc)
            return ET.fromstring(newEnc), True
        except ET.ParseError:
            try:
                newEnc2 = re.sub(r'key="([^"]*)<([^"]*)>([^"]*)"', r'key="\1\2\3"', newEnc)
                return ET.fromstring(newEnc2), True
            except ET.ParseError:
                raise Exception("Invalid XML: \n" + enc)

# parse the list of senses
def parseSenses(senses):
    s = ""
    for sense in senses:
        s += ET.tostring(sense)
    return s

# given text, generate the division with proper vowel lengths
def generateDivision(text):
    text = re.sub(r'([aiu])', r'\1[?]', text)
    text = re.sub(r'([eo])', r'\1[s]', text)
    text = re.sub(r'([hw])', r'\1[l]', text)
    return text

# given an entry, get the text in a parsable manner
def getCoreText(entry):
    coreText = ET.tostring(entry)
    coreText = re.sub(r'<sense', r'$$<sense', coreText, count=1)
    # determine sense split
    coreText = re.sub(r'<[^>]*>', r'', coreText)
    # remove tags
    coreText = re.sub(r'<[^>]*>', r'', coreText)
    # spaces after commas
    coreText = re.sub(r',([^\s])', r', \1', coreText)
    # &#65288;  -> (
    coreText = re.sub(r'&#65288;', r'(', coreText)
    # &#65289; -> )
    coreText = re.sub(r'&#65289;', r')', coreText)
    return coreText

# regular expressions for a variety of special cases for getting the "top"
# text for an entry, which is basically the beginning of the text.
# these are explained in the corresponding if statements below
vMRe = re.compile("(^[^\s]*w[,\s])|(^[^\s]*o/?mai[,\s])")
m1Re = re.compile(":—")
m1_1Re = re.compile(":&#8212;")
m2Re = re.compile("^[^\s]* \(\$\$.*?\), (o\(|h\(|to/|oi\(|ai\(|ta/)")
m2_1Re = re.compile("^[^\s]*( \[[^\]]*\])?, [^\s]+os \((also )?\$\$.*?\), (o\(|h\(|to/|oi\(|ai\(|ta/)")
m2_2Re = re.compile("^[^\s]*( or [^\s]*)? \((cf\. )?\$\$.*?\)( \[[^\]]*\])?, Adv\.")
m2_3Re = re.compile("^[^\s]*( \[[^\]]*\])?(, [^\s]*os)? \(.*?\$\$.*?\), (o\(|h\(|to/|oi\(|ai\(|ta/)[,\.\s]")
m2_4Re = re.compile("\$\$, (o\(|h\(|to/|oi\(|ai\(|ta/)[,\.\s]")
m3Re = re.compile("^[^\s]*:")
m4Re = re.compile("\$\$")

# given core text, get the "top" text, which specifies the grammar
# of the form.
def getTopText(core):
    verbMatch = not(re.search(vMRe, core) == None)
    match1 = re.search(m1Re, core)
    match1_1 = re.search(m1_1Re, core)
    #:&#8212;
    match2 = re.search(m2Re, core)
    match2_1 = re.search(m2_1Re, core)
    match2_2 = re.search(m2_2Re, core)
    match2_3 = re.search(m2_3Re, core)
    match2_4 = re.search(m2_4Re, core)
    match3 = re.search(m3Re, core)
    match4 = re.search(m4Re, core)
    # if ":—" is in the text and this is a verb, split on that
    if (verbMatch and not(match1 == None)):
        return core.split(":—")[0]
    # same as above, just different encoding
    elif (verbMatch and not(match1_1 == None)):
        return core.split(":&#8212;")[0]
    # if we have a single word followed by parentheses with a split into senses,
    # then a gender marker, split to include the gender marker
    elif (not(match2 == None)):
        return core[0:match2.end()]
    # if we have a consonant stem followed by parentheses with a split into
    # senses, then a gender marker, split to include the gender marker
    elif (not(match2_1 == None)):
        return core[0:match2_1.end()]
    # if we have an adverb with parentheses that would be split, split
    # after the adv marker
    elif (not(match2_2 == None)):
        return core[0:match2_2.end()]
    # if we have a break in the middle of parens, followed by a gender,
    # include the gender
    elif (not(match2_3 == None)):
        return core[0:match2_3.end()]
    # if we a gender right after the break, include that
    elif (not(match2_4 == None)):
        return core[0:match2_4.end()]
    # if we have a single word followed by : to start, just take the single word
    elif (not(match3 == None)):
        return core.split(":")[0]
    # otherwise, split on first sense if it exists
    elif (not(match4 == None)):
        return core.split("$$")[0]
    # otherwise, split on ":"
    else:
        return core.split(":")[0]

# get the top text plus the next 20 characters (for debugging)
def getTopPlus20(core, top):
     size = min(len(core), len(top) + 20)
     return core[0:size]

# given core text, get the initial text corresponding to the first word
def getStartText(core):
    init = core.split(" ")[0]
    # remove punctuation
    start = re.sub(r'[,\.:]', r'', init)
    endDash = False
    if start[-1] == "-":
        endDash = True
    start = re.sub(r'[\-]', r'', start)
    if endDash:
        start += "-"
    return start


# handles some modifications to start and core
def coreStartExceptions(core, start):
    # these are not actually a new word in the dictionary, just improperly
    # split from the previous word so just skip them .
    if (start == "gnaq-") or (start == "el-") or (start == "iso-") or (start == "qwrhk-") or (start == "prwto/moir-"):
        return "", "", True


    if (start == "blefa^roto/-"):
        start = "blefa^roto/mon"
        core = re.sub(r'blefa\^roto/- mon', r'blefa\^roto/mo', core)
    elif (start == "i)soda_miorgo/s"):
        # to properly render #ϝiso
        core += "iso- "
    elif (start == "meso/tomos-"):
        start = "meso/tomos"
    elif (start == "o)nei/raut-"):
        start = "o)neirautoptiko/s"
    elif (start == "mu^ropw/lion"):
        core += " mu^ro-ei=on), to/, $$perfumer's shop, Lys.24.20, D.25.52, 34.13, Hyp.Ath.6, Phld.Ir. p.47 W."
    elif (start == "a)nayhla?/fhsls"):
        start = "a)nayhla?/fhsis"
        core = re.sub(r'a\)nayhla\?/f-hsls', r'a)nayhla?/f-hsis', core)
    elif (start == "a)pobi/wsls"):
        start = "a)pobi/wsis"
        core = re.sub(r'a\)pobi/-wsls', r'a)pobi/-wsis', core)

    # if this is a prefix, just continue
    if (start[-1] == "-"):
        return "", "", True

    return core, start, False


# does this match a pattern for one word being linked to another?
# the first is a pattern, the second is whether to match against with $$ removed
linkMatches = [
# for unspecified words that just reference a synonym,
# we skip for now
[re.compile("^[^\s]*( \(.*?\))?:"), False],
# for words that are just variants that point to the common variant
# we skip for now
[re.compile("^(((i\.e\. )?[^\s]*(, contr\. [^,\s]*)?, )+(for|Ep\. forms from|(Dor\.|Aeol\.|Lacon\.|Ep\.|Ion\.|Att\.|Boeot\.)( word)? for) ((and )?[^\s]*( \(q\. v\.\))?([\s]*\(prob\. Lacon\.\))?, )*[^\s]*( \(q\. v\.\))?(, esp\. in sense of .*$|\.[\s]*))(((i\.e\. )?[^\s]*, )+(for|Ep\. forms from|(Dor\.|Aeol\.|Lacon\.|Ep\.|Ion\.)( word)? for) ((and )?[^,;]*( \(q\. v\.\))?([\s]*\(prob\. Lacon\.\))?, )*[^\s]*( \(q\. v\.\))?\.[\s]*)*(; cf [^\s]*\.)?$"), False],
[re.compile("^((i\.e\. )?[^\s]*( \([A-Z]\))?, )+(=) ([^\s]*( \(q\. v\.\))?(, )?)"), True],
# mnasth/r, v. mnhst-
[re.compile("^(([^\s]*( \((gen)\. (pl)\.\))?( \[[^\]]*\])?, )+(etc\., )?((Ep\.|Aeol\.|Dor\.|Ion\.|Att\.|Boeot\.|contr\.)( for)? [^\s]*, )?((v\.|=) (sub )?([^\s]*, )*[^\s]*( ([1Il]+))?(, Hsch| [A-Z]\. \d+\.\d+| sub init| &#65288;[^&\s]*&#65289;)?\.[\s]*)+)+$"), True],
# mu^o-galh=, $$v.l. for mugalh= in Dsc.2.68. (([A-Z][a-z]*|[\d]+)\.){2-3}[\d]+
[re.compile("^[^\s]*( \((dat|acc|gen)\. (sg|pl)\.\))?, ((freq\. |prob\. )?f\.l\.|v\.l\.|written) for [^\s]*( [^\s]*\.?)?(, aor\. inf\. of [^,\.\s]+)?([A-Z]\.[A-Z0-9]+)?( or [^\s]*)?( \(v\. [^\s]+( [A-Z])?\))?,?((((( [A-Z][a-z]*)? [A-Z][a-z]*\.)? (in|ap\.))? (([A-Z]+[a-z]*[\d]*|[\d]+[a-z]?)\.?){1,4}([a-zA-Z0-9]*: in Gloss\. expld\. by murex|; c\.?f\. [^\s]+( \([A-Z]\))?| [A-Z]|\. s\.v\. [^,\.\s]+|,[\s]+=[\s]+(([A-Z]+[a-z]*[\d]*|[\d]+[a-z]?)\.?){1,4})?)| q\.[\s]*v|( \(q\.[\s]*v\.\)(, (Erot|which is to be preferred))?)|( [A-Z][a-z]*\., [A-Z][a-z]*\. [^,\.\s]+, v\. [^,\.\s]+))?\.$"), True],
# bleg, poet. and Dor. for bleg, stuff citations stuff
[re.compile("^[^\s]*( \([A-Z]\))?(, [^\s]*)?( \[[a-z\^_]*\])?(, i\.[\s]*e\. [^\s]*)?( or [^,\s]+)?,[\s]*((( (and )?(Ep\.|Dor\.( \(Lacon\.\))?|Aeol[,\.]|poet\.|Ion\.|Att\.|Boeot\.|contr\.|corrupt)(,)?)+[\s]*for|gloss on)[\s]+[^\s]*( \(q\.[\s]*v\.\))?([,:] |\.))"), True],
# ai)/ke [e^], ai)/ken, poet. and Dor. for e)a/n
[re.compile("^([^\s]*([\s]+\[[^\]]*\])?,[\s]*)+( (and )?(Ep\.|Dor\.|Aeol\.|poet\.|Ion\.|Att\.|Boeot\.))+ for [^\s]*\."), True],
[re.compile("^[^\s]*, (part\. of|late form for) [^\s]*[\.,]"), True],
[re.compile("^[^\s]*, ((Ep\.|Aeol\.|Dor\.|Ion\.) dat\.|pf\.) of [^\s]*(, [A-Z][a-z]*\.\d+\.\d+)?\."), True],
# a, v. b. c, v. d.      and so on
[re.compile("^([^\s]*, v\.[\s]+[^\s]*( \([A-Z]\))?( \([^\.]*?\))?\.[\s]*)+$"), True],
# verb forms, e.g. a)/gerqen, Dor. and Ep. 3pl. aor. 1 Pass. of a)gei/rw.
[re.compile("^([^\s]*([\s]+\[[^\]]*\])?,[\s]*)+( es, e,)?(for [^,\.\s]+, )?([\s]*(but [^,\s]*,[\s]*)?( inf\. of the)?([\s]*( and )?(Ep\.|Dor\.|Aeol\.|poet\.|Ion\.|Att\.|Boeot\.))*([\s]+([1-3])(sg|pl)\.)?([\s]*(opt)\.)?([\s]*(aor|fut|impf|pf|plpf)\.([\s]+[1-2])?)?([\s]+(inf|imper)\.)?([\s]+iterative)?([\s]+(Act|Pass|Med)\.)?[\s]+(of|for)[\s]+[^\s]*([\s]+(\(q\.[\s]*v\.\)|q\.[\s]*v|v\.[\s]+[^,\.\s]*|)|, ([A-Z][a-z]*\.?)+\d+ (\(v\.l\. [^,\.\s]+\))?)?[\.:,])+$"), True],
# noun forms, e.g. na=as, Dor. acc. pl. of nau=s (q.v.).
[re.compile("^[^\s]*,([\s]*(but [^,\s]*,[\s]*)?([\s]*( and )?(Ep\.|Dor\.|Aeol\.|poet\.|Ion\.|Att\.|Boeot\.))*([\s]+(acc|dat|gen)\.)?([\s]+(neut)\.)?([\s]+(sg|pl)\.)?[\s]+(of|from)[\s]+[^\s]*( \(q\.[\s]*v\.\)| q\.[\s]*v)?([\s]*v\. [^,\.\s]*)?[\.:])+$"), True],
# a, b, c, poet. forms, v. d.
[re.compile("^([^\s]+, )+(poet)\. forms, v\. [^\s]+\.$"), True],
# a, acc. sg., dual b, pl. c; v. d.
[re.compile("^[^\s]+, acc\. sg\., dual [^\s]+, pl\. [^\s]+; v\. [^\s]+\.$"), True],
]



#potential central pattern strings
patternStrings = [
    # to break this down; we start with spaces, then potentially
    # have a group of the form [a_ i^] or so specifying lengths,
    # then a number of  Ionic/Attic/Doric variants with their own
    # lengths, a reference (e.g. Alc.125) and stuff in parens;
    # then potentially just a set of parentheses with some other
    # data in it, which seems to specify the form the lexeme is a
    # contract of, or another dialect form; then another set of
    # potential lengths
    "[\s]*(\[[^\]]*\])?(,?[\s]+(or|Ion\.|Att\.|Dor\.|Ep\.|Aeol\.|poet\.)( contr.)?[\s]*[^\s]*([\s]*\[[^\]]*\])?(, hs)?([\s]*[A-Za-z]+[\d]*\.[\d]+(.[\d]+)?)?([\s]*\(.*?\)(?=[,\s]))?)*(, etc\.)?([\s]+\(.*?\)(?=[,\s]))?([,\s]*\[[^\]]*\])?",
    ""
]

# format: regex string, result type, whether to print results.
possibleClassifications = [
    [ # indeclinable
        ["indecl\.",""],
        1,
        utils.ENDING_TYPES.INDECLINABLE,
        False
    ],
    [ # adverb
        ["[Aa]dv\.",""],
        1,
        utils.ENDING_TYPES.ADVERB,
        False
    ],
    [ # two-termination adjective
        ["o/?s","[\s]*,[\s]*o/?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION,
        False
    ],
    [ # two-termination adjective ws, wn, contract from a-os, a-on
        ["w[/=]?s","[\s]*,[\s]*w[/=]?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_A_CONTRACT,
        False
    ],
    [ # two-termination adjective contract from o-os, o-on
        ["ou[/=]?s","[\s]*,[\s]*ou[/=]?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_O_CONTRACT,
        False
    ],
    [ # two-termination adjective plural
        ["oi[/=]?","[\s]*,[\s]*a[/=]?"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION,
        False
    ],
    [ # three-termination adjectives; alpha
        #r'o/?s[\s]*(\[[^\]]*\])?[\s]*,[\s]*a/?[\s]*,[\s]*o/?n',
        ["o/?\^?s","[\s]*,[\s]*a/?[\s]*,[\s]*o/?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A,
        False
    ],
    [ # three-termination adjectives; eta
        #r'o/?s[\s]*(\[[^\]]*\])?[\s]*,[\s]*h/?[\s]*,[\s]*o/?n',
        ["o/?\^?s","[\s]*,[\s]*h/?[\s]*,[\s]*o/?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H,
        False
    ],
    [ # three-termination adjectives; alpha w/ contraction
        ["ou=?s","[\s]*,[\s]*a=?[\s]*,[\s]*ou=?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A_E_CONTRACT,
        False
    ],
    [ # three-termination adjectives; eta w/ contraction
        #r'o/?s[\s]*(\[[^\]]*\])?[\s]*,[\s]*h/?[\s]*,[\s]*o/?n',
        ["ou=?s","[\s]*,[\s]*h=?[\s]*,[\s]*ou=?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H_E_CONTRACT,
        False
    ],
    [ # three-termination adjectives plural
        #r'o/?s[\s]*(\[[^\]]*\])?[\s]*,[\s]*h/?[\s]*,[\s]*o/?n',
        ["oi[/=]?","[\s]*,[\s]*ai[/=]?[\s]*,[\s]*a[/=]?"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H,
        False
    ],
    [ # 3rd declension adjective in -hs (e.g. eu)genh/s)
        #r'h/?s[\s]*(\[[^\]]*\])?[\s]*,[\s]*e/?s',
        ["h/?s","[\s]*,[\s]*e/?s"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_HS,
        False
    ],
    [ # 3rd declension adjective in -wn (e.g. eu)dai/mwn)
        #r'w/?n[\s]*(\[[^\]]*\])?[\s]*,[\s]*o/?n',
        ["w/?n","[\s]*,[\s]*o/?n([\s]*[,:])"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_WN,
        False
    ],
    [ # 3rd declension adjective in -us (e.g. baru/s)
        #r'u/?s[\s]*(\[[^\]]*\])?([\s]*,[\s]*ei=a)?[\s]*,[\s]*u/?',
        ["u/?\^?s","([\s]*,[\s]*[^\s]*ei=?a( \(?Ion\. [^\s]+\)?)?)?[\s]*,[\s]*[^\s]*u/?([\s]*[,:])"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US,
        False
    ],
    [ # 3rd declension participial adjective in -wn, ousa, on (including contract -wn, wsa, wn)
        #r'u/?s[\s]*(\[[^\]]*\])?([\s]*,[\s]*ei=a)?[\s]*,[\s]*u/?',
        ["w[/=]?n","([\s]*,[\s]*[^,\.\s]*ou[=/]?sa[\s]*,[\s]*[^,\.\s]*o/?n|[\s]*,[\s]*w[=/]?sa[\s]*,[\s]w=?n|[\s]*,[\s]participial form)"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_WN,
        False
    ],
    [ # 3rd declension adjective in -eis, essa, en
        # error when e/n is read as e)n in (e)gka^to/eis), so we
        # have to correct
        ["(o/)?ei[/=]?s","[\s]*,[\s]*(o/)?e[/=]?ss?[/=]?a[\s]*,[\s]*(o/)?e[/\)]?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA,
        False
    ],
    [ # 3rd declension adjective in -eis, essa, en with o contract
        ["ou=s","[\s]*,[\s]*ou=ssa[\s]*,[\s]*ou=n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA_O_CONTRACT,
        False
    ],
    [ # 3rd declension adjective in -as, -aina, -an
        ["a[/=]?_?s","[\s]*,[\s]*ai=?na[\s]*,[\s]*a/?\^?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.MIXED_AS_AINA,
        False
    ],
    [ # 3rd declension adjective ending in pous
        # appears to be an encoding error with a)e/rsipons where
        # "-πους" is read "-πονς", so handle that too
        ["^[^\s]*po[un]s, o\(, h\((, poun, to/,)?", ""],
        1,
        utils.ENDING_TYPES.ADJECTIVE.POUS_FOOT,
        False
    ],
    [ # adjectives in -is -i
        ["^[^\s]*is", "[\s]*,[\s]*i"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.IS_I,
        False
    ],
    [ # adjectives in -pas -pasa -pan
        ["^[^\s]*pa[=_]?s", "[\s]*,[\s]*[^,\.\s]*a[=_]?sa( \(.*?\)(?=,))?[\s]*,[\s]*[^,\.\s]*a[=^]?n"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.PAS,
        False
    ],
    [ # 3rd declension adjective in -eis, essa, en
        # error when e/n is read as e)n in (e)gka^to/eis), so we
        # have to correct
        ["w[/=]?s","[\s]*,[\s]*ui[=]?a[\s]*,[\s]*o/?s"],
        0,
        utils.ENDING_TYPES.ADJECTIVE.MIXED_WS_UIA_OS,
        False
    ],
    [ # 1st declension noun in -a
        # two possibilities, o(/h(, no a=?s, or a=?s, maybe o(/h(;
        #r'a/?\^?[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?[\s]*,[\s]*(a=?s|o\(|h\(?)[,\s]',
        ["a/?[_\^]?","([\s]*,[\s]*(a=?s|o\(|h\(?)([,\s]|$)|[\s]*,[\s]*fem\. of)"],
        0,
        utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
        False
    ],
    [ # 1st declension noun in -h
        #r'h/?[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?[\s]*,[\s]*h\(',
        # need : for kuneh
        # note la^bh( for la^bh/ presumably
        ["h[/=\(]?","([\s]*,[\s]*h[=]?s)?[\s]*([,:][\s]*|[\s]+)h[\(,]"],
        0,
        utils.ENDING_TYPES.NOUN.FIRST_H,
        False
    ],
    [ # 1st declension noun in -h/-a, plural
        #r'h/?[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?[\s]*,[\s]*h\(',
        ["ai/?","([\s]*,[\s]*w=?n)?[\s]*,[\s]*ai\(?"],
        0,
        utils.ENDING_TYPES.NOUN.FIRST_H,
        False
    ],
    [ # 2nd declension noun in -os
        #r'^[^\s]*o/?s[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?[\s]*(,[\s]*ou[\s]*)?,[\s]*(o\(|h\()',
        # can potentially have nominative in -ous; a)na/rrous
        ["^[^\s]*o[u]?[/=]?s","([\s]*,[\s]*ou[/=]?)?[\s]*,[\s]*(o\(|h\()"],
        0,
        utils.ENDING_TYPES.NOUN.SECOND_OS,
        False
    ],
    [ # 2nd declension noun in -os, plural
        #r'oi/?[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]+or[\s]+[^\s]*-)?[\s]*,[\s]*(oi\(|ai\()',
        ["oi/?","([\s]*,[\s]*w=?n)?[\s]*,[\s]*(oi[,\(]|ai\()"],
        0,
        utils.ENDING_TYPES.NOUN.SECOND_OS,
        False
    ],
    [ # 2nd declension noun in -hs
        # unfortunately there seems to be a type on thigns like
        # a)gku^loxei/lhs where ou is written "on"
        #r'h/?s[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*(,[\s]*o[un]=?[\s]*)?,[\s]*(o\(|h\()',
        ["h[/\\\\]?s","([\s]*,[\s]*o[un]=?)?[\s]*,[\s]*(o\(|h\()"],
        0,
        utils.ENDING_TYPES.NOUN.SECOND_HS,
        False
    ],
    [ # 2nd declension noun in -hs, plural
        #r'ai/?[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*,[\s]*oi\(',
        ["ai/?","([\s]*,[\s]*w=n)?[\s]*,[\s]*oi\("],
        0,
        utils.ENDING_TYPES.NOUN.SECOND_HS,
        False
    ],
    [ # 2nd declension noun in -as
        # unfortunately there seems to be a type on things like
        # a)gku^loxei/lhs where ou is written "on"
        #r'a/?s[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*(,[\s]*o[un]=?[\s]*)?,[\s]*(o\(|h\()',
        ["a/?s","[\s]*(,[\s]*o[un]=?( \([^\)]*\))?[\s]*)?,[\s]*(o\(|h\(|masc\.|$)"],
        0,
        utils.ENDING_TYPES.NOUN.SECOND_AS,
        False
    ],
    [ # 2nd declension noun in -on
        #r'o/?n[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*(,[\s]*ou[\s]*)?,[\s]*to/',
        ["o/?n","[\s]*(,[\s]*ou[\s]*)?,[\s]*to(/|,)"],
        0,
        utils.ENDING_TYPES.NOUN.SECOND_ON,
        False
    ],
    [ # 2nd declension noun in -on; contract
        #r'o/?n[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*(,[\s]*ou[\s]*)?,[\s]*to/',
        ["ou=?n","[\s]*(,[\s]*ou=?[\s]*)?,[\s]*to(/|,)"],
        0,
        utils.ENDING_TYPES.NOUN.SECOND_ON,
        False
    ],
    [ # 2nd declension noun in -on, plural
        #r'a\^?[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*,[\s]*ta/',
        ["a/?\^?","([\s]*,[\s]*(i/)?w=?n)?[\s]*,[\s]*ta/"],
        0,
        utils.ENDING_TYPES.NOUN.SECOND_ON,
        False
    ],
    [ # 3rd declension consonant stem (look for the repetition?)
        #r'[,\s]+[^\s]*o/?s[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*,[\s]*(o\(|h\(|to/)',
        ["[,\s]+[^\s]*o/?s","([\s]*,[\s]*contr\. [^\s]*)?[\s]*(,[\s]*|[\s]+)(o\(|h\(|to/|fem\.)"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        False
    ],
    [ # 3rd declension consonant stem, with genitive spelled out
        #r'[,\s]+[^\s]*o/?s[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*,[\s]*(o\(|h\(|to/)',
        ["[^\s]*","[\s]*,[\s]*gen\.[\s]+[^\s]*o/?s([\s]*,[\s]*(o\(|h\(|to/))?"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        False
    ],
    [ # 3rd declension consonant stem, with gender cut off
        #r'[,\s]+[^\s]*o/?s[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*,[\s]*(o\(|h\(|to/)',
        ["^[^\s]*","[\s]*os$"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        False
    ],
    [ # 3rd declension consonant stem, low info; just a)h/r, a)e/ros for example,
        # rather than a)-, h)h/r or some such
        #r'[,\s]+[^\s]*o/?s[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*,[\s]*(o\(|h\(|to/)',
        ["^[^\s]*( \[[^\]]*\])?, [^\s]*o/?s(,| :)",""],
        1,
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        False
    ],
    [ # 3rd declension consonant stem; of type swma, but appears shortened?
        #r'a/?[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*,[\s]*to/',
        ["a/?","[\s]*,[\s]*to/"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        False
    ],
    [ # 3rd declension -c stuff o()
        ["^[^\s]*c", "[\s]*,[\s]*o\("],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        False
    ],
    [ # 3rd declension consonant stem plural
        ["^[^\s]*es","([\s]*,[\s]*[^,\.\s]*w[=]?n)?[\s]*,[\s]*(oi\(|ai\()"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        False
    ],
    [ # 3rd declension epsilon stem
        ["os","[\s]*,[\s]*eos[\s]*,[\s]*to/"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_EPSILON,
        False
    ],
    [ # 3rd declension iota stem (polis, polews)
        # note a)po/-sxesis, ***c***ws, h(, ; a)poti?m-hsis, ews, h****)****,
        ["i(\+)?s","([\s]*(,|[\s])[\s]*[ec]/?ws)?[\s]*(,[\s]*|[\s]+)(o\(|h[\(\)])"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_IOTA,
        False
    ],
    [ # 3rd declension iota stem alternate check
        # of type ziggi/beis, ews <JUNK JUNK> o(, h(
        ["^[^\s]*is","[\s]*,[\s]*ews(,| \()"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_IOTA,
        False
    ],
    [ # 3rd declension iota stem plural
        ["^[^\s]*eis","[\s]*,[\s]*ewn(,| \()"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_IOTA,
        False
    ],
    [ # 3rd declension iota stem, neuter (kinna/bari)
        ["^[^\s]*i\^?","([\s]*,[\s]*ews)?, to/"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_IOTA,
        False
    ],
    [ # 3rd declension sigma stem neuter (genos, genous)
        ["o/?s","[\s]*,[\s]*ous[\s]*,[\s]*to/"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_SIGMA_N,
        False
    ],
    [ # 3rd declension sigma stem m/f (swkraths, swkratous)
        ["hs","[\s]*,[\s]*ous[\s]*,[\s]*(o\(|h\()"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_SIGMA_MF,
        False
    ],
    [ # 3rd declension digamma stem (basileus, basilews)
        ["^[^\s]*eu[/\\\\]s(?=[,\s\(])","[\s]*(,[\s]*e/ws[\s]*)?"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_DIGAMMA,
        False
    ],
    [ # 3rd declension digamma stem plural
        #r'eu/s[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*(,[\s]*e/ws[\s]*)?',
        ["(ei|h)=s","([\s]*,[\s]*e/wn)?[\s]*,[\s]*(oi\(|ai\()"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_DIGAMMA,
        False
    ],
    [ # 3rd declension -ou=s genitive
        #r'eu/s[\s]*(\[[^\]]*\])?([\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?([\s]*\[[^\]]*\])?[\s]*(,[\s]*e/ws[\s]*)?',
        ["w/","[\s]*,[\s]*ou=s[\s]*,[\s]*(o\(|h\()"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_OUS,
        False
    ],
    [ # 3rd declension -es, -ous, to/ (seems to just be a)ndro/sakes)
        ["es","[\s]*,[\s]*ous[\s]*,[\s]*to/"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_ES_OUS_TO,
        False
    ],
    [ # 3rd declension -i, to/ (seems to just be a few words )
        ["i/?","[\s]*,[\s]*to/"],
        0,
        utils.ENDING_TYPES.NOUN.THIRD_I_TO,
        False
    ],
    [ # Verb ending in -w; will check for contracts in later step
        # also note a(li/zw(A)
        ["[^\s]*w[=]?(\([A-Z]\))?(\[[^\[]*\])?[,\.\s]",""],
        1,
        utils.ENDING_TYPES.VERB.THEMATIC,
        False
    ],
    [ # Verb ending in -on; usually an aorist
        # also note a(li/zw(A)
        ["[^\s]*on,( aor\. [12],)? inf\. [^\s]*ei=?n",""],
        0,
        utils.ENDING_TYPES.VERB.THEMATIC,
        False
    ],
    [ # Verb ending in -omai; will check for contracts in later step
        #r'[^\s]*[oa]\^?/?mai[,\s]',
        ["[^\s]*([aeowh][\^_]?|ei)[/=]?mai[_]?[,\s]",""],
        1,
        utils.ENDING_TYPES.VERB.DEPONENT,
        False
    ],
    [ # Verb ending in -umi or -umai;
        ["[^\s]*u[_=\^]?ma?i[,\s]",""],
        1,
        utils.ENDING_TYPES.VERB.UMI,
        False
    ],
    [ # athematic verbs
        ["[^\s]*(h_?|w|ei)mi[,\s]",""],
        1,
        utils.ENDING_TYPES.VERB.ATHEMATIC,
        False
    ],
    [ # compounds of oida
        ["^[^\s]*oida,",""],
        0,
        utils.ENDING_TYPES.VERB.OIDA,
        False
    ],
    [ # Verbal adjective
        ["^[^\s]*t-?e/(on|a)[,\s]",""],
        1,
        utils.ENDING_TYPES.VERBAL_ADJECTIVE,
        False
    ],
    [ # Participle of -wn, ousa, on type
        ["^[^\s]*w[/=]?n","[\s]*,[\s]*ou[/=]?sa([\s]*,[\s]*(o[/=]?n|participial form))?"],
        0,
        utils.ENDING_TYPES.PARTICIPLE.WN,
        False
    ]
    #
]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# if none of the first round checks work, try these second
# round checks.
# the first item is a regex string to use to match
# the second is the type to use if successful
# the third is whether to use just the "top" piece (True) or the
# whole core.
# the fourth is a printing flag
secondRoundClassifications = [
    [ # 1st declension fem adj in -a
        "^[^\s]*a, fem\. Adj\.",
        utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A,
        True,
        False
    ],
    [ # 1st declension fem adj in -h
        "^[^\s]*h, fem\. Adj\.",
        utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H,
        True,
        False
    ],
    [ # 1st declension noun in -a; of type sofi/i;
      # specific example is a)dialhyi/a
        "^[^\s]*i/?a[,\s]",
        utils.ENDING_TYPES.NOUN.FIRST_A_LONG,
        True,
        False
    ],
    [ # 1st declension noun in -h; follwed by "poet. fem."
      # specific example is a)dialhyi/a
        "^[^\s]*h, poet\. fem\.",
        utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H,
        True,
        False
    ],
    [ # 2nd declension noun in -os
        "^[^\s]*o/?s[,\s]",
        utils.ENDING_TYPES.NOUN.SECOND_OS,
        True,
        False
    ],
    [ # 2nd declension noun in -hs
        "^[^\s]*h[/=]?s[,\s]",
        utils.ENDING_TYPES.NOUN.SECOND_HS,
        True,
        False
    ],
    [ # 2nd declension noun in -as, -ao
        "^[^\s]*a/?s( \[[^\]]*\])?, (ao, o\(|gen. ao)",
        utils.ENDING_TYPES.NOUN.SECOND_AS,
        True,
        False
    ],
    [ # 2nd declension noun in -as, -a
        "^[^\s]*a[/=]?s( \[[^\]]*\])?, (a[\s]*$|a=?, o\()",
        utils.ENDING_TYPES.NOUN.SECOND_AS,
        True,
        False
    ],
    [ # 3rd declension iota stem ending in polis
        "^[^\s]*po/?lis[,\s]",
        utils.ENDING_TYPES.NOUN.THIRD_IOTA,
        True,
        False
    ],
    [ # 3rd declension iota stem ending in -i/s
        "^[^\s]*i/s, h\(?,",
        utils.ENDING_TYPES.NOUN.THIRD_IS_FEM,
        True,
        False
    ],
    [ # 3rd declension consonant stem with no genitive
        "^[^\s]*([\s]*\[[^\]]*\])?,[\s]+o\(",
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        True,
        False
    ],
    [ # 3rd declension consonant stem is, idos
        "^[^\s]*i/s, i/dos",
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        True,
        False
    ],
    [ # 3rd declension consonant stem au)toe/n
        "^[^\s]*e/n, to/,",
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        True,
        False
    ],
    [ # 3rd declension consonant stem autohdu/
        "^[^\s]*u/, to/,",
        utils.ENDING_TYPES.NOUN.THIRD_HDU_TYPE,
        True,
        False
    ],
    [ # 3rd declension -ψ -πος; (for μονωψ (mon-w/y), which is a mess)
        "^[^\s]*w/y, w=pos",
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        True,
        False
    ],
    [ # another check for second declension ending in -h, where
      # there is a bunch of junk between the ending and the gender
        "^[^\s]*h[/=]?( \[[^\]]*\])?[,\s].*h\(:&#8212;$",
        utils.ENDING_TYPES.NOUN.FIRST_H,
        True,
        False
    ],
    [ # another check for second declension ending in -a, where
      # there is a bunch of junk between the ending and the gender
        "^[^\s]*a[/=]?( \[[^\]]*\])?,.*(h\(:&#8212;|:&#8212;h\(, )$",
        utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
        True,
        False
    ],
    [ # another check for iota stems, where
      # there is a bunch of junk between the ending and the gender
        "^[^\s]*i[/=]?s( \[[^\]]*\])?,.*ews, h\(:&#8212;[\s]*$",
        utils.ENDING_TYPES.NOUN.THIRD_IOTA,
        True,
        False
    ],
    [ # just grabs omma, but worth (TODO look at combining with soma above; would just need to add last thing)
        "^[^\s]*a( \[[^\]]*\])?,.*to/ :&#8212;$",
        utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
        True,
        False
    ],
    [ # basically just dru^opteri/s
        "^[^\s]*i/s, e/ws, o\(,",
        utils.ENDING_TYPES.NOUN.THIRD_IOTA,
        True,
        False
    ],
    [ # polus
        "^[^\s]*polu/?s,",
        utils.ENDING_TYPES.ADJECTIVE.POLUS,
        True,
        False
    ],
    [ # infinitives
        "^[^\s]*ei(=)?n|^[^\s]*h=nai, (inf|part)\.",
        utils.ENDING_TYPES.VERB.INFINITIVE,
        True,
        False
    ],
    [ # conjunctions
        "^[^\s]*( \[[^\]]*\])?( \(.*?\)(?=,))?( or [^\s]+( [^\s]+)?)?,(( Ep.)?( ([^\s]+) \([^\)]*\))+:)?( (Ep\.|causal|relat\.|used as a Final and Temporal))? Conj\.",
        utils.ENDING_TYPES.CONJUNCTION,
        True,
        False
    ],
    [ # a)ta/r also a conjunction, but has a mess of stuff that makes it easier to just check
        "^a\)ta/r",
        utils.ENDING_TYPES.CONJUNCTION,
        True,
        False
    ],
    [ # prepositions
        "(Prep. ((usually )?with|governing|c\.) )|(PREP. WITH )(gen|dat|acc|GEN(IT)?|DAT|ACC)\.",
        utils.ENDING_TYPES.PREPOSITION,
        False,
        False
    ],
    [ # adverb
        "^[^\s]*( \[[^\]]*\])?(,| and [^\s]* \(v\. sub fin\.\):)[\s]+Adv([\s]*\.|[\s]+)",
        utils.ENDING_TYPES.ADVERB,
        False,
        False
    ]
]

# a list of special exceptions
specialWords = {
    "au)sautou=": utils.ENDING_TYPES.ADJECTIVE.AUTOU_COMPOUNDS,
    "bou=s": utils.ENDING_TYPES.NOUN.BOUS,
    "ge/gwna": utils.ENDING_TYPES.VERB.GEGWNA,
    "a)/stu": utils.ENDING_TYPES.NOUN.ASTU,
    "ge/ra^s": utils.ENDING_TYPES.NOUN.GERAS,
    "gh=ras": utils.ENDING_TYPES.NOUN.GHRAS,
    "do/ru": utils.ENDING_TYPES.NOUN.DORU,
    "dru=s": utils.ENDING_TYPES.NOUN.DRUS,
    "e(autou=": utils.ENDING_TYPES.ADJECTIVE.AUTOU_COMPOUNDS,
    "e)gw/": utils.ENDING_TYPES.PRONOUN.EGW,
    "ei(=s": utils.ENDING_TYPES.ADJECTIVE.EIS,
    "e)/oika": utils.ENDING_TYPES.VERB.EOIKA,
    "h(merokalle/s": utils.ENDING_TYPES.NOUN.HMEROKALLES,
    "i)qu/s": utils.ENDING_TYPES.NOUN.IQUS,
    "i)/s": utils.ENDING_TYPES.NOUN.IS,
    "kre/as": utils.ENDING_TYPES.NOUN.KREAS,
    "kw=as": utils.ENDING_TYPES.NOUN.KWAS,
    "la^gw/s": utils.ENDING_TYPES.NOUN.LAGWS,
    "da/kru": utils.ENDING_TYPES.NOUN.DAKRU,
    "mhdei/s": utils.ENDING_TYPES.ADJECTIVE.EIS,
    "me/ga^s": utils.ENDING_TYPES.ADJECTIVE.MEGAS,
    "min": utils.ENDING_TYPES.PRONOUN.MIN,
    "nau=s": utils.ENDING_TYPES.NOUN.NAUS,
    "o(": utils.ENDING_TYPES.ADJECTIVE.O,
    "o(/de": utils.ENDING_TYPES.ADJECTIVE.ODE,
    "o(/s": utils.ENDING_TYPES.ADJECTIVE.OS,
    "o(/sper": utils.ENDING_TYPES.ADJECTIVE.OS,
    "o(/ste": utils.ENDING_TYPES.ADJECTIVE.OS,
    "ou)dei/s": utils.ENDING_TYPES.ADJECTIVE.EIS,
    "ou)qei/s": utils.ENDING_TYPES.ADJECTIVE.EIS,
    "ou)/tis": utils.ENDING_TYPES.ADJECTIVE.TIS,
    "pa/mmega^s": utils.ENDING_TYPES.ADJECTIVE.MEGAS,
    "pe/leku^s": utils.ENDING_TYPES.NOUN.PELAKUS,
    "e(ca^pe/leku^s": utils.ENDING_TYPES.NOUN.PELAKUS,
    "plei/wn": utils.ENDING_TYPES.ADJECTIVE.PLEIWN,
    "polu/s": utils.ENDING_TYPES.ADJECTIVE.POLUS,
    "*pu_qw/": utils.ENDING_TYPES.NOUN.PUQW,
    "seautou=": utils.ENDING_TYPES.ADJECTIVE.AUTOU_COMPOUNDS,
    "sfei=s": utils.ENDING_TYPES.PRONOUN.SFEIS,
    "tis": utils.ENDING_TYPES.ADJECTIVE.TIS,
    "toio/sde": utils.ENDING_TYPES.ADJECTIVE.OSDE_A,
    "toso/sde": utils.ENDING_TYPES.ADJECTIVE.OSDE_H,
    "thli^ko/sde": utils.ENDING_TYPES.ADJECTIVE.OSDE_H,
    "u(pe/rmegas": utils.ENDING_TYPES.ADJECTIVE.MEGAS,
    "fhmi/": utils.ENDING_TYPES.VERB.FHMI,
    "xei/r": utils.ENDING_TYPES.NOUN.XEIR,
    "xrew/": utils.ENDING_TYPES.NOUN.XREW,
    "xrew/n": utils.ENDING_TYPES.NOUN.XREWN,
    "xi_lio/naus": utils.ENDING_TYPES.NOUN.NAUS,

    #======

    "e)piqeia/zw)": utils.ENDING_TYPES.VERB.THEMATIC,
    "h(me/ra": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "h)re/mhsis": utils.ENDING_TYPES.NOUN.THIRD_IOTA,
    "*)inw/": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "qa/lassa": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "kate/pefnon": utils.ENDING_TYPES.VERB.THEMATIC,
    "katwfa^ga=s": utils.ENDING_TYPES.NOUN.SECOND_AS,
    "ke/ra^s": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "kero/eis": utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA,
    "kordu/lh": utils.ENDING_TYPES.NOUN.FIRST_H,
    "kourew=tis": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "kra/s": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "li^gu/s": utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US,
    "li^mh/n": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "metame/lei": utils.ENDING_TYPES.VERB.THEMATIC,
    "o)/noma": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "ou)si/a": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "o)/y": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "patra^loi/as": utils.ENDING_TYPES.NOUN.SECOND_AS,
    "pru/mna^": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "pru^ta^nei=on": utils.ENDING_TYPES.NOUN.SECOND_ON,
    "pru?/ta^nis": utils.ENDING_TYPES.NOUN.THIRD_IOTA,
    "pterofo/ra_s": utils.ENDING_TYPES.NOUN.SECOND_AS,
    "ptu/c": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "pu_go/riza": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "ske/pas": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "smu/rna": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "*sti/c": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "suggnw/mh": utils.ENDING_TYPES.NOUN.FIRST_H,
    "sumplei/ones": utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION,
    "ta?/mi^as": utils.ENDING_TYPES.NOUN.SECOND_AS,
    "te/ras": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "te/tmon": utils.ENDING_TYPES.VERB.THEMATIC,
    "ti/gri^s": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "tri^a_ko/st[ia]": utils.ENDING_TYPES.NOUN.SECOND_ON,
    "tri^hmi/s[eon]": utils.ENDING_TYPES.NOUN.SECOND_ON,
    "fa/rugc": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "frou/rion": utils.ENDING_TYPES.NOUN.SECOND_ON,
    "fu^ta^lia/": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "xa^ra/": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "xa^ri/eis": utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA,
    "xelu/nna": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "xe/rniy": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "xlwrome/la_s": utils.ENDING_TYPES.ADJECTIVE.MIXED_AS_AINA,
    "xno/h": utils.ENDING_TYPES.NOUN.FIRST_H,
    "xroia/": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "w)nh/": utils.ENDING_TYPES.NOUN.FIRST_H,
    "de/llis": utils.ENDING_TYPES.NOUN.THIRD_IOTA,
    "a)rh/n": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "glw/c": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "gru_pa^lw/phc": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "dei/s": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "de/mas": utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    "bra^xu/s": utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US,
    "pa^xu/s": utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US,
    "glu^ku/s": utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US,
    "gastroknh/mh": utils.ENDING_TYPES.NOUN.FIRST_H,
    "bu_nok[opi/a]": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "gene/teira": utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    "w)ku/s": utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US,
    "qh=lus": utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US,
    "h(du/s": utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US,

}

# precompiling for those regexes
for p in possibleClassifications:
    patternString = p[0][0] + patternStrings[p[1]] + p[0][1]
    pattern = re.compile(patternString)
    p.append(pattern)

for p in secondRoundClassifications:
    patternString = p[0]
    pattern = re.compile(patternString)
    p.append(pattern)

# create the dictionary for the various classifications
def makeClassDict():
    classDict = {}

    myList = [
    utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION,
    utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_A_CONTRACT,
    utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_O_CONTRACT,
    utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A,
    utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H,
    utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A_E_CONTRACT,
    utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H_E_CONTRACT,
    utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_HS,
    utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_WN,
    utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US,
    utils.ENDING_TYPES.ADJECTIVE.POUS_FOOT,
    utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA,
    utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA_O_CONTRACT,
    utils.ENDING_TYPES.ADJECTIVE.MIXED_AS_AINA,
    utils.ENDING_TYPES.ADJECTIVE.MIXED_WS_UIA_OS,
    utils.ENDING_TYPES.ADJECTIVE.IS_I,
    utils.ENDING_TYPES.ADJECTIVE.PAS,
    utils.ENDING_TYPES.ADJECTIVE.AUTOU_COMPOUNDS,
    utils.ENDING_TYPES.ADJECTIVE.OSDE_H,
    utils.ENDING_TYPES.ADJECTIVE.OSDE_A,
    utils.ENDING_TYPES.ADJECTIVE.EIS,
    utils.ENDING_TYPES.ADJECTIVE.TIS,
    utils.ENDING_TYPES.ADJECTIVE.MEGAS,
    utils.ENDING_TYPES.ADJECTIVE.POLUS,
    utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN,
    utils.ENDING_TYPES.NOUN.FIRST_A_LONG,
    utils.ENDING_TYPES.NOUN.FIRST_A_SHORT,
    utils.ENDING_TYPES.NOUN.FIRST_H,
    utils.ENDING_TYPES.NOUN.SECOND_OS,
    utils.ENDING_TYPES.NOUN.SECOND_HS,
    utils.ENDING_TYPES.NOUN.SECOND_AS,
    utils.ENDING_TYPES.NOUN.SECOND_ON,
    utils.ENDING_TYPES.NOUN.THIRD_CONSONANT,
    utils.ENDING_TYPES.NOUN.THIRD_EPSILON,
    utils.ENDING_TYPES.NOUN.THIRD_IOTA,
    utils.ENDING_TYPES.NOUN.THIRD_SIGMA_MF,
    utils.ENDING_TYPES.NOUN.THIRD_SIGMA_N,
    utils.ENDING_TYPES.NOUN.THIRD_DIGAMMA,
    utils.ENDING_TYPES.NOUN.THIRD_IS_FEM,
    utils.ENDING_TYPES.NOUN.THIRD_OUS,
    utils.ENDING_TYPES.NOUN.THIRD_ES_OUS_TO,
    utils.ENDING_TYPES.NOUN.THIRD_I_TO,
    utils.ENDING_TYPES.NOUN.THIRD_I_TO,
    utils.ENDING_TYPES.NOUN.THIRD_HDU_TYPE,
    utils.ENDING_TYPES.VERB.THEMATIC,
    utils.ENDING_TYPES.VERB.A_CONTRACT,
    utils.ENDING_TYPES.VERB.E_CONTRACT,
    utils.ENDING_TYPES.VERB.O_CONTRACT,
    utils.ENDING_TYPES.VERB.DEPONENT,
    utils.ENDING_TYPES.VERB.A_CONTRACT_DEPONENT,
    utils.ENDING_TYPES.VERB.E_CONTRACT_DEPONENT,
    utils.ENDING_TYPES.VERB.O_CONTRACT_DEPONENT,
    utils.ENDING_TYPES.VERB.UMI,
    utils.ENDING_TYPES.VERB.ATHEMATIC,
    utils.ENDING_TYPES.VERB.INFINITIVE,
    utils.ENDING_TYPES.VERBAL_ADJECTIVE,
    utils.ENDING_TYPES.PARTICIPLE.WN
    ]

    for l in myList:
        classDict[l] = {}

    classDict["rest"] = {}

    return classDict

# given a classification, get a key for an appropriate dictionary
# (basically lumps all the little ones together in "rest")
def getClassDictKey(classif):
    if ((classif == utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION) or (classif == utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_A_CONTRACT) or (classif == utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_O_CONTRACT) or (classif == utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A) or (classif == utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H) or (classif == utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A_E_CONTRACT) or (classif == utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H_E_CONTRACT) or (classif == utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_HS) or (classif == utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_WN) or (classif == utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US) or (classif == utils.ENDING_TYPES.ADJECTIVE.POUS_FOOT) or (classif == utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA) or (classif == utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA_O_CONTRACT) or (classif == utils.ENDING_TYPES.ADJECTIVE.MIXED_AS_AINA) or (classif == utils.ENDING_TYPES.ADJECTIVE.MIXED_WS_UIA_OS) or (classif == utils.ENDING_TYPES.ADJECTIVE.IS_I) or (classif == utils.ENDING_TYPES.ADJECTIVE.PAS) or (classif == utils.ENDING_TYPES.ADJECTIVE.AUTOU_COMPOUNDS) or (classif == utils.ENDING_TYPES.ADJECTIVE.OSDE_H) or (classif == utils.ENDING_TYPES.ADJECTIVE.OSDE_A) or (classif == utils.ENDING_TYPES.ADJECTIVE.EIS) or (classif == utils.ENDING_TYPES.ADJECTIVE.TIS) or (classif == utils.ENDING_TYPES.ADJECTIVE.MEGAS) or (classif == utils.ENDING_TYPES.ADJECTIVE.POLUS) or (classif == utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN) or (classif == utils.ENDING_TYPES.NOUN.FIRST_A_LONG) or (classif == utils.ENDING_TYPES.NOUN.FIRST_A_SHORT) or (classif == utils.ENDING_TYPES.NOUN.FIRST_H) or (classif == utils.ENDING_TYPES.NOUN.SECOND_OS) or (classif == utils.ENDING_TYPES.NOUN.SECOND_HS) or (classif == utils.ENDING_TYPES.NOUN.SECOND_AS) or (classif == utils.ENDING_TYPES.NOUN.SECOND_ON) or (classif == utils.ENDING_TYPES.NOUN.THIRD_CONSONANT) or (classif == utils.ENDING_TYPES.NOUN.THIRD_EPSILON) or (classif == utils.ENDING_TYPES.NOUN.THIRD_IOTA) or (classif == utils.ENDING_TYPES.NOUN.THIRD_SIGMA_MF) or (classif == utils.ENDING_TYPES.NOUN.THIRD_SIGMA_N) or (classif == utils.ENDING_TYPES.NOUN.THIRD_DIGAMMA) or (classif == utils.ENDING_TYPES.NOUN.THIRD_IS_FEM) or (classif == utils.ENDING_TYPES.NOUN.THIRD_OUS) or (classif == utils.ENDING_TYPES.NOUN.THIRD_ES_OUS_TO) or (classif == utils.ENDING_TYPES.NOUN.THIRD_I_TO) or (classif == utils.ENDING_TYPES.NOUN.THIRD_I_TO) or (classif == utils.ENDING_TYPES.NOUN.THIRD_HDU_TYPE) or (classif == utils.ENDING_TYPES.VERB.THEMATIC) or (classif == utils.ENDING_TYPES.VERB.A_CONTRACT) or (classif == utils.ENDING_TYPES.VERB.E_CONTRACT) or (classif == utils.ENDING_TYPES.VERB.O_CONTRACT) or (classif == utils.ENDING_TYPES.VERB.DEPONENT) or (classif == utils.ENDING_TYPES.VERB.A_CONTRACT_DEPONENT) or (classif == utils.ENDING_TYPES.VERB.E_CONTRACT_DEPONENT) or (classif == utils.ENDING_TYPES.VERB.O_CONTRACT_DEPONENT) or (classif == utils.ENDING_TYPES.VERB.UMI) or (classif == utils.ENDING_TYPES.VERB.ATHEMATIC) or (classif == utils.ENDING_TYPES.VERB.INFINITIVE) or (classif == utils.ENDING_TYPES.VERBAL_ADJECTIVE) or (classif == utils.ENDING_TYPES.PARTICIPLE.WN)):
        return classif
    else:
        return "rest"


# process raw XML into a full dictionary (step 1)
def processDict1(dictName):
    inName = utils.getRawDictionaryFn(dictName)
    entries = utils.getContent(inName, True)

    output = {"name": dictName}
    outputDict = {}

    classDict = makeClassDict()

    if False:
        for entry in range(5):
            key = "key" + str(entry)
            ls = ["a", "a", "b", "b", "b"]
            val = {"key": key, "betacode": "afa", "letter": ls[entry], "pos": "noun", "division": "a[l]fa[s]", "text": "Some text"}
            outputDict[key] = val

    i = 0
    maxIterations = 1
    useMax = False#True#
    printInterval = 5000
    printAtIntervals = True
    totalLen = len(entries)

    # for each entry,
    for entryXML in entries:
        if useMax:
            if (i >= maxIterations):
                break
        i += 1
        #print entry

        # get properly formatted string
        (xml, parsed) = getStringSafe(entryXML)

        # print an update if necessary
        if (printAtIntervals and (i % printInterval == 0)):
            print str(i) + "/" + str(totalLen) + " (" + str(round((100.0*i)/totalLen, 1)) + "%)"
        if not(parsed):
            continue

        #if this is lsj, extract the first round of information
        if (dictName == utils.DICTIONARY_NAMES.LSJ):
            div = xml.find("text").find("body").find("div0")
            entry = div.find("entryFree")

            core = getCoreText(entry)

            #core = ""

            # grab the start, core, and then make adjustments
            start = getStartText(core)
            core, start, cont = coreStartExceptions(core, start)
            top = getTopText(core)
            topPlus20 = getTopPlus20(core, top)

            if cont:
                continue;

            if False:
                print core
                print "-----"
                print top
                print "-----"
                print topPlus20
                print "============================================"

                continue

            # run individual tests
            if False:
                preppedTop = re.sub(r'^([^\s]*) \([A-Z]\)', r'\1', re.sub(r'\$\$', r'', top))

                #print re.sub(r'\$\$', r'', core)
                standard = "[\s]*(\[[^\]]*\])?(,?[\s]+(or|Ion\.|Att\.|Dor\.|Ep\.|Aeol\.)[\s]*[^\s]*([\s]*\[[^\]]*\])?(, hs)?([\s]*[A-Z][a-z]*\.[\d]+(.[\d]+)?)?([\s]*\(.*?\)(?=[,\s]))?)*([\s]+\(.*?\)(?=[,\s]))?([,\s]*\[[^\]]*\])?"
                #standard = "[\s]*(\(.*?\))"
                #"a/?\^?","([\s]*,[\s]*w=?n)?[\s]*,[\s]*ta/"
                #mr = "h/?\^?" + standard + "h("
                mr = "^(([^\s]*, )+(etc\., )?((Ep\.|Aeol\.|Dor\.|Ion\.)( for)? [^\s]*, )?(v\.|=))+" # (sub )?([^\s]*, )*[^\s]*( ([1Il]+))?(, Hsch)?\.[\s]*
                #mr = "ai/?" + standard + "([\s]*,[\s]*w=n)?[\s]*,[\s]*ai\("#+ "([\s]*,[\s]*contr\. [^\s]*)?[\s]*,[\s]*(o\(|h\(|to/|fem\.)"
                #mr = "^[^\s]*,[\s]*(( and )?(Ep\.|Dor\.|Aeol\.|poet\.|Ion\.))+[\s]+([1-3])(sg|pl)\.[\s]+(aor)\.([\s]+[1-2])?[\s]+(Pass)\.[\s]+of[\s]+[^\s]*\.$"#
                repl = re.sub(r'\$\$', r'', core)
                m = re.search(re.compile(mr), repl)#preppedTop)#
    #r"h/?\^?[\s]*(\[[^\]]*\])?(,?[\s]+(or|Ion\.|Att\.|Dor\.)[\s]+[^\s]*)?[\s]*,[\s]*(a=?s|o\(|h\(?)"
                print not(m == None)
                print repl[m.start():m.end(0)]
                print "--"
    #^((i\.e\. )?[\s]*, )+(for|Ep\. forms from|Dor\. for) ([\s]*( q\.v\.)?, )+[^\s]\.[\s]*$


            # linking info we skip for now
            if False:
                # for unspecified words that just reference a synonym,
                # we skip for now

                linkMatch0 = re.search(r"^[^\s]*( \(.*?\))?:", core)

                if (not(linkMatch0) == None):
                    continue

                # for words that are just variants that point to the common variant
                # we skip for now
                linkMatch1 = re.search(r"^(((i\.e\. )?[^\s]*(, contr\. [^,\s]*)?, )+(for|Ep\. forms from|(Dor\.|Aeol\.|Lacon\.|Ep\.|Ion\.|Att\.|Boeot\.)( word)? for) ((and )?[^\s]*( \(q\. v\.\))?([\s]*\(prob\. Lacon\.\))?, )*[^\s]*( \(q\. v\.\))?(, esp\. in sense of .*$|\.[\s]*))(((i\.e\. )?[^\s]*, )+(for|Ep\. forms from|(Dor\.|Aeol\.|Lacon\.|Ep\.|Ion\.)( word)? for) ((and )?[^,;]*( \(q\. v\.\))?([\s]*\(prob\. Lacon\.\))?, )*[^\s]*( \(q\. v\.\))?\.[\s]*)*(; cf [^\s]*\.)?$", core)
                linkMatch2 = re.search(r"^((i\.e\. )?[^\s]*( \([A-Z]\))?, )+(=) ([^\s]*( \(q\. v\.\))?(, )?)", re.sub(r'\$\$', r'', core))
                # mnasth/r, v. mnhst-
                linkMatch3 = re.search(r"^(([^\s]*( \((gen)\. (pl)\.\))?( \[[^\]]*\])?, )+(etc\., )?((Ep\.|Aeol\.|Dor\.|Ion\.|Att\.|Boeot\.|contr\.)( for)? [^\s]*, )?((v\.|=) (sub )?([^\s]*, )*[^\s]*( ([1Il]+))?(, Hsch| [A-Z]\. \d+\.\d+| sub init| &#65288;[^&\s]*&#65289;)?\.[\s]*)+)+$", re.sub(r'\$\$', r'', core))
                #()
                # mu^o-galh=, $$v.l. for mugalh= in Dsc.2.68. (([A-Z][a-z]*|[\d]+)\.){2-3}[\d]+
                linkMatch3_1 = re.search(r"^[^\s]*( \((dat|acc|gen)\. (sg|pl)\.\))?, ((freq\. |prob\. )?f\.l\.|v\.l\.|written) for [^\s]*( [^\s]*\.?)?(, aor\. inf\. of [^,\.\s]+)?([A-Z]\.[A-Z0-9]+)?( or [^\s]*)?( \(v\. [^\s]+( [A-Z])?\))?,?((((( [A-Z][a-z]*)? [A-Z][a-z]*\.)? (in|ap\.))? (([A-Z]+[a-z]*[\d]*|[\d]+[a-z]?)\.?){1,4}([a-zA-Z0-9]*: in Gloss\. expld\. by murex|; c\.?f\. [^\s]+( \([A-Z]\))?| [A-Z]|\. s\.v\. [^,\.\s]+|,[\s]+=[\s]+(([A-Z]+[a-z]*[\d]*|[\d]+[a-z]?)\.?){1,4})?)| q\.[\s]*v|( \(q\.[\s]*v\.\)(, (Erot|which is to be preferred))?)|( [A-Z][a-z]*\., [A-Z][a-z]*\. [^,\.\s]+, v\. [^,\.\s]+))?\.$", re.sub(r'\$\$', r'', core))
                #()
                # bleg, poet. and Dor. for bleg, stuff citations stuff
                linkMatch4 = re.search(r"^[^\s]*( \([A-Z]\))?(, [^\s]*)?( \[[a-z\^_]*\])?(, i\.[\s]*e\. [^\s]*)?( or [^,\s]+)?,[\s]*((( (and )?(Ep\.|Dor\.( \(Lacon\.\))?|Aeol[,\.]|poet\.|Ion\.|Att\.|Boeot\.|contr\.|corrupt)(,)?)+[\s]*for|gloss on)[\s]+[^\s]*( \(q\.[\s]*v\.\))?([,:] |\.))", re.sub(r'\$\$', r'', core))
                #()
                # ai)/ke [e^], ai)/ken, poet. and Dor. for e)a/n
                linkMatch4_1 = re.search(r"^([^\s]*([\s]+\[[^\]]*\])?,[\s]*)+( (and )?(Ep\.|Dor\.|Aeol\.|poet\.|Ion\.|Att\.|Boeot\.))+ for [^\s]*\.", re.sub(r'\$\$', r'', core))
                linkMatch5 = re.search(r"^[^\s]*, (part\. of|late form for) [^\s]*[\.,]", re.sub(r'\$\$', r'', core))
                linkMatch6 = re.search(r"^[^\s]*, ((Ep\.|Aeol\.|Dor\.|Ion\.) dat\.|pf\.) of [^\s]*(, [A-Z][a-z]*\.\d+\.\d+)?\.", re.sub(r'\$\$', r'', core))
                # a, v. b. c, v. d.      and so on
                linkMatch7 = re.search(r"^([^\s]*, v\.[\s]+[^\s]*( \([A-Z]\))?\.[\s]*)+$", re.sub(r'\$\$', r'', core))
                # verb forms, e.g. a)/gerqen, Dor. and Ep. 3pl. aor. 1 Pass. of a)gei/rw.
                linkMatch8 = re.search(r"^([^\s]*([\s]+\[[^\]]*\])?,[\s]*)+( es, e,)?(for [^,\.\s]+, )?([\s]*(but [^,\s]*,[\s]*)?( inf\. of the)?([\s]*( and )?(Ep\.|Dor\.|Aeol\.|poet\.|Ion\.|Att\.|Boeot\.))*([\s]+([1-3])(sg|pl)\.)?([\s]*(opt)\.)?([\s]*(aor|fut|impf|pf|plpf)\.([\s]+[1-2])?)?([\s]+(inf|imper)\.)?([\s]+iterative)?([\s]+(Act|Pass|Med)\.)?[\s]+(of|for)[\s]+[^\s]*([\s]+(\(q\.[\s]*v\.\)|q\.[\s]*v|v\.[\s]+[^,\.\s]*|)|, ([A-Z][a-z]*\.?)+\d+ (\(v\.l\. [^,\.\s]+\))?)?[\.:,])+$", re.sub(r'\$\$', r'', core))
                # ()
                # noun forms, e.g. na=as, Dor. acc. pl. of nau=s (q.v.).
                linkMatch9 = re.search(r"^[^\s]*,([\s]*(but [^,\s]*,[\s]*)?([\s]*( and )?(Ep\.|Dor\.|Aeol\.|poet\.|Ion\.|Att\.|Boeot\.))*([\s]+(acc|dat|gen)\.)?([\s]+(neut)\.)?([\s]+(sg|pl)\.)?[\s]+(of|from)[\s]+[^\s]*( \(q\.[\s]*v\.\)| q\.[\s]*v)?([\s]*v\. [^,\.\s]*)?[\.:])+$", re.sub(r'\$\$', r'', core))
                # ()
                # a, b, c, poet. forms, v. d.
                linkMatch10 = re.search(r"^([^\s]+, )+(poet)\. forms, v\. [^\s]+\.$", re.sub(r'\$\$', r'', core))

                # a, acc. sg., dual b, pl. c; v. d.
                linkMatch11 = re.search(r"^[^\s]+, acc\. sg\., dual [^\s]+, pl\. [^\s]+; v\. [^\s]+\.$", re.sub(r'\$\$', r'', core))

                #print re.sub(r'\$\$', r'', core)[linkMatch8.start():linkMatch8.end()]

                # ()
                # need that comment to keep the syntax highlighting correct in atom, some silly glitch


                if (not(linkMatch1 == None) or not(linkMatch2 == None) or not(linkMatch3 == None) or not(linkMatch3_1 == None) or not(linkMatch4 == None) or not(linkMatch4_1 == None) or not(linkMatch5 == None) or not(linkMatch6 == None) or not(linkMatch7 == None) or not(linkMatch8 == None) or not(linkMatch9 == None) or not(linkMatch10 == None) or not(linkMatch11 == None)):
                    continue

            # look for link matches, and if it has them, skip
            # this is basically entries that say "bla is a form of bleh"
            hadLinkMatch = False
            for j in range(len(linkMatches)):
                lm = linkMatches[j]
                if lm[1]:
                    check = re.sub(r'\$\$', r'', core)
                else:
                    check = core
                match = re.search(lm[0], check)
                if (not(match == None)):
                    hadLinkMatch = True

            if hadLinkMatch:
                continue


            # determine the ending types for the word
            matches = []
            someMatch = False

            preppedTop = re.sub(r'^([^\s]*) \([A-Z]\)', r'\1', re.sub(r'\$\$', r'', top))

            if (start in specialWords):
                classification = specialWords[start]
            else:
                # check each of the possible classifications
                for p in possibleClassifications:
                    pattern = p[-1]
                    match = re.search(pattern, preppedTop)
                    if (not(match == None)):
                        someMatch = True
                        index = match.end(0)
                        key = p[2]
                        matches.append((index, key))
                        if (p[3]):
                            print start
                            print core
                            print "-------------------------------------"

                if someMatch:
                    # grab the classification from the first item in sorted order
                    # that is, the first match that appears.
                    classification = sorted(matches, key=lambda x: x[0])[0][1]
                else:
                    # try second round of simple checks for p in secondRoundClassifications:
                    for p in secondRoundClassifications:
                        pattern = p[-1]
                        if p[2]:
                            matchAgainst = preppedTop
                        else:
                            matchAgainst = core
                        match = re.search(pattern, matchAgainst)
                        if (not(match == None)):
                            someMatch = True
                            index = match.end(0)
                            key = p[1]
                            matches.append((index, key))
                            if (p[3]):
                                print start
                                print core
                                print "-------------------------------------"

                    # check for matches again
                    if someMatch:
                        # grab the classification from the first item in sorted order
                        # that is, the first match that appears.
                        classification = sorted(matches, key=lambda x: x[0])[0][1]
                    else:
                        classification = utils.ENDING_TYPES.OTHER

                        if False:
                            print start
                            print "-----"
                            print top
                            print "-----"
                            print preppedTop
                            print "-----"
                            print core
                            print "============================================"


            #print classification
            if (False):
                print topPlus20
                print "-----"
                print classification
                print "============================================"

            #print classification

            ###
            key = entry.attrib["key"]
            val = {
            "start": start,
            "core": core,
            "classification": classification,
            "entryXML": entryXML
            }
            properDict = classDict[getClassDictKey(classification)]
            properDict[key] = val
            #outputDict[key] = val

            continue


            key = entry.attrib["key"]
            sortKey = entry.attrib["id"]
            betacode = entry.attrib["key"]
            letter = div.attrib["n"]
            pos = "???"
            division =  generateDivision(start)
            senses = parseSenses(entry.findall("sense"))
            endingType = ""
            stem = {}
            stemDivision = {}
            irregular = False


        # TODO
        if (dictName == utils.DICTIONARY_NAMES.Slater):
            div1 = xml.find("text").find("body").find("div1")
            entry = div1.find("entryFree")

            key = entry.attrib["key"]
            sortKey = entry.attrib["id"]
            betacode = entry.attrib["key"]
            letter = div1.attrib["n"]
            pos = "???"
            division = generateDivision(entry.find("orth").text)
            senses = parseSenses(entry.findall("sense"))
            endingType = ""
            stem = {}
            stemDivision = {}
            irregular = False

        val = {
        "letter": letter,
        "division": division,
        "senses": senses,
        "key": key,
        "betacode": betacode,
        "sortKey": sortKey,
        "pos": pos,
        "endingType": endingType,
        "stem": stem,
        "stemDivision": stemDivision,
        "irregular": irregular
        }
        outputDict[key] = val

    output["dict"] = classDict;

    # save the intermediate dictionary
    outFileName = utils.getProcessedDictionaryFn(dictName+"_intermediate_1")
    utils.safeWrite(outFileName, json.dumps(output))





#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# part 2


# remove all non-betacode and accents
def betaCodeOnlyNoAccent(s):
    return re.sub(r'[^A-Za-z)(+|&\'\s*]', "", s)


# regexes for finding stem lengths
doubleWordRegex = re.compile("^[^\s]+ or ([^\s]+),")
lengthSpecificationAtStartRegex = re.compile("^[^\s]+[\s]*\[(?:prob\. )?([^\]]*)\],")
lengthSplitRegex = re.compile("([\^_])")
replaceCommaInLensRegex = re.compile("[\s]*,[\s]*")
lRegex = re.compile("[1hw]")
sRegex = re.compile("[eo]")
qRegex = re.compile("[aiu]")
dipthongReplaceRegex = re.compile("(a|e|o|u)i(?![=/]*\+)|(a|o|e|h|w)u(?![=/]*\+)")
lensOnlyRegex = re.compile("^[\^_]+$")

# get a series of lengths for the stem
def getStemLengths(myStem, core, classification, num):
    result = []
    # replace dipthongs with a 1; they are always long
    s = re.sub(dipthongReplaceRegex, r'1', myStem)

    # if the stem ends in a list of vowel lengths, e.g.
    # panta/la_s [ta^]
    # insert them into the stem we examine
    # (yielding panta^/la_s)
    startLengthSpec = re.search(lengthSpecificationAtStartRegex, core)
    skipString = "@a)mhth/r@"
    if (not(startLengthSpec == None) and skipString.find("@"+s+"@") == -1):
        specs = core[startLengthSpec.start(1):startLengthSpec.end(1)]
        if (s == "likni/t"): # (misread as "vi_")
            specs = "ni_"
        elif (s == "sta/xus"): # either read as u_ or u^
            specs = "sta^"
        elif (s == "diama/lac"): # ma read as ua?
            specs = "ma^"
        elif (s == "u(/br"): # u^ by nature, u_ by position in Ep. etc.
            specs = "u^"
        elif (s == "1)/ma_ris"): # u^ by nature, u_ by position in Ep. etc.
            specs = ""
        elif (s == "mi_li^a/ri"): # says first i is both long and short; second i redundant
            specs = "a_"
        elif (s == "h(du^sw/ma^t" or s == "du^se/ya^n"): # redundant stuff
            specs = ""
        elif (s == "e)na^kisxi/li"): # says first i is both long and short; second i redundant
            specs = "xi_"
        elif (s == "*pu/qi^"): # some notes at end
            specs = "u_"
        elif (s == "fu^ta^li"): # some notes
            specs = ""
        elif (s == "katara/"): # different in attic and epic
            specs = ""
        elif (s == "f" or s == "*d" or s == "u(pokl" or s == "y"): # unecessary
            specs = ""
        elif (s == "diaqgi/b"): # li instead of gi? or was it di?
            specs = "gi_"
        elif (s == "i(dr"): # unecessary stuff
            specs = "i_"
        elif (s == "a)pamfie/nn"): # refers to ending
            specs = ""
        elif ((s == "a)ntepaf" or s == "a)ntaf") and specs == "fi^"): # refers to ending
            specs = ""
        elif ((s == "meta") and specs == "di^"): # refers to ending
            specs = ""
        elif ((s == "a)mfi" or s == "") and specs == "ti^"): # refers to ending
            specs = ""
        elif (specs[0:2] == "$$"): # refers to ending
            specs = specs[2:]
        elif (s == "e)n11ta"): # bad setup
            specs = ""
        elif (s == "meta" and specs == "a^, but a_ in S.Ph.184 (s. v. l., lyr.)"): # TODO make this ?
            specs = "a^"
        elif (s == "e)xis" and specs == "Nic. Th.223, -i_s metri gr. IG2.1660"):
            specs = "a"
        elif (s == "laqrh|" and specs == "a_^"): # uh, their way of writing ?
            specs = ""
        elif (s == "bra^xi/wn" and specs == "Ion. i^, Att. i_"): # TODO
            specs = ""
        elif (s == "*mi/nws" and specs == "i_, but also i^ Pl.Com.15 D."): # TODO
            specs = ""
        elif (s == "1)xmht" and specs == "a^"): # TODO; based on ending
            specs = ""
        elif (s == "prw=|r"): # TODO; based on ending
            specs = ""
        elif (s == "i)di^opa/q1"): # TODO; better handling for i^d type?
            specs = "i^, pa^"

        if not(lensOnlyRegex.search(specs) == None):
            res = []
            for char in specs:
                if (char == "^"):
                    res.append(utils.VOWEL_LEN.SHORT)
                else: # (char == "_"):
                    res.append(utils.VOWEL_LEN.LONG)
            return res
        if (specs[0:4] == "Att."):
            s = s
            # just skip out
        else:
            split = re.split(lengthSplitRegex, specs)
            i = 1
            newS = ""
            remainder = s
            while i < len(split):
                match = re.sub(replaceCommaInLensRegex, '', split[i-1])
                vowelLen = split[i]
                if (match == None):
                    print len(split)
                    break
                match = match.replace("*", "\*")
                mySplit = re.split(re.compile(match+"(?![_\^])"), remainder, maxsplit=1)
                newS += mySplit[0] + match + vowelLen
                if (len(mySplit) <= 1):
                    # sometimes get a marker that the final u in an -us, -eia, -u
                    # is short
                    if (classification == utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US and match == "u"):
                        break
                    else:
                        print "Bad Split: "
                        print match
                        print "Orig: " + s
                        print "Left: " + remainder
                        print "-----"
                        print core
                remainder = mySplit[1]
                i += 2
            newS += remainder
            if VERBOSE:
                print "~~~~~~~~~~~~~~~~~~~~~~~"
                print "Stem: " + myStem
                print "-----"
                print "Vowels: " + specs
                print "-----"
                print "New stem: " + newS
                print "-----"
                print "Core:"
                print core
                print "~~~~~~~~~~~~~~~~~~~~~~~"
            s = newS


    # TODO: replace with defaulter below?
    if (num == 0):
        myLen = len(s)
        for i in range(myLen):
            char = s[i]
            # dipthong or long by nature (omega, eta)
            if not(re.search(lRegex, char) == None):
                result.append(utils.VOWEL_LEN.LONG)
            # short by nature (omicron, epsilon)
            elif not(re.search(sRegex, char) == None):
                result.append(utils.VOWEL_LEN.SHORT)
            # unknown by nature alpha, iota, upsilon
            elif not(re.search(qRegex, char) == None):
                # if there are next characters
                if (i < myLen - 1):
                    nextChar = s[i+1]
                    if (nextChar == "_" or nextChar == "="):
                        result.append(utils.VOWEL_LEN.LONG)
                    elif (nextChar == "^"):
                        result.append(utils.VOWEL_LEN.SHORT)
                    else:
                        result.append(utils.VOWEL_LEN.UNKNOWN)
                else:
                    result.append(utils.VOWEL_LEN.UNKNOWN)

    #dusta/la^s vs dusta=la^s

        return result
    return None



#[A-Za-z)(/=\\+|&\']
#?[\s]*(\$\$)?[\s]*(\(.*?\))[\s]+
linkRegex = re.compile("^,?[\s]*(?:\$\$)?(?:(?:Ion)\. Noun,)?[\s]*\(([A-Za-z)(/=\\+|&\']*?)(?:, cf. .*?)?\)[\s]+")
# search the text for a "link" word that could supply missing lengths
def findLink(restOfCore):
    search = re.search(linkRegex, restOfCore)
    if not(search == None):
        return restOfCore[search.start(1):search.end(1)]
    else:
        return ""


# given start, core, and classification, get multiple possible starts,
# e.g. if we have "freattw/ or frea_tw/" for example
def getMultipleStarts(start, core, classification):
    dwr = re.search(doubleWordRegex, core)
    if not(dwr == None):
        if VERBOSE:
            print "~~~~~~~~~~~~~~~~~~"
            print "OR MATCH ON:"
            print core
            print "~~~~~~~~~~~~~~~~~~"

        start2 = core[dwr.start(1):dwr.end(1)]
        return [start, start2]

    else:
        return [start]


# define default functions for stem and length handling
def defaultStemFunc(s):
    return s
def defaultLensFunc(ls):
    return ls


# get stem and stem division information for an adjective
def doStemWorkAdj(starts, core, classification, stemSplitter, mNSF, nNSF, mSF, fSF, nSF, mNLF, nNLF, mLF, fLF, nLF):
    mNomStem = []
    nNomStem = []
    mStem = []
    fStem = []
    nStem = []
    mNomSD = []
    nNomSD = []
    mSD = []
    fSD = []
    nSD = []

    myStems = []

    for currStart in starts:
        myStem = re.split(stemSplitter, currStart)[0]

        myStems.append(myStem)

        simpleStem = betaCodeOnlyNoAccent(myStem)


        mNomStem.append(mNSF(simpleStem))
        nNomStem.append(nNSF(simpleStem))
        mStem.append(mSF(simpleStem))
        fStem.append(fSF(simpleStem))
        nStem.append(nSF(simpleStem))

        base = getStemLengths(myStem, core, classification, 0)
        mNomLens = mNLF(copy.deepcopy(base))
        nNomLens = nNLF(copy.deepcopy(base))
        mLens = mLF(copy.deepcopy(base))
        fLens = fLF(copy.deepcopy(base))
        nLens = nLF(copy.deepcopy(base))

        mNomSD.append(mNomLens)
        nNomSD.append(nNomLens)
        mSD.append(mLens)
        fSD.append(fLens)
        nSD.append(nLens)


    stem = {
    "mascNom": mNomStem,
    "neutNom": nNomStem,
    "masc": mStem,
    "fem": fStem,
    "neut": nStem
    }
    stemDivision = {
    "mascNom": mNomSD,
    "neutNom": nNomSD,
    "masc": mSD,
    "fem": fSD,
    "neut": nSD
    }

    return myStems, stem, stemDivision

# get stem and stem division information for a noun that doesn't have a
# complicated nomsg/stem difference; e.g. στρατεγος, ου has a simple,
# αιξ, αιγος does not
def doStemWorkNounSimple(starts, core, classification, stemSplitter, nsSF, rSF, nsLF, rLF):
    nomSgStem = []
    restStem = []
    nomSgSD = []
    restSD = []

    myStems = []

    for currStart in starts:
        myStem = re.split(stemSplitter, currStart)[0]

        myStems.append(myStem)

        simpleStem = betaCodeOnlyNoAccent(myStem)

        nomSgStem.append(nsSF(simpleStem))
        restStem.append(rSF(simpleStem))


        base = getStemLengths(myStem, core, classification, 0)
        nomSg = nsLF(copy.deepcopy(base))
        rest = rLF(copy.deepcopy(base))

        nomSgSD.append(nomSg)
        restSD.append(rest)

    stem = {
    "nomsg": nomSgStem,
    "rest": restStem
    }
    stemDivision = {
    "nomsg": nomSgSD,
    "rest": restSD
    }

    return myStems, stem, stemDivision




# regexes for third declension consonant stems

# TODO handle "gen. ios or idos" better
#cStemGenFinderRegex = re.compile('$([^,\s]+)(?:u/s|i/n|a), (u[=/]?dos|i[=/]?nos|a[=/]?tos)')
#(?:)?
cStemGenString = ""
# start
cStemGenString += "^([^,\s]+)"
# start endings
cStemGenString += "(?:pais|pous|xeir|[ai]|(?:a|e|h|i|o|u|w|ei|ou)[\+]?[/=_\^]?(?:[crnsy]|gc))"
# middle stuff
cStemGenString += "(?: \[[^\]]*\])?(?: or (?:[^,\s]+))?(?: \(.*\))?(?:, (?:Dor|Ion|Aeol|Att|Ep)\. [^,\s]+(?: \(q\.[\s]*v\.\))?)?, (?:(?:o\(, )?(?:h\(, )?gen\. (?:([^\s]+) or )?)?"
# genitive endings
cStemGenString += "(pai[=/]?d|po[=/]?d|xeir|[aou][/=_\^]?(?:kt|nt)|(?:a|e|h|i|o|u|w|ei)[\+]?[/=_\^]?(?:[ntrdxkgpbq]|gg)?)o/?s"
# last stuff
cStemGenString += "(?: \[[^\]]*\])?[,\$]"


cStemGenFinderRegex = re.compile(cStemGenString)

cStemPluralGenFinderRegex = re.compile('^([^,\s]+)es(?: or ([^,\s]+)es)?(?:, wn)?, (oi\(|ai\(|ta/)')

cStemAtosFinderRegex = re.compile('^([^,\s]+)a/?, to/,')

# get stem and stem division information for a noun that that is a third
# declension consonant stem, e.g. αιξ, αιγος does not

# note this has a TON of exceptions right now, which should be handled
# with better regexes but the additional breakage they would cause
# wasn't something I could handle at the level of tiredness I was (TODO)
def doStemWorkNounConsonantStem(starts, core, classification):
    nomSgStem = []
    restStem = []
    nomSgSD = []
    restSD = []

    myStems = []

    for currStart in starts:
        myStem = currStart

        myStems.append(myStem)
        # simple stuff
        simpleStem = betaCodeOnlyNoAccent(myStem)
        baseLens = getStemLengths(myStem, core, classification, 0)
        nomSg = copy.deepcopy(baseLens)

        regexFind = re.search(cStemGenFinderRegex, core)
        pluralRegexFind = re.search(cStemPluralGenFinderRegex, core)
        atosRegexFind = re.search(cStemAtosFinderRegex, core)


        if (currStart[-4:] == "qric" and core.find("qric, tri^xos") != -1): # dissimilation of aspirates stuff
            restStemText = simpleStem.replace("qric", "trix")
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif not(regexFind == None) and (currStart != "bri^a^ro/xeir" and currStart != "ka^lola/i+gc"):
            # main attempt, which catches most cases
            base = core[regexFind.start(1):regexFind.end(1)]
            #print "bing: " + base
            genEndingAlt = core[regexFind.start(2):regexFind.end(2)]
            genEnding = core[regexFind.start(3):regexFind.end(3)]
            cleanGenEnding = betaCodeOnlyNoAccent(genEnding)
            if (((len(cleanGenEnding) <= 2) and (cleanGenEnding[0] == "a" or cleanGenEnding[0] == "i" or cleanGenEnding[0] == "u"))
                or ((len(cleanGenEnding) == 3) and (((cleanGenEnding[0] == "i") and (cleanGenEnding[1] == "+"))
                or ((cleanGenEnding[0] == "a" or cleanGenEnding[0] == "o" or cleanGenEnding[0] == "u") and (cleanGenEnding[1:3] == "nt" or cleanGenEnding[1:3] == "kt"))
                or ((cleanGenEnding[1] == "g"))))):
                # unknown vowels
                restStemText = betaCodeOnlyNoAccent(base) + cleanGenEnding
                restStemDivision = copy.deepcopy(baseLens)[:-1]

                if (len(cleanGenEnding) == 1):
                    secondPiece = ""
                    firstPiece = cleanGenEnding[0]
                elif (len(cleanGenEnding) == 3):
                    if (cleanGenEnding[1] == "+"):
                        secondPiece = cleanGenEnding[2]
                        firstPiece = cleanGenEnding[0:2]
                    else:
                        secondPiece = cleanGenEnding[1:]
                        firstPiece = cleanGenEnding[0]

                else:
                    secondPiece = cleanGenEnding[1]
                    firstPiece = cleanGenEnding[0]
                shortMatch1 = firstPiece + "/" + secondPiece
                shortMatch2 = firstPiece + "^" + secondPiece
                longMatch1 = firstPiece + "=" + secondPiece
                longMatch2 = firstPiece + "_" + secondPiece
                unknownMatch = cleanGenEnding
                if (genEnding == shortMatch1 or genEnding == shortMatch2):
                    restStemDivision.append(utils.VOWEL_LEN.SHORT)
                elif (genEnding == longMatch1 or genEnding == longMatch2):
                    restStemDivision.append(utils.VOWEL_LEN.LONG)
                elif (genEnding == unknownMatch):
                    restStemDivision.append(utils.VOWEL_LEN.UNKNOWN)
                else:
                    raise Exception("Bad " + cleanGenEnding + "os ending: " + genEnding)
            elif (cleanGenEnding == "pod" or ((len(cleanGenEnding) <= 2) and (cleanGenEnding[0] == "e" or cleanGenEnding[0] == "o"))):
                # short vowels
                restStemText = betaCodeOnlyNoAccent(base) + cleanGenEnding
                restStemDivision = copy.deepcopy(baseLens)[:-1]
                restStemDivision.append(utils.VOWEL_LEN.SHORT)
            elif (cleanGenEnding == "paid" or cleanGenEnding == "xeir" or cleanGenEnding == "eid" or ((len(cleanGenEnding) <= 2) and (cleanGenEnding[0] == "h" or cleanGenEnding[0] == "w"))):
                # long vowels
                restStemText = betaCodeOnlyNoAccent(base) + cleanGenEnding
                restStemDivision = copy.deepcopy(baseLens)[:-1]
                restStemDivision.append(utils.VOWEL_LEN.LONG)
            else:
                restStemText = simpleStem
                restStemDivision = copy.deepcopy(baseLens)
                if VERBOSE:
                    print "~~~~~~~~~~~~~~~~~~~~~~~"
                    print "Stem: " + myStem
                    print "-----"
                    print "Core:"
                    print core
                    print "~~~~~~~~~~~~~~~~~~~~~~~"
        elif not(pluralRegexFind == None):
            restStemText = simpleStem[-2:] # remove -es at the end
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif not(atosRegexFind == None):
            restStemText = simpleStem + "t"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*dhw/"):
            restStemText = "dho"
            restStemDivision = [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.SHORT]
        elif (currStart == "mei/s"):
            restStemText = "mhn"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "grau=s"):
            restStemText = "gra"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "r(i/s"):
            restStemText = "r(in"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "a)pexqh/men"):
            restStemText = "a)pexqhmon"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "e)lefanto/xrws"):
            restStemText = "e)lefantoxrwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fa/y"):
            restStemText = "fab"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "a)gu/naic"):
            restStemText = "a)gunaik"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "e)/pos"):
            restStemText = "e)pe"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT]
        elif (currStart == "ai)/gotriy"):
            restStemText = "ai)gotrib"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sklhro/pous"):
            restStemText = "sklhropod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "tessa^ra^kaieikosi/pous"):
            restStemText = "tessarakaieikosipod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*qrh=|c"):
            restStemText = "qrh|k"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "u(/steros"):
            restStemText = "u(stat"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "a)/xeir"):
            restStemText = "a)xeir"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i(erofu/lac"):
            restStemText = "i(erofulak"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*)ia/ones"):
            restStemText = "i)aon"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "a)na/dema"):
            restStemText = "a)nademat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "u(/fear"):
            restStemText = "u(fear"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "xe/rniy"):
            restStemText = "xernib"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "phri/n"):
            restStemText = "phrin"
            restStemDivision = [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.LONG]
        elif (currStart == "e)piku^li/des"):
            restStemText = "e)pikulid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "fa/os"):
            restStemText = "fae"
            restStemDivision = [utils.VOWEL_LEN.UNKNOWN, utils.VOWEL_LEN.SHORT]
        elif (currStart == "o)/noma"):
            restStemText = "o)nomat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a(ma/macu^s"):
            restStemText = "a(mamacu"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "knh/kwn"):
            restStemText = "knhkwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "h(lioplh/c"):
            restStemText = "h(lioplhg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "khli/s"):
            restStemText = "khlid"
            restStemDivision = [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.LONG]
            nomSg = [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.LONG]
        elif (currStart == "pi/wn"):
            restStemText = "pion"
            restStemDivision = [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.SHORT]
        elif (currStart == "pro/spneuma"):
            restStemText = "prospneumat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "dmw/s"):
            restStemText = "dmw"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "r(i/y"):
            restStemText = "r(ip"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "nu/c"):
            restStemText = "nukt"
            restStemDivision = [utils.VOWEL_LEN.UNKNOWN]
        elif (currStart == "a)na/dhma"):
            restStemText = "a)nadhmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "h(qm/s"):
            restStemText = "h(qm"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "pro/c"):
            restStemText = "prok"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "prw/c"):
            restStemText = "prwk"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "fa/r"):
            restStemText = "far"
            restStemDivision = [utils.VOWEL_LEN.UNKNOWN]
        elif (currStart == "milto/xrws"):
            restStemText = "miltoxrwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mh/trws"):
            restStemText = "mhtrw"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a(/ploqric"):
            restStemText = "a(plotrix"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "zela=s"):
            restStemText = "zel"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "*)argw/"):
            restStemText = "argo"
            restStemDivision = [utils.VOWEL_LEN.UNKNOWN, utils.VOWEL_LEN.SHORT]
        elif (currStart == "o)/mma"):
            restStemText = "o)mma"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "xh/n"):
            restStemText = "xhn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "dokw/"):
            restStemText = "doko"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT]
        elif (currStart == "bra/qu"):
            restStemText = "braqu"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "u(gro/bhc"):
            restStemText = "u(grobhx"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pa?/xuqric"):
            restStemText = "paxutrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "borro/liy"):
            restStemText = "borrolib"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)sth/r"):
            restStemText = "a)ster"
            restStemDivision = [utils.VOWEL_LEN.UNKNOWN, utils.VOWEL_LEN.SHORT]
        elif (currStart == "ge/nos"):
            restStemText = "gen"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "tri/bwn"):
            restStemText = "tribwn"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG]
            nomSg = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG]
        elif (currStart == "klei/s"):
            restStemText = "kleid"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "a)rgi^o/dous"):
            restStemText = "a)rgiodont"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "h(migu/naic"):
            restStemText = "h(migunaik"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "satari/s"):
            restStemText = "satarid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o(mo/xrws"):
            restStemText = "o(moxrwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)/pais"):
            restStemText = "a)paid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mh=kos"):
            restStemText = "mhke"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sa/rc"):
            restStemText = "sark"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ma/rghlis"):
            restStemText = "marghlid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)kuro/ths"):
            restStemText = "a)kurotht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "qhlw/"):
            restStemText = "qhlo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "qu^i+/s"):
            restStemText = "qui+d"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG]
        elif (currStart == "di/neuma"):
            restStemText = "dineumat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)rh/n"):
            restStemText = "a)rn"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "feidw/"):
            restStemText = "feido"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "feidw/"):
            restStemText = "feido"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "r(w/y"):
            restStemText = "r(wp"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "xrw/s"):
            restStemText = "xrwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "spa/dwn"):
            restStemText = "spadwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)rgew/n"):
            restStemText = "o)rgewn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "di^o/nuc"):
            restStemText = "dionux"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT]
        elif (currStart == "ghqulli/s"):
            restStemText = "ghqullid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "u(da^toplh/c"):
            restStemText = "u(datoplhg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "te/ras"):
            restStemText = "tera"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mh/kwn"):
            restStemText = "mhkwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ta^kero/xrws"):
            restStemText = "takeroxrwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pre/sbu^s"):
            restStemText = "pre/sbe"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "xru_soe/qeir"):
            restStemText = "xrusoeqeir"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fle/y"):
            restStemText = "fleb"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sh/kwma"):
            restStemText = "shkwmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "qri/c"):
            restStemText = "trix"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "ki/s"):
            restStemText = "ki"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "e)festri/s"):
            restStemText = "e)festrio"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)nacuri/des"):
            restStemText = "a)nacurid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "qri/y"):
            restStemText = "qrip"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "e)phgkeni/des"):
            restStemText = "e)phgkenid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "te/trac"):
            restStemText = "tetrag"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT]
        elif (currStart == "skni/y"):
            restStemText = "sknip"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "ti/gri^s"):
            restStemText = "ti/gri"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "xqw/n"):
            restStemText = "xqon"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "stri/c"):
            restStemText = "strig"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kwpa_i+/s"):
            restStemText = "kwpai+d"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "gh=rus"):
            restStemText = "ghru"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "klw/y"):
            restStemText = "klwp"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "e)pikra_ti/des"):
            restStemText = "e)pikratid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "sfh/c"):
            restStemText = "sfhk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sfh/n"):
            restStemText = "sfhn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "prwtogu/naikes"):
            restStemText = "prwtogunaik"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "*ka^luyw/"):
            restStemText = "kaluyo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "lu?/kolugc"):
            restStemText = "lu?kolugk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "dusmh/twr"):
            restStemText = "dusmhtor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "knw/y"):
            restStemText = "knwp"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)/kwn"):
            restStemText = "a)kont"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "de/ndreon"):
            restStemText = "dendre"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "bh=ma"):
            restStemText = "bhmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*di^o/pa_n"):
            restStemText = "diopan"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*pa/n"):
            restStemText = "pan"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "bre/tas"):
            restStemText = "brete"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT]
        elif (currStart == "foberodiakra/tores"):
            restStemText = "foberodiakrator"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "kaqh=lic"):
            restStemText = "kaqhlik"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)na/qema"):
            restStemText = "a)naqemat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*proku/wn"):
            restStemText = "proku/n"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT]
        elif (currStart == "tri^xa/i+kes"):
            restStemText = "trixa/i+k"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "a)naire/tis"):
            restStemText = "a)nairetid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ka/xru^s"):
            restStemText = "kaxru"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)rso/qric"):
            restStemText = "o)rsotrix"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT]
        elif (currStart == "kata/phc"):
            restStemText = "kataphg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "h(/sswn"):
            restStemText = "h(sson"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "qh/r"):
            restStemText = "qhr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "qh/s"):
            restStemText = "qht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "gu/y"):
            restStemText = "gup"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "pente/pous"):
            restStemText = "pentepod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "me/geqos"):
            restStemText = "megeqe"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ou)=das"):
            restStemText = "ou)de"
            restStemDivision = [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.SHORT]
        elif (currStart == "a(pa^lo/pais"):
            restStemText = "a(palopaid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "melikra/s"):
            restStemText = "melikrat"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.UNKNOWN, utils.VOWEL_LEN.LONG]
        elif (currStart == "a)ki/nagma"):
            restStemText = "a)kinagmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)kti/s"):
            restStemText = "a)ktin"
            restStemDivision = [utils.VOWEL_LEN.UNKNOWN, utils.VOWEL_LEN.LONG]
            nomSg = [utils.VOWEL_LEN.UNKNOWN, utils.VOWEL_LEN.LONG]
        elif (currStart == "a)steroblh/s"):
            restStemText = "a)steroblht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)nabo/a_ma"):
            restStemText = "a)naboamat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "h)=mar"):
            restStemText = "h)mat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i)/c"):
            restStemText = "i)k"
            restStemDivision = [utils.VOWEL_LEN.LONG]
            nomSg = [utils.VOWEL_LEN.LONG]
        elif (currStart == "i)/dris"):
            restStemText = "i)dri"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pu/rroqric"):
            restStemText = "purrotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "be/kos" or currStart == "beko/s"):
            restStemText = "bek"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pu/c"):
            restStemText = "pug"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "krath/r"):
            restStemText = "krathr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "u(/stric"):
            restStemText = "u(strix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "puci^o/pous"):
            restStemText = "puciopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*sxoinh/|s"):
            restStemText = "sxoinh|d"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*kh/r"):
            restStemText = "khr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mhlodroph=es"):
            restStemText = "mhlodroph"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "kre/c"):
            restStemText = "krek"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ai)/c"):
            restStemText = "ai)g"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "u(droku/wn"):
            restStemText = "u(drokun"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "*sardw/"):
            restStemText = "sardo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "peri/deilos"):
            restStemText = "perideil"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "ste/ar"):
            restStemText = "steat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*stu/c"):
            restStemText = "stug"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "*bri^a/rews"):
            restStemText = "briar"
            restStemDivision = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT]
        elif (currStart == "sklh/roqric"):
            restStemText = "sklhrotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "kra_tobrw/s"):
            restStemText = "kratobrwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "yhfi/s"):
            restStemText = "yhfid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "pai=s"):
            restStemText = "paid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mona/s"):
            restStemText = "monad"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*si^mo/eis"):
            restStemText = "simo/ent"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "xh/r"):
            restStemText = "xhr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)/gli_s"):
            restStemText = "a)gliq"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)/gos"):
            restStemText = "a)ge"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sarkoku/wn"):
            restStemText = "sarkokun"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "poiki?/loqric"):
            restStemText = "poikilotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "la^si^o/pous"):
            restStemText = "lasiopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "fi^loku/wn"):
            restStemText = "filokun"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "moixa^li/s"):
            restStemText = "moixalid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pla/stigc"):
            restStemText = "plastigg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)stroku/wn"):
            restStemText = "a)strokun"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "*cenofw=n"):
            restStemText = "cenofwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ke/ra^s"):
            restStemText = "kera"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "klw/n"):
            restStemText = "klwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "au)tobou=s"):
            restStemText = "au)tobo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "xutri/s"):
            restStemText = "xutrid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "xelwni/a"):
            restStemText = "xelwnid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "stra/gc"):
            restStemText = "stragg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kra/nos"):
            restStemText = "krane"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sfra_gi/s"):
            restStemText = "sfragid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "ga/nos"):
            restStemText = "gane"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)rtu_mata=s"):
            restStemText = "a)rtumatat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mh/stwr"):
            restStemText = "mhstwr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fwtoplh/c"):
            restStemText = "fwtoplhg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)rodemnia/des"):
            restStemText = "o)rodemniad"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "splh/n"):
            restStemText = "splhn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "streblo/pous"):
            restStemText = "streblopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "o)stru/a"):
            restStemText = "o)strua"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "o)/a^r"):
            restStemText = "o)ar"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)/nac"):
            restStemText = "a)nakt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ptw/c"):
            restStemText = "ptwk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "qa/rsos"):
            restStemText = "qarse"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "gleu=kos"):
            restStemText = "gleuke"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "lu/gc"):
            restStemText = "lugg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kh/c"):
            restStemText = "khk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)cue/qeir"):
            restStemText = "o)cueqeir"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "di/zuc"):
            restStemText = "dizug"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "po/rnotrif"):
            restStemText = "pornotrib"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "glau/c"):
            restStemText = "glau/k"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i(/n" or currStart == "ei(/n"):
            restStemText = "ei(n"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "a)tmi/s"):
            restStemText = "a)tmid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*)/aray"):
            restStemText = "a)rab"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "qu^rokigkli/des"):
            restStemText = "qurokigklid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "skambo/pous"):
            restStemText = "skambopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)na/pauma"):
            restStemText = "a)napaumat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "go/nu^"):
            restStemText = "gonat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)e/lloqric"):
            restStemText = "a)ellotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*ku/klwy"):
            restStemText = "kuklwp"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*(ellhspontofu/la^kes"):
            restStemText = "e(llhspontofulak"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "boubwnofu/lac[u^]"):
            restStemText = "boubwnofulak"
            restStemDivision = [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.UNKNOWN]
            simpleStem = "boubwnofulac"
            nomSg = [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.UNKNOWN]
        elif (currStart == "ya/r"):
            restStemText = "yar"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "a)/i+c"):
            restStemText = "a)i+g"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "deiro/pais"):
            restStemText = "deiropaid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*pleia/des"):
            restStemText = "pleiad"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "dh/c"):
            restStemText = "dhk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)|w/n"):
            restStemText = "a)|on"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "tera/mwn"):
            restStemText = "teramwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fi^loqh/c"):
            restStemText = "filoqhk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)sfu=s"):
            restStemText = "o)sfu"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ko/ndu^"):
            restStemText = "kondu"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*ski^a/podes"):
            restStemText = "skiapod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "kalli/xeir"):
            restStemText = "kallixeir"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "eu)/xaris"):
            restStemText = "eu)xarit"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "glw/c"):
            restStemText = "glwk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)e/twma"):
            restStemText = "a)e/twmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ge/lws"):
            restStemText = "gelwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "skoto/frwn"):
            restStemText = "skotofron"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "pta/kis"):
            restStemText = "ptakid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "laio/pous"):
            restStemText = "laiopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "ske/pas"):
            restStemText = "skepa"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sh/r"):
            restStemText = "shr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sh/y"):
            restStemText = "shp"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "dikta/twr"):
            restStemText = "diktato"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*)axelwi+/des"):
            restStemText = "a)xelwi+d"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "h(=lic"):
            restStemText = "h(lik"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "eu)ga_qh/s"):
            restStemText = "eu)gaqht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "maini/s"):
            restStemText = "mainid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "trw/c"):
            restStemText = "trwg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "proi/c"):
            restStemText = "proik"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ma/sswn"):
            restStemText = "masson"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)na/pneuma"):
            restStemText = "a)napneumat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "gru/y"):
            restStemText = "grup"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "tri/pous"):
            restStemText = "tripod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "pla/c"):
            restStemText = "pla/k"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*)aqhnaio/ths"):
            restStemText = "a)qhnaiotht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "xi^tw/n"):
            restStemText = "xitwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "glwxi/n"):
            restStemText = "glwxid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "skh/nhma"):
            restStemText = "skhnhmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "diw=ruc"):
            restStemText = "diwruk"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "se/ri^s"):
            restStemText = "se/rid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ne/oqric"):
            restStemText = "neotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "bla/c"):
            restStemText = "blak"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "karki^no/pous"):
            restStemText = "karkinopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "ktei/s"):
            restStemText = "kten"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "bri^a^ro/xeir"):
            restStemText = "briaroxeir"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fi^lo/qhr"):
            restStemText = "filoqhr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)mpelew/n"):
            restStemText = "a)mpelewn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "qu^ga/thr"):
            restStemText = "qugathr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "prwtoku/wn"):
            restStemText = "prwtokun"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "da/ma^r"):
            restStemText = "damart"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)y"):
            restStemText = "o)p"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i(eromnh/mwn"):
            restStemText = "i(eromnhmon"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "thlo/meli"):
            restStemText = "thlomelit"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "gu^naika/nhr"):
            restStemText = "gunaikand"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "nebri/s"):
            restStemText = "nebrid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kalli^gu/naic"):
            restStemText = "kalligunaik"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kra/s"):
            restStemText = "krat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)llo/ths"):
            restStemText = "a)llotht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "yi/lac"):
            restStemText = "yilak"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "yeudoku/wn"):
            restStemText = "yeudokun"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "peri/sti^xes"):
            restStemText = "peristix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "xri=sma"):
            restStemText = "xrismat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*peiqw/"):
            restStemText = "peiqo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "i)/ugc"):
            restStemText = "i)ugg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o(mo/dais"):
            restStemText = "o(modait"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "qw/y"):
            restStemText = "qwp"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "qw/s"):
            restStemText = "qw"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "skw/y"):
            restStemText = "skwp"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*keltoli/gu^es"):
            restStemText = "keltoligu"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "*)ia/n"):
            restStemText = "i)an"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)gnu/s"):
            restStemText = "a)gnuq"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pamfa^no/wn"):
            restStemText = "pamfanownt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "qi/s"):
            restStemText = "qin"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i)/aspi^s"):
            restStemText = "i)aspid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ptu/c"):
            restStemText = "ptux"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "nekro/xrws"):
            restStemText = "nekroxrwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fh/r"):
            restStemText = "fhr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kisti/s"):
            restStemText = "kistid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "morfw/"):
            restStemText = "morfo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "ga/la"):
            restStemText = "galakt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "stegno/ths"):
            restStemText = "stegnotht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "bra^xu^h=lic"):
            restStemText = "braxuhlik"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "u(/dwr"):
            restStemText = "u(dat"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.UNKNOWN)
        elif (currStart == "a)/rwma"):
            restStemText = "a)rwmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "li^mh/n"):
            restStemText = "lime/n"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "r(u/twr"):
            restStemText = "r(utor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "kerdw/"):
            restStemText = "kerdo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "chro/bhc"):
            restStemText = "chrobhx"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "si/kinni^s"):
            restStemText = "sikinnid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "melagxi/twn"):
            restStemText = "melagxitwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "e)kdoth/r"):
            restStemText = "e)kdothr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)lw/phc"):
            restStemText = "a)lwpek"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "klausi/gelws"):
            restStemText = "klausigelwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)kraifno/ths"):
            restStemText = "a)kraifnotht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)mfipa/tores"):
            restStemText = "a)mfipator"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "h(gemw/n"):
            restStemText = "h(gemon"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)grofu/lac"):
            restStemText = "a)grofulak"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "bw=c"):
            restStemText = "bwk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ma/r"):
            restStemText = "mar"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "gasteroplh/c"):
            restStemText = "gasteroplhk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fri/c"):
            restStemText = "frik"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "ai)gialofu/lac"):
            restStemText = "ai)gialofulak"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "xei/rwn"):
            restStemText = "xeiron"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "koni/podes"):
            restStemText = "konipod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "*trwi+a/s"):
            restStemText = "trwi+ad"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "e)/ndais"):
            restStemText = "e)ndaid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "smi=lac"):
            restStemText = "smilak"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "monomh/twr"):
            restStemText = "monomhtor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "neossi/s"):
            restStemText = "neossid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*sfi/gc"):
            restStemText = "sfigg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "e(/lmins"):
            restStemText = "e(lminq"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "koufo/pous"):
            restStemText = "koufopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "pneuma^to/fws"):
            restStemText = "pneumatofwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fqei/r"):
            restStemText = "fqeir"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)nti/pais"):
            restStemText = "a)ntipaid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "e)/kteisma"):
            restStemText = "e)kteismat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)cu?/rri_n"):
            restStemText = "o)currin"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mi_mw/"):
            restStemText = "mimo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "eu)h/nwr"):
            restStemText = "eu)hnor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*)ia_sw/"):
            restStemText = "i)aso"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)/kroptuc"):
            restStemText = "a)kroptuk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pla/tos"):
            restStemText = "plate"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*mormw/"):
            restStemText = "mormo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "plw/s"):
            restStemText = "plwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "klh/s"):
            restStemText = "klh|d"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i)/stwr"):
            restStemText = "i)stor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "i(/stwr"):
            restStemText = "i(stor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "o)cu^o/dous"):
            restStemText = "o)cuodont"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "ga^laktokra/s"):
            restStemText = "galaktokrat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fw/s"):
            restStemText = "fwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "perisso/frwn"):
            restStemText = "perissofron"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "flukti/s"):
            restStemText = "fluktid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "tri^a_ka/s"):
            restStemText = "triakad"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fa/rugc"):
            restStemText = "farug"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "o(moga/laktes"):
            restStemText = "o(mogalakt"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "xru_seo/dous"):
            restStemText = "xruseodont"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "ka^lola/i+gc"):
            restStemText = "kalolai+gg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)na/sarc"):
            restStemText = "a)na/sark"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)na/sarc"):
            restStemText = "a)na/sark"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kaqhgemw/n"):
            restStemText = "kaqhgemon"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "pei/rins"):
            restStemText = "peirinq"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)/or"):
            restStemText = "a)or"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)=or"):
            restStemText = "a)or"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kath=liy"):
            restStemText = "kathlif"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "genhi+/s"):
            restStemText = "genhi+d"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "baqmi/s"):
            restStemText = "baqmid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fw/r"):
            restStemText = "fwr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mela?/noqric"):
            restStemText = "mela?notrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "smh=nos"):
            restStemText = "smhne"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "dai/s"):
            restStemText = "dait"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "meli^gene/twr"):
            restStemText = "meligenetor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "ei)na/teres"):
            restStemText = "ei)nater"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "ti^qa\s"):
            restStemText = "tiqad"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "e)/nqrhnos"):
            restStemText = "e)nqrhn"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "du/sda^mar"):
            restStemText = "dusdamart"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*(uyw/"):
            restStemText = "u(yo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "gu^ri=nos"):
            restStemText = "gurin"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "dei/s"):
            restStemText = "den"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "foini?koqric"):
            restStemText = "foinikotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)rgu?/rofley"):
            restStemText = "a)rgurofleb"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sti/mmi" or currStart == "sti=mi"):
            restStemText = "stimmi" # TODO or ews or idos
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)mfifw=n"):
            restStemText = "a)mfifwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "gri/pwn"):
            restStemText = "gripwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "diplo/qric"):
            restStemText = "diplotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "perikti/ones"):
            restStemText = "periktion"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "sxa/s"):
            restStemText = "sxad"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "tru/c"):
            restStemText = "trug"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "bou/pais"):
            restStemText = "boupaid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mikrau=lac"):
            restStemText = "mikraulak"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "sxizo/pous"):
            restStemText = "sxizopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "e)pige/nnhma"):
            restStemText = "e)pigennhmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*)inw/"):
            restStemText = "i)no"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "pu=r"):
            restStemText = "pur"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "pa/n"):
            restStemText = "pan"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*ka/r"):
            restStemText = "kar"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "tomarofu/la^kes"):
            restStemText = "tomarofulak"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "h(mera/lwy"):
            restStemText = "th(meralop"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "u(groxi/twn"):
            restStemText = "u(groxitwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "di/pous"):
            restStemText = "dipod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a(rpi/s"):
            restStemText = "a(rpid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "ku^a?/noqric"):
            restStemText = "kuanotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)pospoggisma/"):
            restStemText = "a)pospoggismat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "li?/poqric"):
            restStemText = "lipotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)/naus"):
            restStemText = "a)/na"
            restStemDivision = [utils.VOWEL_LEN.UNKNOWN, utils.VOWEL_LEN.LONG]
        elif (currStart == "li/y"):
            restStemText = "lib"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i)/kti^s"):
            restStemText = "i)ktid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "oi)stroplh/c"):
            restStemText = "oi)stroplhg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*lhtw/"):
            restStemText = "lhto"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "na_ma^si^ph/c"):
            restStemText = "namasiphg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fru/c"):
            restStemText = "frug"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "*sh/r"):
            restStemText = "shr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*qra=|c"):
            restStemText = "qra|k"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mnh=ma"):
            restStemText = "mnhmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sw/frwn"):
            restStemText = "swfron"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "da?/su^qric"):
            restStemText = "dasutrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "te/ttic"):
            restStemText = "tettig"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "a)/rshn"):
            restStemText = "a)rsen"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "ka/lli^floc"):
            restStemText = "kalliflog"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "da+mosiofu/la^kes"):
            restStemText = "da+mosiofulak"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "i(ppoku/wn"):
            restStemText = "i(ppokun"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "e)rusi/xqwn"):
            restStemText = "e)rusi/xqon"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "ma/rtu^s"):
            restStemText = "martur"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "nw/y"):
            restStemText = "nwp"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "teta^no/qric"):
            restStemText = "tetanotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "parasxi/des"):
            restStemText = "parasxid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "a(/ls)"):
            restStemText = "a(l"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "tra^go/pa_n"):
            restStemText = "tragopan"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "nikhth/r"):
            restStemText = "nikhthr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kra/tos"):
            restStemText = "krate"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ku/wn"):
            restStemText = "kun"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "ku^no/dous"):
            restStemText = "kunodont"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "fre/ar"):
            restStemText = "freat"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "pa^th/r"):
            restStemText = "pater"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "pemfi/s"):
            restStemText = "pemfid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.UNKNOWN)
        elif (currStart == "*borea/s"):
            restStemText = "boread"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*trw/s"):
            restStemText = "*trw"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i(la/eis"):
            restStemText = "i(laen"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "o(/moqric"):
            restStemText = "o(motrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "kolo/xeir"):
            restStemText = "koloxeir"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*sti/c"):
            restStemText = "stik"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "r(a/c"):
            restStemText = "r(ag"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "qhlupteri/s"):
            restStemText = "qhlupterid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "me/loy"):
            restStemText = "melop"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "tri^ti/renes"):
            restStemText = "tritiren"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "mico/qhr"):
            restStemText = "micoqhr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)h/r"):
            restStemText = "a)er"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "pa/trws"):
            restStemText = "patrw"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "h)i+w/n"):
            restStemText = "h)i+on"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*)aellw/"):
            restStemText = "ae)llo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "o)/qric"):
            restStemText = "o)trix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "sth/mwn"):
            restStemText = "sthmon"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "yi/c"):
            restStemText = "yik"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "kni/y"):
            restStemText = "knip"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "w)=s"):
            restStemText = "w)t"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "a)le/ktwr"):
            restStemText = "a)lektor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "strouqo/pous"):
            restStemText = "strouqopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "au)to/pu_r"):
            restStemText = "au)topur"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "pu^ri^no/qric"):
            restStemText = "purinotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "forki/des"):
            restStemText = "forkid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "a)xh/n"):
            restStemText = "a)xhn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*)anqrwfhraklh=s"):
            restStemText = "a)nqrwfhraklhe"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "o)nh/twr"):
            restStemText = "o)nhtor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "tlh/mwn"):
            restStemText = "tlhmon"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "w)/y"):
            restStemText = "w)p"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)yi/klwy"):
            restStemText = "o)yiklwp"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "na^kokle/y"):
            restStemText = "nakoklep"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "spa/ka"):
            restStemText = "spak"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "r(w/c"):
            restStemText = "r(wg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)i+zu/s"):
            restStemText = "o)i+zu"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "fi^locenofw=n"):
            restStemText = "filocenofwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o(mh=lic"):
            restStemText = "o(mhlik"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "tri^o/dous"):
            restStemText = "triodont"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*mi/nws"):
            restStemText = "minw"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "r(a^fi/s"):
            restStemText = "r(afid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "smh=ma"):
            restStemText = "smhmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i)/ktar"):
            restStemText = "i)ktar"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ba^ru^brw/s"):
            restStemText = "barubrwt"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ya^ka/s"):
            restStemText = "yakad"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "h(/rws"):
            restStemText = "h(rw"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "phne/loy"):
            restStemText = "phnelop"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "bh/c"):
            restStemText = "bhx"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sfhno/pous"):
            restStemText = "sfhnopod"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "yedno/qric"):
            restStemText = "yednotrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "fra/thr"):
            restStemText = "frater"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "blh/xwn"):
            restStemText = "blhxwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pw=u"):
            restStemText = "pwe"
            restStemDivision = [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.SHORT]
        elif (currStart == "proiti/des"):
            restStemText = "proitid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "flo/c"):
            restStemText = "flog"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*qra^sw/"):
            restStemText = "qraso"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "stai=s"):
            restStemText = "stait"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ponti^fec"):
            restStemText = "pontifik"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "a)ntilh/ptwr"):
            restStemText = "a)ntilhptor"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "*za/n"):
            restStemText = "zan"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*eu)meni/des"):
            restStemText = "eu)menid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "e)pith/deuma"):
            restStemText = "e)pithdeumat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "i(ero/xqwn"):
            restStemText = "i(eroxqon"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "toiouto/ths"):
            restStemText = "toiouto/tht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "lexw/"):
            restStemText = "lexo"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "prw/n"):
            restStemText = "prwn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)mpw/lhma"):
            restStemText = "a)mpwlhmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "korsa=s"):
            restStemText = "korsat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ca/nqoqric"):
            restStemText = "canqoqrix"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "kwfo/ths"):
            restStemText = "kwfotht"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "kla/|c"):
            restStemText = "klak"
            restStemDivision = [utils.VOWEL_LEN.LONG]
        elif (currStart == "ba/ros"):
            restStemText = "bar"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "sh=ma"):
            restStemText = "shmat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "peri/xqwn"):
            restStemText = "perixqon"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "xauli^o/dous"):
            restStemText = "xauliodont"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "yh/r"):
            restStemText = "yhr"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "mega^lorrw/c"):
            restStemText = "megalorrwg"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "frh/n"):
            restStemText = "fren"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "yh/n"):
            restStemText = "yhn"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pari/ske[yis]"):
            restStemText = "pariskeyi"
            restStemDivision = copy.deepcopy(baseLens)
            simpleStem = "pari/skeyis"
        elif (currStart == "a(yi/s"):
            restStemText = "ayid"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.LONG)
        elif (currStart == "a)bra^mi/s" or currStart == "a)/bramis"):
            restStemText = "a)bramid"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "dai+/s"):
            restStemText = "dai+d"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "a)popla/stwp"):
            restStemText = "a)poplastop"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "pnu/c"):
            restStemText = "puk"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pru^le/es"):
            restStemText = "prule"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "a)rto/meli"):
            restStemText = "a)rtomelit"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*kelti/bhres"):
            restStemText = "keltibhr"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
        elif (currStart == "mu=s"):
            restStemText = "mu"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "e)ru^si?/pelas"):
            restStemText = "e)rusipelat"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "ma^taio/frwn"):
            restStemText = "mataiofron"
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "ka/lai+s"):
            restStemText = "kalai+d"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*dhmh/thr"):
            restStemText = "dhmhter" #TODO and dhmhtros
            restStemDivision = copy.deepcopy(baseLens)[:-1]
            restStemDivision.append(utils.VOWEL_LEN.SHORT)
        elif (currStart == "polu/sku^lac"):
            restStemText = "poluskulak"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "polu/sku^lac"):
            restStemText = "poluskulak"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "o)/y"):
            restStemText = "o)p"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "sugklei/s"):
            restStemText = "sugkleit"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "*ma/r"):
            restStemText = "mar"
            restStemDivision = copy.deepcopy(baseLens)
        elif (currStart == "pta/c"):
            restStemText = "ptak"
            restStemDivision = [utils.VOWEL_LEN.SHORT]
        elif (currStart == "monw/y"):
            restStemText = "monwp"
            restStemDivision = copy.deepcopy(baseLens)
        else:
            restStemText = simpleStem
            restStemDivision = copy.deepcopy(baseLens)
            if VERBOSE:
                print "~~~~~~~~~~~~~~~~~~~~~~~"
                print "Stem: " + myStem
                print "-----"
                print "Core:"
                print core
                print "~~~~~~~~~~~~~~~~~~~~~~~"


        nomSgStem.append(simpleStem)
        nomSgSD.append(nomSg)
        restStem.append(restStemText)
        restSD.append(restStemDivision)

    stem = {
    "nomsg": nomSgStem,
    "rest": restStem
    }
    stemDivision = {
    "nomsg": nomSgSD,
    "rest": restSD
    }

    return myStems, stem, stemDivision





# information for creating verb forms
vowelStartRegex = re.compile("^(ai|a\||au|oi|ei|eu|a|e|i|o|u)")
vowelStart2Regex = re.compile("^(w|h)")
# augment transitions
augmentVowels = {
"a": "h",
"e": "h",
"i": "i",
"o": "w",
"u": "u",
"ai": "h|",
"a|": "h|",
"au": "hu",
"oi": "w|",
"ei": "h|",
"eu": "hu"
}
# add an augment to a verb
def augmentStem(stem, lens):
    # TODO: handle splitting off prepositions
    oldLens = copy.deepcopy(lens)
    vowelStartMatch = re.search(vowelStartRegex, stem)
    vowelStart2Match = re.search(vowelStart2Regex, stem)
    if not(vowelStartMatch == None):
        match = stem[vowelStartMatch.start(1):vowelStartMatch.end(1)]
        rest = stem[vowelStartMatch.end(1):]
        newStart = augmentVowels[match]
        newStem = newStart + rest
        newLens = [utils.VOWEL_LEN.LONG]
        newLens.extend(lens[1:])
    elif not(vowelStart2Match == None):
        newStem = copy.deepcopy(stem)
        newLens = lens
    else:
        newStem = "e)" + stem
        newLens = [utils.VOWEL_LEN.SHORT]
        newLens.extend(lens)
    return newStem, stem, newLens, oldLens

# sigmatize a verb
def sigmatizeStem(fullStart, contractVowel, stem, lens):
    if len(stem) == 0:
        return "s", lens
    last = stem[-1]
    if (contractVowel == "a"):
        stem += "hs"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "e"):
        stem += "hs"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "o"):
        stem += "ws"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "ei"):
        stem += "eis"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (last == "p" or last == "f" or last == "b" or stem[-2:] == "pt"):
        stem = stem[:-1] + "y"
    elif (last == "d" or last == "t" or last == "q"):
        stem = stem[:-1] + "s"
    elif (last == "g" or last == "k" or last == "x"):
        stem = stem[:-1] + "c"
    elif (last == "z"):
        stem = stem[:-1] + "s"
    elif (stem[-2:] == "tt" or stem[-2:] == "ss"):
        stem = stem[:-2] + "s" #TODO or cw
    else:
        stem = stem + "s"
    return stem, lens


# convert from present stem to unaugmented aorist passive
def aorPassivizeStem(fullStart, contractVowel, stem, lens):
    if len(stem) == 0:
        return "q", lens
    last = stem[-1]
    if (contractVowel == "a"):
        stem += "hq"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "e"):
        stem += "hq"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "o"):
        stem += "wq"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "ei"):
        stem += "eiq"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (last == "p" or last == "f" or last == "b" or stem[-2:] == "pt"):
        stem = stem[:-1] + "fq"
    elif (last == "g" or last == "k" or last == "x"):
        stem = stem[:-1] + "xq"
    elif (last == "d" or last == "t" or last == "q"):
        stem = stem[:-1] + "sq"
    elif (last == "z"):
        stem = stem[:-1] + "sq"
    elif (stem[-2:] == "tt" or stem[-2:] == "ss"):
        stem = stem[:-2] + "sq" #TODO or xq
    else:
        stem = stem + "q"
    return stem, lens

# convert from unaugmented aorist passive to future aorist passive stem
def futPassivizeStem(stem, lens):
    newStem = stem + "hs"
    lens.append(utils.VOWEL_LEN.LONG)
    return newStem, lens

consonantNoRhoRegex = re.compile("[bcdfgjklmnpqstvxyz]")
vowelRegex = re.compile("[aehiouw]")
muteRegex = re.compile("[pbfkgxtdq]")
liquidRegex = re.compile("[rlmn]")
# is this just a simple consonant other than rho at the start?
def type1Redup(stem):
    if (len(stem) == 0):
        return False
    if not(re.search(consonantNoRhoRegex, stem[0]) == None) and (len(stem) == 1 or not(re.search(vowelRegex, stem[1]) == None)):
        return True
    return False

# is this a mute followed by a liquid?
def type2Redup(stem):
    if (len(stem) == 0):
        return False
    if not(re.search(muteRegex, stem[0]) == None) and (len(stem) > 1 and not(re.search(liquidRegex, stem[1]) == None)):
        return True
    return False

# guess the reduplication of a stem
def reduplicateStem(stem, lens):
    oldLens = copy.deepcopy(lens)
    vowelStartMatch = re.search(vowelStartRegex, stem)
    vowelStart2Match = re.search(vowelStart2Regex, stem)
    if not(vowelStartMatch == None):
        match = stem[vowelStartMatch.start(1):vowelStartMatch.end(1)]
        rest = stem[vowelStartMatch.end(1):]
        newStart = augmentVowels[match]
        newStem = newStart + rest
        newLens = [utils.VOWEL_LEN.LONG]
        newLens.extend(lens[1:])
    elif not(vowelStart2Match == None):
        newStem = copy.deepcopy(stem)
        newLens = lens
    else:
        if (type1Redup(stem) or type2Redup(stem)):
            newStem = stem[0] + "e" + stem
            newLens = [utils.VOWEL_LEN.SHORT]
            newLens.extend(lens)
        else:
            newStem = "e)" + stem
            newLens = [utils.VOWEL_LEN.SHORT]
            newLens.extend(lens)
    return newStem, newLens

# guess the perfect active stem of a verb from its present form
def perfectizeActivizeVerb(fullStart, contractVowel, stem, lens):
    stem, lens = reduplicateStem(stem, lens)
    if len(stem) == 0:
        return "k", lens
    last = stem[-1]
    if (contractVowel == "a"):
        stem += "hk"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "e"):
        stem += "hk"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "o"):
        stem += "wk"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "ei"):
        stem += "eik"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (last == "p" or last == "f" or last == "b" or stem[-2:] == "pt"):
        stem = stem[:-1] + "f"
    elif (last == "g" or last == "k" or last == "x"):
        stem = stem[:-1] + "x"
    elif (last == "d" or last == "t" or last == "q"):
        stem = stem[:-1] + "k"
    elif (last == "z"):
        stem = stem[:-1] + "k"
    elif (stem[-2:] == "tt" or stem[-2:] == "ss"):
        stem = stem[:-2] + "k" #TODO or x
    else:
        stem = stem + "k"
    return stem, lens

# guess the perfect passive stem of a verb from its present form
def perfectizePassivizeVerb(fullStart, contractVowel, stem, lens):
    stem, lens = reduplicateStem(stem, lens)
    last = stem[-1]
    if len(stem) == 0:
        return "", lens
    if (contractVowel == "a"):
        stem += "h"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "e"):
        stem += "h"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "o"):
        stem += "w"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (contractVowel == "ei"):
        stem += "ei"
        lens.append(utils.VOWEL_LEN.LONG)
    elif (last == "p" or last == "f" or last == "b" or stem[-2:] == "pt"):
        stem = stem[:-1] + "m" # mmai
    elif (last == "g" or last == "k" or last == "x"):
        stem = stem[:-1] + "g" # gmai
    elif (last == "d" or last == "t" or last == "q"):
        stem = stem[:-1] + "s"# smai
    elif (last == "z"):
        stem = stem[:-1] + "s"
    elif (stem[-2:] == "tt" or stem[-2:] == "ss"):
        stem = stem[:-1] + "s" #TODO or g
    else:
        stem = stem
    return stem, lens

# get the future perfect setups
def futurePerfectize(stem, lens):
    return stem + "s", lens

# handle verbs
def processVerbStandard(start, stemSplitter, contractVowel, core, classification):

    myStem = re.split(stemSplitter, start)[0]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres, presLens = (simpleStem, copy.deepcopy(baseLens))
    sig, sigLens = sigmatizeStem(start, contractVowel, simpleStem, copy.deepcopy(baseLens))
    futActMid, futActMidLens = (copy.deepcopy(sig), copy.deepcopy(sigLens))
    aorActMidY, aorActMidN, aorActMidYLens, aorActMidNLens = augmentStem(copy.deepcopy(sig), copy.deepcopy(sigLens))
    aorPassBase, aorPassBaseLens = aorPassivizeStem(start, contractVowel, simpleStem, copy.deepcopy(baseLens))
    perfAct, perfActLens = perfectizeActivizeVerb(start, contractVowel, simpleStem, copy.deepcopy(baseLens))
    perfMP, perfMPLens = perfectizePassivizeVerb(start, contractVowel, simpleStem, copy.deepcopy(baseLens))

    # phase 2: check core
    # TODO

    # guess secondary
    imperfY, imperfN, imperfYLens, imperfNLens = augmentStem(copy.deepcopy(pres), copy.deepcopy(presLens))

    aorPassY, aorPassN, aorPassYLens, aorPassNLens = augmentStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))
    futPass, futPassLens = futPassivizeStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))


    plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
    plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    futperf, futperfLens = futurePerfectize(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    # check secondary
    # TODO

    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid, "pass": futPass},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY},
            "pass": {"n": aorPassN, "y": aorPassY}
        },
        "perf": {"act": perfAct, "mp": perfMP},
        "plup": {
            "act": {"n": plupActN, "y": plupActY},
            "mp": {"n": plupMPN, "y": plupMPY}
        },
        "futperf": futperf
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens, "pass": futPassLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens},
            "pass": {"n": aorPassNLens, "y": aorPassYLens}
        },
        "perf": {"act": perfActLens, "mp": perfMPLens},
        "plup": {
            "act": {"n": plupActNLens, "y": plupActYLens},
            "mp": {"n": plupMPNLens, "y": plupMPYLens}
        },
        "futperf": futperfLens
    }

    return myStem, stem, stemDivision

    if (False):
        stem = {
            "pres": {
                "act": "tiq",
                "mp": "tiq"
            },
            "imperf": {
                "act": {"n": "tiq", "y": "e)tiq"},
                "mp": {"n": "tiq", "y": "e)tiq"}
            },
            "fut": {
                "act": "qhs",
                "mid": "qhs",
                "pass": ""
            },
            "aor": {
                "act": {"n": "qhk", "y": "e)qhk"},
                "mid": {"n": "qhk", "y": "e)qhk"},
                "pass": {"n": "", "y": ""}
            },
            "perf": {
                "act": "teqhk",
                "mp": ""
            },
            "plup": {
                "act": "",
                "mp": ""
            }
        }
        stemDivision= {
            "pres": {
                "act": ["s"],
                "mp": ["s"]
            },
            "imperf": {
                "act": {"n": ["s"], "y": ["s", "s"]},
                "mp": {"n": ["s"], "y": ["s", "s"]}
            },
            "fut": {
                "act": ["s"],
                "mid": ["s"],
                "pass": []
            },
            "aor": {
                "act": {"n": ["l"], "y": ["s", "l"]},
                "mid": {"n": ["l"], "y": ["s", "l"]},
                "pass": {"n": [], "y": []}
            },
            "perf": {
                "act": ["s", "l"],
                "mp": []
            },
            "plup": {
                "act": [],
                "mp": []
            }
        }

# handle verbs that are aorist only
def processVerbAorOnly(start, stemSplitter, contractVowel, core, classification):

    myStem = re.split(stemSplitter, start)[0]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    aorActMidY, aorActMidYLens = (simpleStem, copy.deepcopy(baseLens))
    aorActMidN, aorActMidNLens = (simpleStem, copy.deepcopy(baseLens))

    # phase 2: check core
    # TODO

    # check secondary
    # TODO

    # TODO:  te/mei, from tetmon, as a present
    # TODO: a)ne/tlh, from a)netlhn; as imperfect
    stem = {
        "imperf": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY}
        },
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY}
        }
    }
    stemDivision= {
        "imperf": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens}
        },
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens}
        }
    }

    return myStem, stem, stemDivision


# handle verbs that appear in infinitive forms
def processVerbInfinitive(start, stemSplitter, contractVowel, core, classification):

    myStem = re.split(stemSplitter, start)[0]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres, presLens = (simpleStem, copy.deepcopy(baseLens))
    aorActMidY, aorActMidYLens = (simpleStem, copy.deepcopy(baseLens))
    aorActMidN, aorActMidNLens = (simpleStem, copy.deepcopy(baseLens))

    perfAct, perfActLens = perfectizeActivizeVerb(start, contractVowel, simpleStem, copy.deepcopy(baseLens))
    perfMP, perfMPLens = perfectizePassivizeVerb(start, contractVowel, simpleStem, copy.deepcopy(baseLens))

    # phase 2: check core
    # TODO

    stem = {
        "pres": {"act": pres, "mp": pres},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY}
        },
        "perf": {"act": perfAct, "mp": perfMP}
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens}
        },
        "perf": {"act": perfActLens, "mp": perfMPLens}
    }

    return myStem, stem, stemDivision

# handle -umi verbs
def processVerbUmi(start, stemSplitter, contractVowel, core, classification):

    myStem = re.split(stemSplitter, start)[0]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # TODO: kera/nnumi futures
    if (simpleStem[-2:] == "nn"): # strwnnumi or kera/nnumi
        restStem = simpleStem[:-2]
        restLens = copy.deepcopy(baseLens)
    elif (simpleStem[-2:] == "mn"): # omnumi
        restStem = simpleStem[:-2]
        restLens = copy.deepcopy(baseLens)
    elif (simpleStem[-2:] == "ll"): # apollumi
        restStem = simpleStem[:-2]
        restLens = copy.deepcopy(baseLens)
    elif (simpleStem[-1:] == "n"): # mei/gnumi
        restStem = simpleStem[:-1]
        restLens = copy.deepcopy(baseLens)
    else:
        restStem = simpleStem
        restLens = copy.deepcopy(baseLens)

    # phase 1: guess core
    pres, presLens = (simpleStem, copy.deepcopy(baseLens))
    sig, sigLens = sigmatizeStem(start, contractVowel, restStem, copy.deepcopy(restLens))
    futActMid, futActMidLens = (copy.deepcopy(sig), copy.deepcopy(sigLens))
    aorActMidY, aorActMidN, aorActMidYLens, aorActMidNLens = augmentStem(copy.deepcopy(sig), copy.deepcopy(sigLens))
    aorPassBase, aorPassBaseLens = aorPassivizeStem(start, contractVowel, restStem, copy.deepcopy(restLens))
    perfAct, perfActLens = perfectizeActivizeVerb(start, contractVowel, restStem, copy.deepcopy(restLens))
    perfMP, perfMPLens = perfectizePassivizeVerb(start, contractVowel, restStem, copy.deepcopy(restLens))

    # phase 2: check core
    # TODO

    # guess secondary
    imperfY, imperfN, imperfYLens, imperfNLens = augmentStem(copy.deepcopy(pres), copy.deepcopy(presLens))

    aorPassY, aorPassN, aorPassYLens, aorPassNLens = augmentStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))
    futPass, futPassLens = futPassivizeStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))


    plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
    plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    futperf, futperfLens = futurePerfectize(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    # check secondary
    # TODO

    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid, "pass": futPass},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY},
            "pass": {"n": aorPassN, "y": aorPassY}
        },
        "perf": {"act": perfAct, "mp": perfMP},
        "plup": {
            "act": {"n": plupActN, "y": plupActY},
            "mp": {"n": plupMPN, "y": plupMPY}
        },
        "futperf": futperf
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens, "pass": futPassLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens},
            "pass": {"n": aorPassNLens, "y": aorPassYLens}
        },
        "perf": {"act": perfActLens, "mp": perfMPLens},
        "plup": {
            "act": {"n": plupActNLens, "y": plupActYLens},
            "mp": {"n": plupMPNLens, "y": plupMPYLens}
        },
        "futperf": futperfLens
    }

    return myStem, stem, stemDivision


# handle eimi
def processVerbEimi(start, stemSplitter, contractVowel, core, classification):

    myMatch = re.search(stemSplitter, start)
    myStem = start[myMatch.start(1):myMatch.end(1)]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres = simpleStem
    presLens = copy.deepcopy(baseLens)

    futActMid = simpleStem + "es"
    futActMidLens = copy.deepcopy(baseLens)
    futActMidLens.append(utils.VOWEL_LEN.SHORT)


    # guess secondary
    imperfY = simpleStem
    imperfN = simpleStem
    imperfYLens = copy.deepcopy(baseLens)
    imperfNLens = copy.deepcopy(baseLens)


    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid}
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens}
    }

    return myStem, stem, stemDivision


# handle isthmi
def processVerbIsthmi(start, stemSplitter, contractVowel, core, classification):

    myMatch = re.search(stemSplitter, start)
    myStem = start[myMatch.start(1):myMatch.end(1)]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres = simpleStem + "ist"
    presLens = copy.deepcopy(baseLens)
    presLens.append(utils.VOWEL_LEN.LONG)

    futActMid = simpleStem + "sths"
    futActMidLens = copy.deepcopy(baseLens)
    futActMidLens.append(utils.VOWEL_LEN.LONG)

    aorActMidY = simpleStem + "esths"
    aorActMidYLens = copy.deepcopy(baseLens)
    aorActMidYLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG])

    aorActMidN = simpleStem + "sths"
    aorActMidNLens = copy.deepcopy(baseLens)
    aorActMidNLens.append(utils.VOWEL_LEN.LONG)

    aorPassBase = simpleStem + "staq"
    aorPassBaseLens = copy.deepcopy(baseLens)
    aorPassBaseLens.append(utils.VOWEL_LEN.SHORT)


    perfAct = simpleStem + "estak"
    perfActLens = copy.deepcopy(baseLens)
    perfActLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT])

    perfMP = simpleStem + "esta"
    perfMPLens = copy.deepcopy(baseLens)
    perfMPLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT])

    # TODO

    # guess secondary
    imperfY, imperfN, imperfYLens, imperfNLens = augmentStem(copy.deepcopy(pres), copy.deepcopy(presLens))

    aorPassY, aorPassN, aorPassYLens, aorPassNLens = augmentStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))
    futPass, futPassLens = futPassivizeStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))


    plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
    plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    # TODO; esthn

    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid, "pass": futPass},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY},
            "pass": {"n": aorPassN, "y": aorPassY}
        },
        "perf": {"act": perfAct, "mp": perfMP},
        "plup": {
            "act": {"n": plupActN, "y": plupActY},
            "mp": {"n": plupMPN, "y": plupMPY}
        }
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens, "pass": futPassLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens},
            "pass": {"n": aorPassNLens, "y": aorPassYLens}
        },
        "perf": {"act": perfActLens, "mp": perfMPLens},
        "plup": {
            "act": {"n": plupActNLens, "y": plupActYLens},
            "mp": {"n": plupMPNLens, "y": plupMPYLens}
        }
    }

    return myStem, stem, stemDivision


# handle didwmi
def processVerbDidwmi(start, stemSplitter, contractVowel, core, classification):

    myMatch = re.search(stemSplitter, start)
    myStem = start[myMatch.start(1):myMatch.end(1)]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres = simpleStem + "did"
    presLens = copy.deepcopy(baseLens)
    presLens.append(utils.VOWEL_LEN.SHORT)

    futActMid = simpleStem + "dws"
    futActMidLens = copy.deepcopy(baseLens)
    futActMidLens.append(utils.VOWEL_LEN.LONG)

    aorActMidY = simpleStem + "edwk"
    aorActMidYLens = copy.deepcopy(baseLens)
    aorActMidYLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG])

    aorActMidN = simpleStem + "dwk"
    aorActMidNLens = copy.deepcopy(baseLens)
    aorActMidNLens.append(utils.VOWEL_LEN.LONG)

    aorPassBase = simpleStem + "doq"
    aorPassBaseLens = copy.deepcopy(baseLens)
    aorPassBaseLens.append(utils.VOWEL_LEN.SHORT)


    perfAct = simpleStem + "dedwk"
    perfActLens = copy.deepcopy(baseLens)
    perfActLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG])

    perfMP = simpleStem + "dedw"
    perfMPLens = copy.deepcopy(baseLens)
    perfMPLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG])

    # guess secondary
    imperfY, imperfN, imperfYLens, imperfNLens = augmentStem(copy.deepcopy(pres), copy.deepcopy(presLens))

    aorPassY, aorPassN, aorPassYLens, aorPassNLens = augmentStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))
    futPass, futPassLens = futPassivizeStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))


    plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
    plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    futperf, futperfLens = futurePerfectize(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid, "pass": futPass},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY},
            "pass": {"n": aorPassN, "y": aorPassY}
        },
        "perf": {"act": perfAct, "mp": perfMP},
        "plup": {
            "act": {"n": plupActN, "y": plupActY},
            "mp": {"n": plupMPN, "y": plupMPY}
        },
        "futperf": futperf
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens, "pass": futPassLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens},
            "pass": {"n": aorPassNLens, "y": aorPassYLens}
        },
        "perf": {"act": perfActLens, "mp": perfMPLens},
        "plup": {
            "act": {"n": plupActNLens, "y": plupActYLens},
            "mp": {"n": plupMPNLens, "y": plupMPYLens}
        },
        "futperf": futperfLens
    }

    return myStem, stem, stemDivision


# handle other -wmi
def processVerbWmi(start, stemSplitter, contractVowel, core, classification):

    myMatch = re.search(stemSplitter, start)
    myStem = start[myMatch.start(1):myMatch.end(1)]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres, presLens = (simpleStem, copy.deepcopy(baseLens))

    basePlusLong = copy.deepcopy(baseLens)
    basePlusLong.append(utils.VOWEL_LEN.LONG)
    basePlusShort = copy.deepcopy(baseLens)
    basePlusShort.append(utils.VOWEL_LEN.SHORT)

    sig, sigLens = sigmatizeStem(start, contractVowel, simpleStem+"w", copy.deepcopy(basePlusLong))
    futActMid, futActMidLens = (copy.deepcopy(sig), copy.deepcopy(sigLens))
    aorActMidY, aorActMidN, aorActMidYLens, aorActMidNLens = augmentStem(copy.deepcopy(sig), copy.deepcopy(sigLens))
    aorPassBase, aorPassBaseLens = aorPassivizeStem(start, contractVowel, simpleStem+"o", copy.deepcopy(basePlusShort))
    perfAct, perfActLens = perfectizeActivizeVerb(start, contractVowel, simpleStem+"w", copy.deepcopy(basePlusLong))
    perfMP, perfMPLens = perfectizePassivizeVerb(start, contractVowel, simpleStem+"w", copy.deepcopy(basePlusLong))

    # guess secondary
    imperfY, imperfN, imperfYLens, imperfNLens = augmentStem(copy.deepcopy(pres), copy.deepcopy(presLens))

    aorPassY, aorPassN, aorPassYLens, aorPassNLens = augmentStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))
    futPass, futPassLens = futPassivizeStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))


    plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
    plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    futperf, futperfLens = futurePerfectize(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid, "pass": futPass},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY},
            "pass": {"n": aorPassN, "y": aorPassY}
        },
        "perf": {"act": perfAct, "mp": perfMP},
        "plup": {
            "act": {"n": plupActN, "y": plupActY},
            "mp": {"n": plupMPN, "y": plupMPY}
        },
        "futperf": futperf
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens, "pass": futPassLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens},
            "pass": {"n": aorPassNLens, "y": aorPassYLens}
        },
        "perf": {"act": perfActLens, "mp": perfMPLens},
        "plup": {
            "act": {"n": plupActNLens, "y": plupActYLens},
            "mp": {"n": plupMPNLens, "y": plupMPYLens}
        },
        "futperf": futperfLens
    }

    return myStem, stem, stemDivision

# handle ihmi
def processVerbIhmi(start, stemSplitter, contractVowel, core, classification):

    myMatch = re.search(stemSplitter, start)
    myStem = start[myMatch.start(1):myMatch.end(1)]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres = simpleStem + "i"
    presLens = copy.deepcopy(baseLens)
    presLens.append(utils.VOWEL_LEN.UNKNOWN) # can be both

    futActMid = simpleStem + "hs"
    futActMidLens = copy.deepcopy(baseLens)
    futActMidLens.append(utils.VOWEL_LEN.LONG)

    aorActMidY = simpleStem + "hk"
    aorActMidYLens = copy.deepcopy(baseLens)
    aorActMidYLens.extend([utils.VOWEL_LEN.LONG])

    aorActMidN = simpleStem + "hk"
    aorActMidNLens = copy.deepcopy(baseLens)
    aorActMidNLens.append(utils.VOWEL_LEN.LONG)

    aorPassBase = simpleStem + "eq"
    aorPassBaseLens = copy.deepcopy(baseLens)
    aorPassBaseLens.append(utils.VOWEL_LEN.SHORT)


    perfAct = simpleStem + "eik"
    perfActLens = copy.deepcopy(baseLens)
    perfActLens.extend([utils.VOWEL_LEN.LONG])

    perfMP = simpleStem + "ei"
    perfMPLens = copy.deepcopy(baseLens)
    perfMPLens.extend([utils.VOWEL_LEN.LONG])

    # guess secondary
    imperfY, imperfN, imperfYLens, imperfNLens = augmentStem(copy.deepcopy(pres), copy.deepcopy(presLens))

    aorPassY, aorPassN, aorPassYLens, aorPassNLens = augmentStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))
    futPass, futPassLens = futPassivizeStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))


    plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
    plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    futperf, futperfLens = futurePerfectize(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid, "pass": futPass},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY},
            "pass": {"n": aorPassN, "y": aorPassY}
        },
        "perf": {"act": perfAct, "mp": perfMP},
        "plup": {
            "act": {"n": plupActN, "y": plupActY},
            "mp": {"n": plupMPN, "y": plupMPY}
        },
        "futperf": futperf
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens, "pass": futPassLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens},
            "pass": {"n": aorPassNLens, "y": aorPassYLens}
        },
        "perf": {"act": perfActLens, "mp": perfMPLens},
        "plup": {
            "act": {"n": plupActNLens, "y": plupActYLens},
            "mp": {"n": plupMPNLens, "y": plupMPYLens}
        },
        "futperf": futperfLens
    }

    return myStem, stem, stemDivision

# handle tiqhmi
def processVerbTiqhmi(start, stemSplitter, contractVowel, core, classification):

    myMatch = re.search(stemSplitter, start)
    myStem = start[myMatch.start(1):myMatch.end(1)]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres = simpleStem + "tiq"
    presLens = copy.deepcopy(baseLens)
    presLens.append(utils.VOWEL_LEN.SHORT)

    futActMid = simpleStem + "qhs"
    futActMidLens = copy.deepcopy(baseLens)
    futActMidLens.append(utils.VOWEL_LEN.LONG)

    aorActMidY = simpleStem + "eqhk"
    aorActMidYLens = copy.deepcopy(baseLens)
    aorActMidYLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG])

    aorActMidN = simpleStem + "qhk"
    aorActMidNLens = copy.deepcopy(baseLens)
    aorActMidNLens.append(utils.VOWEL_LEN.LONG)

    aorPassBase = simpleStem + "teq"
    aorPassBaseLens = copy.deepcopy(baseLens)
    aorPassBaseLens.append(utils.VOWEL_LEN.SHORT)


    perfAct = simpleStem + "teqhk"
    perfActLens = copy.deepcopy(baseLens)
    perfActLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG])

    perfMP = simpleStem + "teqh"
    perfMPLens = copy.deepcopy(baseLens)
    perfMPLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG])

    # guess secondary
    imperfY, imperfN, imperfYLens, imperfNLens = augmentStem(copy.deepcopy(pres), copy.deepcopy(presLens))

    aorPassY, aorPassN, aorPassYLens, aorPassNLens = augmentStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))
    futPass, futPassLens = futPassivizeStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))


    plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
    plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    futperf, futperfLens = futurePerfectize(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid, "pass": futPass},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY},
            "pass": {"n": aorPassN, "y": aorPassY}
        },
        "perf": {"act": perfAct, "mp": perfMP},
        "plup": {
            "act": {"n": plupActN, "y": plupActY},
            "mp": {"n": plupMPN, "y": plupMPY}
        },
        "futperf": futperf
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens, "pass": futPassLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens},
            "pass": {"n": aorPassNLens, "y": aorPassYLens}
        },
        "perf": {"act": perfActLens, "mp": perfMPLens},
        "plup": {
            "act": {"n": plupActNLens, "y": plupActYLens},
            "mp": {"n": plupMPNLens, "y": plupMPYLens}
        },
        "futperf": futperfLens
    }

    return myStem, stem, stemDivision


# handle other -hmi
def processVerbHmi(start, stemSplitter, contractVowel, core, classification):

    myMatch = re.search(stemSplitter, start)
    myStem = start[myMatch.start(1):myMatch.end(1)]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres, presLens = (simpleStem, copy.deepcopy(baseLens))

    basePlusLong = copy.deepcopy(baseLens)
    basePlusLong.append(utils.VOWEL_LEN.LONG)
    basePlusShort = copy.deepcopy(baseLens)
    basePlusShort.append(utils.VOWEL_LEN.SHORT)

    sig, sigLens = sigmatizeStem(start, contractVowel, simpleStem+"h", copy.deepcopy(basePlusLong))
    futActMid, futActMidLens = (copy.deepcopy(sig), copy.deepcopy(sigLens))
    aorActMidY, aorActMidN, aorActMidYLens, aorActMidNLens = augmentStem(copy.deepcopy(sig), copy.deepcopy(sigLens))
    aorPassBase, aorPassBaseLens = aorPassivizeStem(start, contractVowel, simpleStem+"e", copy.deepcopy(basePlusShort))
    perfAct, perfActLens = perfectizeActivizeVerb(start, contractVowel, simpleStem+"h", copy.deepcopy(basePlusLong))
    perfMP, perfMPLens = perfectizePassivizeVerb(start, contractVowel, simpleStem+"h", copy.deepcopy(basePlusLong))

    # guess secondary
    imperfY, imperfN, imperfYLens, imperfNLens = augmentStem(copy.deepcopy(pres), copy.deepcopy(presLens))

    aorPassY, aorPassN, aorPassYLens, aorPassNLens = augmentStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))
    futPass, futPassLens = futPassivizeStem(copy.deepcopy(aorPassBase), copy.deepcopy(aorPassBaseLens))


    plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
    plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    futperf, futperfLens = futurePerfectize(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid, "pass": futPass},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY},
            "pass": {"n": aorPassN, "y": aorPassY}
        },
        "perf": {"act": perfAct, "mp": perfMP},
        "plup": {
            "act": {"n": plupActN, "y": plupActY},
            "mp": {"n": plupMPN, "y": plupMPY}
        },
        "futperf": futperf
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens, "pass": futPassLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens},
            "pass": {"n": aorPassNLens, "y": aorPassYLens}
        },
        "perf": {"act": perfActLens, "mp": perfMPLens},
        "plup": {
            "act": {"n": plupActNLens, "y": plupActYLens},
            "mp": {"n": plupMPNLens, "y": plupMPYLens}
        },
        "futperf": futperfLens
    }

    return myStem, stem, stemDivision

# handle fhmi
def processVerbFhmi(start, stemSplitter, contractVowel, core, classification):

    myMatch = re.search(stemSplitter, start)
    myStem = start[myMatch.start(1):myMatch.end(1)]
    simpleStem = betaCodeOnlyNoAccent(myStem)
    baseLens = getStemLengths(myStem, core, classification, 0)

    # phase 1: guess core
    pres = simpleStem + "f"
    presLens = copy.deepcopy(baseLens)

    futActMid = simpleStem + "fhs"
    futActMidLens = copy.deepcopy(baseLens)
    futActMidLens.append(utils.VOWEL_LEN.LONG)

    aorActMidY = simpleStem + "efhs"
    aorActMidYLens = copy.deepcopy(baseLens)
    aorActMidYLens.extend([utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG])

    aorActMidN = simpleStem + "fhs"
    aorActMidNLens = copy.deepcopy(baseLens)
    aorActMidNLens.append(utils.VOWEL_LEN.LONG)

    perfMP = simpleStem + "pef"
    perfMPLens = copy.deepcopy(baseLens)
    perfMPLens.extend([utils.VOWEL_LEN.SHORT])

    # guess secondary
    imperfY, imperfN, imperfYLens, imperfNLens = augmentStem(copy.deepcopy(pres), copy.deepcopy(presLens))

    plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    futperf, futperfLens = futurePerfectize(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

    stem = {
        "pres": {"act": pres, "mp": pres},
        "imperf": {
            "act": {"n": imperfN, "y": imperfY},
            "mp": {"n": imperfN, "y": imperfY}
        },
        "fut": {"act": futActMid, "mid": futActMid},
        "aor": {
            "act": {"n": aorActMidN, "y": aorActMidY},
            "mid": {"n": aorActMidN, "y": aorActMidY}
        },
        "perf": {"mp": perfMP},
        "plup": {
            "mp": {"n": plupMPN, "y": plupMPY}
        },
        "futperf": futperf
    }
    stemDivision= {
        "pres": {"act": presLens, "mp": presLens},
        "imperf": {
            "act": {"n": imperfNLens, "y": imperfYLens},
            "mp": {"n": imperfNLens, "y": imperfYLens}
        },
        "fut": {"act": futActMidLens, "mid": futActMidLens},
        "aor": {
            "act": {"n": aorActMidNLens, "y": aorActMidYLens},
            "mid": {"n": aorActMidNLens, "y": aorActMidYLens}
        },
        "perf": {"mp": perfMPLens},
        "plup": {
            "mp": {"n": plupMPNLens, "y": plupMPYLens}
        },
        "futperf": futperfLens
    }

    return myStem, stem, stemDivision

# function for finding the link
def fullFindLink(myRE, core):
    split = re.split(myRE, core)
    if (len(split) > 1):
        restOfCore = split[1]
        link = findLink(restOfCore)
    else:
        restOfCore = ""
        link = ""
    return restOfCore, link

# print that a match failed
def printMatchFail(start, core, classification):
    print "MATCH FAIL:"
    print "Start: " + start
    print "--------"
    print "Classification: " + classification
    print "--------"
    print "Core:"
    print core
    print "============================="

# print everything from the handler
def printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link):
    print "Start: " + start
    print "--------"
    print "Core:"
    print core
    print "--------"
    print "Stem:"
    print myStems
    print "--------"
    print "Stem object:"
    print stem
    print "--------"
    print "Stem Division:"
    print stemDivision
    print "--------"
    print "Rest of Core:"
    print restOfCore
    print "--------"
    print "Link: " + link
    print "============================="






#-------------------
# individual handlers
# they take the first word, the core text, and the associated classification
# and return the full set for the word.

# the default handler
def placeholder(start, core, classification):
    if start == "e)xis": # todo make sure this isn't caught
        return noun3i(start, core, utils.ENDING_TYPES.NOUN.THIRD_IOTA)
    elif start == "h)mi/" or start == "fhmi/":
        return verbAthematic(start, core, utils.ENDING_TYPES.VERB.ATHEMATIC)
    elif start == "sa/os":
        return threeTermAHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A)
    elif start == "dedokhme/nos":
        return threeTermHHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H)
    elif start == "keka^fhw/s":
            return adj3WSHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.MIXED_WS_UIA_OS)
    elif start == "h(=mai":
        return verbDeponent(start, core, utils.ENDING_TYPES.VERB.DEPONENT)
    elif start == "a)lo/w" or start == "e)pi/sxw":
        return verbThematic(start, core, utils.ENDING_TYPES.VERB.THEMATIC)
    elif start == "e)rga^qei=n":
        return verbInfinitive(start, core, utils.ENDING_TYPES.VERB.INFINITIVE)
    elif start == "suno/xwka":
        myStem = "sunoxw"
        perfAct = "sunoxwk"
        perfActLens = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG]
        perfMP = "sunoxw"
        perfMPLens = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG]
        plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
        plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

        stem = {
            "imperf": {
                "act": {"n": perfAct, "y": perfAct},
                "mp": {"n": perfMP, "y": perfMP}
            },
            "perf": {"act": perfAct, "mp": perfMP},
            "plup": {
                "act": {"n": plupActN, "y": plupActY},
                "mp": {"n": plupMPN, "y": plupMPY}
            },
        }
        stemDivision= {
            "imperf": {
                "act": {"n": perfActLens, "y": perfActLens},
                "mp": {"n": perfMPLens, "y": perfMPLens}
            },
            "perf": {"act": perfActLens, "mp": perfMPLens},
            "plup": {
                "act": {"n": plupActNLens, "y": plupActYLens},
                "mp": {"n": plupMPNLens, "y": plupMPYLens}
            },
        }
        return utils.POS.VERB, "", utils.ENDING_TYPES.VERB.THEMATIC, stem, stemDivision, False, ""
    elif start == "te/qhpa":
        myStem = "teqhp"
        perfAct = "teqhp"
        perfActLens = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG]
        perfMP = "teqhm"
        perfMPLens = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG]
        plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
        plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

        aorActMidN = "taf"
        aorActMidY = "e)taf"
        aorActMidNLens = [utils.VOWEL_LEN.UNKNOWN]
        aorActMidYLens = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.UNKNOWN]

        stem = {
            "imperf": {
                "act": {"n": perfAct, "y": perfAct},
                "mp": {"n": perfMP, "y": perfMP}
            },
            "aor": {
                "act": {"n": aorActMidN, "y": aorActMidY},
                "mid": {"n": aorActMidN, "y": aorActMidY}
            },
            "perf": {"act": perfAct, "mp": perfMP},
            "plup": {
                "act": {"n": plupActN, "y": plupActY},
                "mp": {"n": plupMPN, "y": plupMPY}
            },
        }
        stemDivision= {
            "imperf": {
                "act": {"n": perfActLens, "y": perfActLens},
                "mp": {"n": perfMPLens, "y": perfMPLens}
            },
            "aor": {
                "act": {"n": aorActMidNLens, "y": aorActMidYLens},
                "mid": {"n": aorActMidNLens, "y": aorActMidYLens}
            },
            "perf": {"act": perfActLens, "mp": perfMPLens},
            "plup": {
                "act": {"n": plupActNLens, "y": plupActYLens},
                "mp": {"n": plupMPNLens, "y": plupMPYLens}
            },
        }
        return utils.POS.VERB, "", utils.ENDING_TYPES.VERB.THEMATIC, stem, stemDivision, False, ""
    elif start == "a)/nwga":
        myStem = "a)nwg"
        perfAct = "a)nwg"
        perfActLens = [utils.VOWEL_LEN.UNKNOWN, utils.VOWEL_LEN.LONG]
        perfMP = "a)nwg"
        perfMPLens = [utils.VOWEL_LEN.UNKNOWN, utils.VOWEL_LEN.LONG]
        plupActY, plupActN, plupActYLens, plupActNLens = augmentStem(copy.deepcopy(perfAct), copy.deepcopy(perfActLens))
        plupMPY, plupMPN, plupMPYLens, plupMPNLens = augmentStem(copy.deepcopy(perfMP), copy.deepcopy(perfMPLens))

        sig, sigLens = sigmatizeStem(start, "", perfAct, copy.deepcopy(perfActLens))
        aorActMidY, aorActMidN, aorActMidYLens, aorActMidNLens = augmentStem(copy.deepcopy(sig), copy.deepcopy(sigLens))


        stem = {
            "imperf": {
                "act": {"n": perfAct, "y": perfAct},
                "mp": {"n": perfMP, "y": perfMP}
            },
            "aor": {
                "act": {"n": aorActMidN, "y": aorActMidY},
                "mid": {"n": aorActMidN, "y": aorActMidY}
            },
            "perf": {"act": perfAct, "mp": perfMP},
            "plup": {
                "act": {"n": plupActN, "y": plupActY},
                "mp": {"n": plupMPN, "y": plupMPY}
            },
        }
        stemDivision= {
            "imperf": {
                "act": {"n": perfActLens, "y": perfActLens},
                "mp": {"n": perfMPLens, "y": perfMPLens}
            },
            "aor": {
                "act": {"n": aorActMidNLens, "y": aorActMidYLens},
                "mid": {"n": aorActMidNLens, "y": aorActMidYLens}
            },
            "perf": {"act": perfActLens, "mp": perfMPLens},
            "plup": {
                "act": {"n": plupActNLens, "y": plupActYLens},
                "mp": {"n": plupMPNLens, "y": plupMPYLens}
            },
        }
        return utils.POS.VERB, "", utils.ENDING_TYPES.VERB.THEMATIC, stem, stemDivision, False, ""
    elif start == "a)/lalke":
        myStem = "a)/lalk"
        baseStem = "a)lalk"
        baseLens = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.UNKNOWN]
        aorActMidY, aorActMidN, aorActMidYLens, aorActMidNLens = augmentStem(copy.deepcopy(baseStem), copy.deepcopy(baseLens))

        stem = {
            "aor": {
                "act": {"n": aorActMidN, "y": aorActMidY},
                "mid": {"n": aorActMidN, "y": aorActMidY}
            }
        }
        stemDivision= {
            "aor": {
                "act": {"n": aorActMidNLens, "y": aorActMidYLens},
                "mid": {"n": aorActMidNLens, "y": aorActMidYLens}
            }
        }
        return utils.POS.VERB, "", utils.ENDING_TYPES.VERB.THEMATIC, stem, stemDivision, False, ""
    elif start == "oi)=da" or start == "ei)sanei=don":
        classification = utils.ENDING_TYPES.VERB.OIDA

    #raise Exception("Missing Function " + start + "; " + classification)
    pos = "??"
    division = ""
    endingType = classification
    stem = betaCodeOnlyNoAccent(start)
    stemDivision = getStemLengths(stem, core, classification, 0)
    irregular = False
    if classification == utils.ENDING_TYPES.VERB.EOIKA or classification == utils.ENDING_TYPES.VERB.GEGWNA or classification == utils.ENDING_TYPES.VERB.OIDA:
        irregular = True
        pos = "verb"
    elif (endingType == utils.ENDING_TYPES.NOUN.POUS or endingType == utils.ENDING_TYPES.NOUN.ASTU or endingType == utils.ENDING_TYPES.NOUN.BOUS or endingType == utils.ENDING_TYPES.NOUN.GERAS or endingType == utils.ENDING_TYPES.NOUN.GHRAS or endingType == utils.ENDING_TYPES.NOUN.DORU or endingType == utils.ENDING_TYPES.NOUN.DRUS or endingType == utils.ENDING_TYPES.NOUN.HMEROKALLES or endingType == utils.ENDING_TYPES.NOUN.IQUS or endingType == utils.ENDING_TYPES.NOUN.IS or endingType == utils.ENDING_TYPES.NOUN.KREAS or endingType == utils.ENDING_TYPES.NOUN.KWAS or endingType == utils.ENDING_TYPES.NOUN.LAGWS or endingType == utils.ENDING_TYPES.NOUN.DAKRU or endingType == utils.ENDING_TYPES.NOUN.NAUS or endingType == utils.ENDING_TYPES.NOUN.PELAKUS or endingType == utils.ENDING_TYPES.NOUN.PUQW or endingType == utils.ENDING_TYPES.NOUN.XEIR or endingType == utils.ENDING_TYPES.NOUN.XREW or endingType == utils.ENDING_TYPES.NOUN.XREWN or endingType == utils.ENDING_TYPES.NOUN.ZEUS):
        irregular = True
        pos = "noun"
    elif (endingType == utils.ENDING_TYPES.PRONOUN.EGW or endingType == utils.ENDING_TYPES.PRONOUN.MIN or endingType == utils.ENDING_TYPES.PRONOUN.SFEIS):
        irregular = True
        pos = "pron"
    elif (start == "a)/mfw" or endingType == utils.ENDING_TYPES.ADJECTIVE.EIS or endingType == utils.ENDING_TYPES.ADJECTIVE.O or endingType == utils.ENDING_TYPES.ADJECTIVE.ODE or endingType == utils.ENDING_TYPES.ADJECTIVE.OS or endingType == utils.ENDING_TYPES.ADJECTIVE.TIS or endingType == utils.ENDING_TYPES.ADJECTIVE.MEGAS or endingType == utils.ENDING_TYPES.ADJECTIVE.PLEIWN or endingType == utils.ENDING_TYPES.ADJECTIVE.POLUS or endingType == utils.ENDING_TYPES.ADJECTIVE.DUO):
        irregular = True
        pos = "adj"
    link = ""
    return pos, division, endingType, stem, stemDivision, irregular, link

# oi ai regex
oiAiRegex = re.compile("^([^\s]+)oi( \[[^\]]\])?, ai,")
# two terminatino adjectives handler
def twoTermHandler(start, core, classification):
    if not(re.search(oiAiRegex, start) == None):
        return threeTermHHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H)
    elif (start == "o)ppopoi=" or start == "u(popro/st(" or start == "o)totoi="):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    elif (start == "deilokatafronhth/s"):#TODO
        start = "deilokatafro/nhtos"
    elif (start == "gumnh/siai" or start == "*kua/neai"):#TODO
        return noun1A(start, core, utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN)
    elif (start == "i(ppa/striai" or start == "a)/ntai&lt;*&gt;" or start == "e)popoi=" or start == "*ke/ws"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    elif (start == "tri?/xoto"):
        start = "tri?/xotonos"
        core = core.replace("  [nos", "nos")
    elif (start == "sumplei/ones"):
        return adj3HSHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_HS )
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("(o[/\^]?s|oi/?)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'o/?n,', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def twoTermAHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("w/?s$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'w/?n[\s]*[,:](?: gen\. w,)?', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

is3DecNounRegex = re.compile("^([^\s]+)ou=s, ou=ntos[,\s]")
def twoTermOHandler(start, core, classification):
    if not(re.search(is3DecNounRegex, core) == None):
        pos = utils.POS.NOUN
        division = ""
        stemSplitter = re.compile("ou=s$")

        classification = utils.ENDING_TYPES.NOUN.THIRD_CONSONANT
        endingType = classification
        starts = getMultipleStarts(start, core, classification)

        def nomFunc(s):
            return s + "ous"
        def stemFunc(s):
            return s + "ount"

        def nomLensFunc(ls):
            ls.append(utils.VOWEL_LEN.LONG)
            return ls
        def stemLensFunc(ls):
            ls.append(utils.VOWEL_LEN.LONG)
            return ls

        (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, nomFunc, stemFunc, nomLensFunc, stemLensFunc)

        irregular = False
        (restOfCore, link) = fullFindLink(r'o\(,(?: contr\. fr\. puramo/eis,)?', core) #("", "")
        if (re.search(stemSplitter, start) == None):
            printMatchFail(start, core, classification)
        if VERY_VERBOSE:
            printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
        return pos, division, endingType, stem, stemDivision, irregular, link
    elif start[-4:] == "pous":
        return adj3PousHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.POUS_FOOT)
    elif start == "a)po/ploos(B)":
        start = "a)po/ploos"
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("(ou=?s|oos)$") # todo; handle oos separately

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'w/?n[\s]*[,:](?: gen\. w,)?', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def threeTermAHandler(start, core, classification):
    if start == "skiw/dion":
        start = "skiw/dios"
    elif start == "ga/i+os[a_]":
        start = "ga/i+os"
    elif (start == "*khfisi/s"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("(o[/\^]?s|a[=/\^]?|oi[/]?)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'o/?n,', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def threeTermHHandler(start, core, classification):
    if start == "a)rii/hqen":
        start = "*)arka^diko/s"
    elif start == "u(pe/rpolus":
        return adjPolusHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.POLUS)
    elif (start == "lhri/as"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("(o[/\^]?s|h[=/\^]?|ws)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'o/?n,', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def threeTermeAHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("(ou=s|eos)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'a=, ou=n,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def threeTermeHHandler(start, core, classification):
    if start == "xa/lkeos":
        return threeTermAHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A)
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("ou=s$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'ou=n,', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adj3HSHandler(start, core, classification):
    if (start == "a)drai/a"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("(h/?s|es)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'e/?s[\s]*[,:]', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

regexOusaMatch = re.compile("^([^\s]+)wn, ousa")
def adj3WNHandler(start, core, classification):
    if not(re.search(regexOusaMatch, core) == None):
        return pplWn(start, core, utils.ENDING_TYPES.PARTICIPLE.WN)
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("w[/=]?n$")

    starts = getMultipleStarts(start, core, classification)

    def mascNomFunc(s):
        return s
    def neutNomFunc(s):
        return s
    def mascStemFunc(s):
        return s + "on"
    def femStemFunc(s):
        return s + "on"
    def neutStemFunc(s):
        return s + "on"

    def mascNomLensFunc(ls):
        return ls
    def neutNomLensFunc(ls):
        return ls
    def mascLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def neutLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'gen\. onos,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adj3USHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("u/?\^?s$")

    starts = getMultipleStarts(start, core, classification)

    def femStemFunc(s):
        return s + "ei"
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, femStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, femLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'u/?[\s]*[,:]', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link


def adj3PousHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("pous$")

    starts = getMultipleStarts(start, core, classification)

    def mascNomFunc(s):
        return s + "pous"
    def neutNomFunc(s):
        return s + "poun"
    def mascStemFunc(s):
        return s + "pod"
    def femStemFunc(s):
        return s + "pod"
    def neutStemFunc(s):
        return s + "pod"

    def mascNomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def neutNomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def mascLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def neutLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'gen\. podos,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link


def adj3EisHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("eis$")

    starts = getMultipleStarts(start, core, classification)

    def mascNomFunc(s):
        return s + "eis"
    def neutNomFunc(s):
        return s + "en"
    def mascStemFunc(s):
        return s + "ent"
    def femStemFunc(s):
        return s + "ess"
    def neutStemFunc(s):
        return s + "ent"

    def mascNomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def neutNomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def mascLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def neutLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'ou=n,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adj3oEisHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("ou=s$")

    starts = getMultipleStarts(start, core, classification)

    def mascNomFunc(s):
        return s + "ous"
    def neutNomFunc(s):
        return s + "oun"
    def mascStemFunc(s):
        return s + "ount"
    def femStemFunc(s):
        return s + "ouss"
    def neutStemFunc(s):
        return s + "ount"

    def mascNomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def neutNomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def mascLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def neutLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'ou=n,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link



def adjMixedHNHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("h(?:_)?n$")

    starts = getMultipleStarts(start, core, classification)

    def femStemFunc(s):
        return s + "ein"
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, femStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, femLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r', \$\$', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adj3ASHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("a(_)?s$")

    starts = getMultipleStarts(start, core, classification)

    def femStemFunc(s):
        return s + "ain"
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, femStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, femLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r', \$\$', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adj3WSHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("w/s$")

    starts = getMultipleStarts(start, core, classification)

    def femStemFunc(s):
        return s + "ui"
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, femStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, femLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'ui=a, o/s', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

utils.ENDING_TYPES.NOUN.THIRD_CONSONANT
idosCStemRegex = re.compile("^()(?:[^\s]+)is(( or|, (Dor|Ion|Aeol|Att|Ep|[Pp]oet)\.) [^\s]+)?( \(not [^\s]+( [^\s]+)?\))?( \(-pri=stis cod\.\))?( \(sc\. [^,\s]+\))?( \([A-Z]\))?( \[[^\]]*\]| \((pro)?(parox|perisp)\.\))?, (?:i\)?[_/\^]?[dtq]?os[,\s])")
def adjIS_IHandler(start, core, classification):
    if not(re.search(idosCStemRegex, core) == None) or start == "e)/fhlis" or start == "mnh=stis" or start == "*trwgodu/tis" or start == "vi/lsis" or start == "nea=nis":
        return noun3c(start, core, utils.ENDING_TYPES.NOUN.THIRD_CONSONANT)
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("i/?s$")

    starts = getMultipleStarts(start, core, classification)



    # TODO: cut this down to be more conservative
    # -ews
    def mascNomFunc(s):
        return s
    def neutNomFunc(s):
        return s
    def mascStemFunc(s):
        return s
    def femStemFunc(s):
        return s
    def neutStemFunc(s):
        return s

    def mascNomLensFunc(ls):
        return ls
    def neutNomLensFunc(ls):
        return ls
    def mascLensFunc(ls):
        return ls
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def neutLensFunc(ls):
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)

    # -eos
    def mascStemFunc(s):
        return s + "e"
    def femStemFunc(s):
        return s + "e"
    def neutStemFunc(s):
        return s + "e"

    def mascLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def neutLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls

    (myStems1, stem1, stemDivision1) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)

    # -ios
    def mascStemFunc(s):
        return s + "i"
    def femStemFunc(s):
        return s + "i"
    def neutStemFunc(s):
        return s + "i"

    (myStems2, stem2, stemDivision2) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)

    # -ios
    def mascStemFunc(s):
        return s + "id"
    def femStemFunc(s):
        return s + "id"
    def neutStemFunc(s):
        return s + "id"

    (myStems3, stem3, stemDivision3) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)
    myStems.extend(myStems1)
    myStems.extend(myStems2)
    myStems.extend(myStems3)
    stem["mascNom"].extend(stem1["mascNom"])
    stem["neutNom"].extend(stem1["neutNom"])
    stem["masc"].extend(stem1["masc"])
    stem["fem"].extend(stem1["fem"])
    stem["neut"].extend(stem1["neut"])
    stem["mascNom"].extend(stem2["mascNom"])
    stem["neutNom"].extend(stem2["neutNom"])
    stem["masc"].extend(stem2["masc"])
    stem["fem"].extend(stem2["fem"])
    stem["neut"].extend(stem2["neut"])
    stem["mascNom"].extend(stem3["mascNom"])
    stem["neutNom"].extend(stem3["neutNom"])
    stem["masc"].extend(stem3["masc"])
    stem["fem"].extend(stem3["fem"])
    stem["neut"].extend(stem3["neut"])
    stemDivision["mascNom"].extend(stemDivision1["mascNom"])
    stemDivision["neutNom"].extend(stemDivision1["neutNom"])
    stemDivision["masc"].extend(stemDivision1["masc"])
    stemDivision["fem"].extend(stemDivision1["fem"])
    stemDivision["neut"].extend(stemDivision1["neut"])
    stemDivision["mascNom"].extend(stemDivision2["mascNom"])
    stemDivision["neutNom"].extend(stemDivision2["neutNom"])
    stemDivision["masc"].extend(stemDivision2["masc"])
    stemDivision["fem"].extend(stemDivision2["fem"])
    stemDivision["neut"].extend(stemDivision2["neut"])
    stemDivision["mascNom"].extend(stemDivision3["mascNom"])
    stemDivision["neutNom"].extend(stemDivision3["neutNom"])
    stemDivision["masc"].extend(stemDivision3["masc"])
    stemDivision["fem"].extend(stemDivision3["fem"])
    stemDivision["neut"].extend(stemDivision3["neut"])


    irregular = False
    (restOfCore, link) = fullFindLink(r'ui=a, o/s', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adjPasHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("pa[=_]?s$")

    starts = getMultipleStarts(start, core, classification)

    def mascNomFunc(s):
        return s + "pas"
    def neutNomFunc(s):
        return s + "pan"
    def mascStemFunc(s):
        return s + "pant"
    def femStemFunc(s):
        return s + "pas"
    def neutStemFunc(s):
        return s + "pant"

    def mascNomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def neutNomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls
    def mascLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def neutLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'pa[=_]n', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adjAutouHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("ou=$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'ou=,', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adjOsdeHHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("o/?sde$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'o/?nde[\s]*[,:]', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adjOsdeAHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("o/?sde$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'o/?nde[\s]*[,:]', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adjEisHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("ei\(?[=/]?s$")

    starts = getMultipleStarts(start, core, classification)

    if (start == "ei(=s"):
        suffix = "mi"
        shorts = [utils.VOWEL_LEN.SHORT]
    else:
        suffix = "emi"
        shorts = [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.SHORT]

    def mascNomFunc(s):
        return s
    def neutNomFunc(s):
        return s
    def mascStemFunc(s):
        return s
    def femStemFunc(s):
        return s + suffix
    def neutStemFunc(s):
        return s

    def mascNomLensFunc(ls):
        return ls
    def neutNomLensFunc(ls):
        return ls
    def mascLensFunc(ls):
        return ls
    def femLensFunc(ls):
        ls.extend(shorts)
        return ls
    def neutLensFunc(ls):
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)



    irregular = True
    (restOfCore, link) = fullFindLink(r'e/n', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link


def adjTisHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("is")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = ("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link


def adjMegasHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("a\^?s$")

    starts = getMultipleStarts(start, core, classification)

    def femStemFunc(s):
        return s + "al"
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, femStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, femLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = ("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def adjPolusHandler(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("u[/\^]?s$")

    starts = getMultipleStarts(start, core, classification)
    def mascNomFunc(s):
        return s
    def neutNomFunc(s):
        return s
    def mascStemFunc(s):
        return s + "l"
    def femStemFunc(s):
        return s + "l"
    def neutStemFunc(s):
        return s + "l"

    def mascNomLensFunc(ls):
        return ls
    def neutNomLensFunc(ls):
        return ls
    def mascLensFunc(ls):
        return ls
    def femLensFunc(ls):
        return ls
    def neutLensFunc(ls):
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, mascNomFunc, neutNomFunc, mascStemFunc, femStemFunc, neutStemFunc, mascNomLensFunc, neutNomLensFunc, mascLensFunc, femLensFunc, neutLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'po[=/\^]?lu[=/\^]?,', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

# alpha end matcher
alphaMatchRegex = re.compile("a[=/_\^]?$")
etaMatchRegex = re.compile("h[=/_]?$")
alphaSigmaMatchRegex = re.compile("a[=/_]?s$")
etaSigmaMatchRegex = re.compile("h[=/_]?s$")
def noun1A(start, core, classification):
    if (start == "bu_nok[opi/a]"):
        start = "bu_nokopi/a"
    elif (start == "kastanikai/"): # TODO
        start = "kastane/a"
    elif (start == "*lu^ai=os"): # TODO
        start = "*lu^ai=a"
    elif not(re.search(etaMatchRegex, start) == None):
        return noun1H(start, core, utils.ENDING_TYPES.NOUN.FIRST_H)
    elif not(re.search(alphaSigmaMatchRegex, start) == None):
        return noun2as(start, core, utils.ENDING_TYPES.NOUN.SECOND_AS)
    elif not(re.search(etaSigmaMatchRegex, start) == None):
        return noun2hs(start, core, utils.ENDING_TYPES.NOUN.SECOND_HS)
    elif (start == "e)pita/de" or start == "matako\s" or start == "klu^tote/rmwn" or start == "khto/dorpos" or start == "suntonolu_disti\\" or start == "skolophi+\s" or start == "pa_w/tar"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    #"to/rma^"
    pos = utils.POS.NOUN
    division = ""
    if (utils.isShortAlphaStem(start) or start[-1] == "^"):
        endingType = utils.ENDING_TYPES.NOUN.FIRST_A_SHORT
    else:
        endingType = utils.ENDING_TYPES.NOUN.FIRST_A_LONG
    stemSplitter = re.compile("(a[\^_=/\\\\]?|ai/?)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'h\(,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun1H(start, core, classification):
    if not(re.search(alphaMatchRegex, start) == None):
        return noun1A(start, core, utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN)
    elif (start == "prokomi^d"):
        start = "prokomi^dh/"
    elif (start == "gri_phi\s" or start == "*prome/neios" or start == "*tri_twnia\s" or start == "ku^nofo/ntis" or start == "ka)k" or start == "dwroceni/as" or start == "o)yi^ga^mi/ou" or start == "e)fe/simos" or start == "*)epimhli/des"
          or start == "yeudeggra^fh=s" or start == "e)leuqeropra_si/ou" or start == "khpi/des" or start == "e)cou/lhs"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("(h[\(\^_=/\\\\]?|ai/?)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'h\(,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

# handle nouns in -pous
def nounPousHandler(start, core):
    pos = utils.POS.NOUN
    division = ""
    classification = utils.ENDING_TYPES.NOUN.POUS
    endingType = classification
    stemSplitter = re.compile("pou[=/]?[sn]$")

    starts = getMultipleStarts(start, core, classification)

    def nomFunc(s):
        return s + "pous"
    def stemFunc(s):
        return s + "pod"

    def nomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def stemLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, nomFunc, stemFunc, nomLensFunc, stemLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'gen\. podos,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

# handle nouns in -pous
def nounDousHandler(start, core):
    pos = utils.POS.NOUN
    division = ""
    classification = utils.ENDING_TYPES.NOUN.THIRD_CONSONANT
    endingType = classification
    stemSplitter = re.compile("dous$")

    starts = getMultipleStarts(start, core, classification)

    def nomFunc(s):
        return s + "dous"
    def stemFunc(s):
        return s + "dont"

    def nomLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls
    def stemLensFunc(ls):
        ls.append(utils.VOWEL_LEN.SHORT)
        return ls

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, nomFunc, stemFunc, nomLensFunc, stemLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'dontos,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def nounoOsHandler(start, core):
    pos = utils.POS.NOUN
    division = ""
    classification = utils.ENDING_TYPES.NOUN.SECOND_oOS
    endingType = classification
    stemSplitter = re.compile("ou=?s$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'o\(,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

regexPousMatch = re.compile("^([^\s]*)pou[=/]?s$")
regexOusOuMatch = re.compile("^([^\s]*)ou=?s, ou=?")
regexDousMatch = re.compile("^([^\s]*)dou[=/]?s$")
regexGeneralOusMatch = re.compile("^([^\s]*)ou=?s$")
def noun2os(start, core, classification):
    if (start == "bi/os[i^]"):
        start = "bi/os"
    if (start == "a(rmok[o/pos]"):
        start = "a(rmoko/pos"
    elif not(re.search(regexPousMatch, start) == None):
        return nounPousHandler(start, core)
    elif not(re.search(regexOusOuMatch, core) == None) or start == "r(ou=s" or start == "thqalla^dou=s":
        return nounoOsHandler(start, core)
    elif not(re.search(regexDousMatch, start) == None):
        return nounDousHandler(start, core)
    elif not(re.search(regexGeneralOusMatch, start) == None):
        return nounoOsHandler(start, core)
    elif (start == "proorni_qi/ai" or start == "pro/s"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)

    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("(o[/\^\\\\]?s|oi[/]?|w=?s)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'o\(,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun2as(start, core, classification):
    if (start == "paraprosta/ths[sta^]"):
        start = "paraprosta/ths"


    if not(re.search(etaSigmaMatchRegex, start) == None):
        return noun2hs(start, core, utils.ENDING_TYPES.NOUN.SECOND_HS)
    elif start == "ou)/ligc":
        return noun3c(start, core, utils.ENDING_TYPES.NOUN.THIRD_CONSONANT)
    elif start == "fu^ta^lia/":
        return noun1A(start, core, utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN)
    elif (start == "mu^lakri\s" or start == "oi)=sqa" or start == "nh=a"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("(a[_=/\\\\]?s|ai/?)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'(o\(,|oi\(,|h\(,)', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun2hs(start, core, classification):
    if (start == "*maih=tis"):
        start = "maiw/ths"
    elif (start == "e)riou/nios"):
        start = "e)riou/nhs"
    elif (start == "ion"): # TODO
        start = "la^xa^nopwl-h/trhs"
    elif (start == "mesozu/gios"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    elif not(re.search(alphaMatchRegex, start) == None):
        return noun1A(start, core, utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN)
    elif not(re.search(alphaSigmaMatchRegex, start) == None):
        return noun2as(start, core, utils.ENDING_TYPES.NOUN.SECOND_AS)
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("(h[=/\\\\]?s|ai/?)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'(o\(,|oi\(,|h\(,)', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun2on(start, core, classification):
    if (start == "a)e/rsipons"): # note this is caught be set below
        start = "a)e/rsipous"

    if (start == "tri^ta/la_s"):
        return adj3ASHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.MIXED_AS_AINA)
    elif (start == "si/dhros"):
        return noun2os(start, core, utils.ENDING_TYPES.NOUN.SECOND_OS)
    elif (start[-4:] == "pous" or start[-4:] == "poun"):
        return nounPousHandler(start, core)
    elif (start == "*)ama/rios"):
        return threeTermAHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A)
    elif (start == "bra/ket("):
        start = "bra/keton"
    elif (start == "ke/a^r"):
        start = "ke/a^rnon"
    elif (start == "tri^a_ko/st[ia]"):
        start = "tri^a_ko/stia"
    elif (start == "tri^hmi/s[eon]"):
        start = "tri^hmi/seon"
    elif (start == "sarcifa^ge/s"): # TODO
        start = "sarcifa^gon"
    elif (start == "bou/keras" or start[-2:] == "wn"):
        return noun3c(start, core, utils.ENDING_TYPES.NOUN.THIRD_CONSONANT)
    elif (start == "su/ntreis" or start == "do" or start == "phxuale\s" or start == "o)/f" or start == "kordu^ballw=des"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    pos = utils.POS.NOUN
    division = ""
    stemSplitter = re.compile("(o[/\^]?n|a[/]?)$")
    if (start == "ba^traxiou=n"):
        stemSplitter = re.compile("ou=n$")
        classification = utils.ENDING_TYPES.NOUN.SECOND_oON
    endingType = classification

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'to/,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun3c(start, core, classification):
    if start == "ma/nti^s" or start == "sa/ga^ris" or start == "a)ci/wsis" or start == "a)/nesis" or start == "knh=stis" or start == "polu/i+dris" or start == "*ta/nis" or start == "sa/ra_pis" or start == "semi/da_lis":
        return noun3i(start, core, utils.ENDING_TYPES.NOUN.THIRD_IOTA)
    elif start == "eu)dia/koros" or start == "eu)h/trios":
        return twoTermHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION)
    elif start == "u(/steros" or start == "e)pimwmhto/s":
        return threeTermAHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A)
    elif start == "*qrhi+ki/h":
        return threeTermHHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H)
    elif start == "mh/thr":
        return utils.POS.NOUN, "", classification, {"nomsg": "mhthr", "rest": "mhthr"}, {"nomsg": [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.LONG], "rest": [utils.VOWEL_LEN.LONG, utils.VOWEL_LEN.LONG]}, True, ""
    elif start == "a)nh/r":
        return utils.POS.NOUN, "", classification, {"nomsg": "a)nhr", "rest": "a)ndr"}, {"nomsg": [utils.VOWEL_LEN.SHORT, utils.VOWEL_LEN.LONG], "rest": [utils.VOWEL_LEN.SHORT]}, True, ""
    elif start == "limnia/rxhs" or start == "sku^la^de/yhs" or start == "summoria/rxhs":
        return noun2hs(start, core, utils.ENDING_TYPES.NOUN.SECOND_HS)
    elif start == "h)li^ba/ta_s" or start == "e)lasa=s" or start == "o(mwxe/ta_s" or start == "kabita=s" or start == "ba^ruo/pa_s" or start == "la_ke/ta_s" or start == "patikoura=s" or start == "ma^ri^ka=s":
        return noun2as(start, core, utils.ENDING_TYPES.NOUN.SECOND_AS)
    elif start == "po/lemos" or start == "a)/wros" or start == "qu^rwro/s" or start == "daktu/lios" or start == "no/sos" or start == "ka^ru^owto\s" or start == "sugku^nhg-o/s" or start == "a(rmok[o/pos]" or start == "xe/rsos" or start == "da_miergo/s" or start == "ai)/giqos" or start == "parwrai+smo/s" or start == "leptusmo^s" or start == "ai)/louros" or start == "koni/sa^los" or start == "ei(rgmo/s":
        return noun2os(start, core, utils.ENDING_TYPES.NOUN.SECOND_OS)
    elif start == "meshmbri/a":
        return noun1A(start, core, utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN)
    elif start == "mu/kh":
        return noun1H(start, core, utils.ENDING_TYPES.NOUN.FIRST_H)
    elif start == "te/rhn":
        return adjMixedHNHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.MIXED_HN_EINA)
    pos = utils.POS.NOUN
    division = ""
    endingType = classification

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounConsonantStem(starts, core, classification)

    irregular = False
    (restOfCore, link) = fullFindLink(r'(o\(,?|h\(,?|oi\(,?ai\(,?|to/,?)', core) #("", "")
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun3e(start, core, classification):
    print start
    print core
    print "============================="
    pos = "???"
    division = ""
    endingType = ""
    stem = {}
    stemDivision = {}
    irregular = False
    restOfCore = core
    link = findLink(restOfCore)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun3i(start, core, classification):
    if start == "&lt;*&gt;":
        start = "xrh=sis"
    elif start == "w)du^si/h": #TODO
        start = "w)/du^sis"
    elif start == "smi_lei/a": #TODO
        start = "smi?leusis"
    elif start == "ku^rhba^si/a": #TODO
        start = "ku^rh/b-a^sis"
    elif start == "me/la_s":
        return adj3ASHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.MIXED_AS_AINA)
    elif (start == "zeu" or start == "nossa\s" or start == "tufli/nhs" or start == "a)guio/peza"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("(i[=/\^+]?s|i[=/\^]?)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'e/?ws(?:, (?:o\(,|h\(,))?', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun3smf(start, core, classification):
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("hs$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = ("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link


def noun3sn(start, core, classification):
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("os$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'to/[,\.]', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun3digamma(start, core, classification):
    if (start == "xo/es"):
        # we don't actually need this, it is just a link
        return "", "", "", {}, {}, False, ""
    elif (start == "*zeu/s"):
        # since zeus is irregular, no need for stem stuff;
        return utils.POS.NOUN, "", utils.ENDING_TYPES.NOUN.ZEUS, {}, {}, True, ""
    elif (start == "a(lieu/s(laterwritten"):
        start = "a(lieu/s"
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("(eu[/\\\\]?s|ei=?s|h=?s)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'e/ws(?:, o\(,)?', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun3is_f(start, core, classification):
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("i[=/\\\\]?s$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'h\(,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun3ous(start, core, classification):
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("w/$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'ou=s, h\(,', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link


def noun3es(start, core, classification):
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("es$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)


    irregular = False
    (restOfCore, link) = ("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun3i_to(start, core, classification):
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("i/$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)


    irregular = False
    (restOfCore, link) = ("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def noun3hdu(start, core, classification):
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("u/$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'to/[,\.]', core) #("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def nounWS(start, core, classification):
    pos = utils.POS.NOUN
    division = ""
    endingType = classification
    stemSplitter = re.compile("w/?[sn]$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = ("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link


# for verbs that are aorist only
def aoristNoPresentHandler(start, core, classification):
    pos = utils.POS.VERB
    division = ""
    contractVowel = ""

    endingType = classification
    stemSplitter = re.compile("[oh]n$")


    (myStems, stem, stemDivision) = processVerbAorOnly(start, stemSplitter, contractVowel, core, classification)

    irregular = False
    (restOfCore, link) = ("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link



adverbRegex = re.compile("^([^\s]+)w=, Adv\.")
wsNounRegex = re.compile("^([^\s]+)w=?s, w[,\s]")
collapsedLengthSpecRegex = re.compile("^([^\s]+w)\[[^\]]*\]")
toEndingRegex = re.compile("^[^\s]+to$")
removeEndingRegex = re.compile("^[^\s]+(ei=n|ai)$")
paraskeuaRegex = re.compile("paraskeua/zw, fut\.")
aoristNoPresentRegex = re.compile("^[^\s]+on$")
linkRegex = re.compile("(^[^\s]+, ((Ep|prop|Dor|Arc|Ion|intr)\.)?[\s]*(3(sg|pl)\.)?[\s]*(((redupl|imper)\.[\s]*)?(aor|pf|pres|impf)\.)?([\s]*[1-3])?([\s]*(subj|inf|part|imper)\.( (Act|Med|Pass)\.)?)? of )|(^[^\s]+w=n, n\. [^\s]+$)")
def verbThematic(start, core, classification):
    if not(re.search(adverbRegex, core) == None) or (start == "dasto/s"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    elif (start == "h(mie/ktewn" or start == "peri/news" or start == "fi^ba/lews" or start == "i(ppo/fews" or start == "ai)goke/rws" or start == "ga/lows" or start == "*)/aqws" or start == "pri/wn" or start == "zeuci/lews" or start == "ai)goke/rws"
          or start == "fi^ba/lews" or start == "peri/news" or start == "h(mie/ktewn"):
        return nounWS(start, core, utils.ENDING_TYPES.NOUN.THIRD_WS_S)
    elif (start == "a)cio/xrews" or start == "prwto/news"):
        return twoTermAHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_A_CONTRACT)
    elif (start == "ka/tw" or start == "e)copi/sw" or start == "e)/cw" or start == "ei)/sw" or start == "pro/sw" or start == "o)pi/sw" or start == "prote/rw"):
        return placeholder(core, start, utils.ENDING_TYPES.ADVERB)
    elif (start == "pw" or start == "a)/mfw" or start == "e)/sw"):
        return placeholder(core, start, utils.ENDING_TYPES.OTHER)
    elif (start == "du/o"):
        pos = utils.POS.ADJECTIVE
        division = ""
        classification = utils.ENDING_TYPES.ADJECTIVE.DUO
        endingType = classification
        stemSplitter = re.compile("o")

        starts = getMultipleStarts(start, core, classification)

        (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

        irregular = False
        (restOfCore, link) = ("", "")
        if (re.search(stemSplitter, start) == None):
            printMatchFail(start, core, classification)
        if VERY_VERBOSE:
            printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
        return pos, division, endingType, stem, stemDivision, irregular, link
    elif (start == "*kw=s" or start == "*lukiourgoi/" or start == "ka/lws" or start == "*di^o/nucos" or not(re.search(wsNounRegex, core) == None)):
        return noun2os(start, core, utils.ENDING_TYPES.NOUN.SECOND_OS)
    elif (start == "r(u/sion"):
        return noun2on(start, core, utils.ENDING_TYPES.NOUN.SECOND_ON)
    elif (start == "polia=xos" or start == "phro/s" or start == "da^ero/s"):
        return threeTermHHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H)
    elif (start == "*mi/das" or start == "*loci/as" or start == "stigma^ti/as" or start == "*)adri/as" or start == "*pu_qa^go/ras" or start == "nea_ni/as" or start == "qhludri/as"):
        return noun2as(start, core, utils.ENDING_TYPES.NOUN.SECOND_AS)
    elif (start == "mu/khs"):
        return noun3c(start, core, utils.ENDING_TYPES.NOUN.THIRD_CONSONANT)
    elif (start == "o)puihth/s" or start == "*qa^lh=s" or start == "a)kra_topo/ths" or start == "moirhge/ths" or start == "*)atrei/dhs" or start == "katarra/kths" or start == "h)erodi/nhs" or start == "moira_ge/ths" or start == "poli^h/ths" or start == "e)ribru/xhs" or start == "oi)kih/ths" or start == "u(mna^go/rhs" or start == "dra_pe/ths" or start == "e)ribreme/ths" or start == "*si^mwni/dhs" or start == "pu^ri^bh/ths"):
        return noun2hs(start, core, utils.ENDING_TYPES.NOUN.SECOND_HS)
    elif (start == "e)pikexodw/s"):
        return adj3WSHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.MIXED_WS_UIA_OS)
    elif (start == "a)i+/caske" or start == "e)/cesti" or start == "prosei=pon" or start == "*ka/r" or start == "e)pegro/mhn" or start == "i)/deskon" or start == "e)/ssu^o" or start == "a)me/lei" or start == "qwu=ma" or start == "suno/xwka" or start == "pettei/a" or start == "mua^lo/s" or start == "a)gostai/" or start == "ballhna/^de" or start == "e)/coi"
          or start == "eu)quktai/na" or start == "dierw=" or start == "lei/n[" or start == "e)skeqh=n" or start == "a)mfi^a^xui=a" or start == "xolemesi/a" or start == "a)nakwxh/" or start == "katoptiko\s" or start == "ou(/tws" or start == "a)nassei/aske"
          or start == "h)/nsei" or start == "kh=en" or start == "e(/sthka" or start == " *ka/r" or start == "*r" or start == "kateirga^qo/mhn" or start == "e(ce/men" or start == "kekmhw/s" or start == "e)/nace" or start == "au)tou=" or start == "me/n"
          or start == "ai)e/tion" or start == "*o)/kwxa" or start == "kla|cw=" or start == "fa^noi/hn" or start == "e)cwxei/rion" or start == "ka/riso" or start == "bw/sas" or start == "qe/eion" or start == "katapepthui=a" or start == "r(w="
          or start == "probi^ba/s" or start == "sfa=s" or start == "a)pessu/meqa" or start == "leikna/rion" or start == "u(peregrh/gora" or start == "au)totroph/sas" or start == "pw/pote" or start == "gna/falon" or start == "e)nika/bbale" or start == "e)/mba_"
          or start == "tarro/s" or start == "a)mpi/" or start == "kaqicw=" or start == "kra=" or start == "li/gce" or start == "i)auoi=" or start == "o)/lwla" or start == "sth/gwn" or start == "gdou=pos" or start == "r(i?gion"
          or start == "peto/ntessi" or start == "me/le" or start == "e)/ktu^pe" or start == "i)sxu_ristikw=s" or start == "prosapei=pon" or start == "o)pi^sambw/" or start == "a)/strabda" or start == "fa/anqen" or start == "i)ou/" or start == "e)cwxei/rion"
          or start == "e)pegro/mhn" or start == "a)/ge" or start == "ka^qh=rai" or start == "mh\\" or start == "h)ra^" or start == "lhqa/nemos" or start == "qew=" or start == "metei=pon" or start == "zh=" or start == "tri/yorxis" or start == "ou)de/"
          or start == "ou)de/" or start == "ou)/ti" or start == " i)sxu_ristikw=s" or start == "prosegrh/gora" or start == "leipandri/a" or start == "o(rma_qw=" or start == "prosku/sas" or start == "sunei=don" or start == "gw=" or start == "e)capei=don"
          or start == "e)pe/npoi" or start == "r(e/gxos" or start == "li^qa" or start == "propi=n" or start == "e)s" or start == "deu=ro" or start == "fa/nai" or start == "blh/menos" or start == "qu/rda" or start == "ti/os" or start == "pagkro/tws"
          or start == "dw=" or not(re.search(toEndingRegex, start) == None)
          or not(re.search(removeEndingRegex, start) == None) or not(re.search(linkRegex, core) == None)):
        if not(start == "a)lo/w" or start == "e)pi/sxw"):
            return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    elif (start == "katadeh/s(A)"):
        return adj3HSHandler("katadeh/s", core, utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_HS)
    elif (start == "kle/os" or start == "o)/felos"):
        pos = utils.POS.NOUN
        division = ""
        classification = utils.ENDING_TYPES.NOUN.THIRD_CONSONANT
        endingType = classification
        stemSplitter = re.compile("os")

        starts = getMultipleStarts(start, core, classification)
        def newStemFunc(s):
            return s + "os"

        def newLensFunc(ls):
            ls.append(utils.VOWEL_LEN.SHORT)
            return ls
        (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, newStemFunc, defaultStemFunc, newLensFunc, defaultLensFunc)

        irregular = False
        (restOfCore, link) = ("", "")
        if (re.search(stemSplitter, start) == None):
            printMatchFail(start, core, classification)
        if VERY_VERBOSE:
            printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
        return pos, division, endingType, stem, stemDivision, irregular, link
    elif (start == "da/i+s"):
        pos = utils.POS.NOUN
        division = ""
        classification = utils.ENDING_TYPES.NOUN.THIRD_CONSONANT
        endingType = classification
        stemSplitter = re.compile("i\+s")

        starts = getMultipleStarts(start, core, classification)
        (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

        irregular = False
        (restOfCore, link) = ("", "")
        if (re.search(stemSplitter, start) == None):
            printMatchFail(start, core, classification)
        if VERY_VERBOSE:
            printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
        return pos, division, endingType, stem, stemDivision, irregular, link
    elif (start == "*sapfw/" or start == "*gellw/"):
        pos = utils.POS.NOUN
        division = ""
        classification = utils.ENDING_TYPES.NOUN.THIRD_CONSONANT
        endingType = classification
        stemSplitter = re.compile("$")

        starts = getMultipleStarts(start, core, classification)
        def newStemFunc(s):
            return s[:-1]

        def newLensFunc(ls):
            return ls[:-1]
        (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, newStemFunc, defaultLensFunc, newLensFunc)

        irregular = False
        (restOfCore, link) = ("", "")
        if (re.search(stemSplitter, start) == None):
            printMatchFail(start, core, classification)
        if VERY_VERBOSE:
            printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
        return pos, division, endingType, stem, stemDivision, irregular, link
    elif (start == "*)apo/llwn"):
        pos = utils.POS.NOUN
        division = ""
        classification = utils.ENDING_TYPES.NOUN.THIRD_CONSONANT
        endingType = classification
        stemSplitter = re.compile("$")

        starts = getMultipleStarts(start, core, classification)

        (myStems, stem, stemDivision) = doStemWorkNounSimple(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc)

        irregular = False
        (restOfCore, link) = ("", "")
        if (re.search(stemSplitter, start) == None):
            printMatchFail(start, core, classification)
        if VERY_VERBOSE:
            printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
        return pos, division, endingType, stem, stemDivision, irregular, link
    elif (not(re.search(collapsedLengthSpecRegex, start) == None)):
        match = re.search(collapsedLengthSpecRegex, start)
        start = start[match.start(1):match.end(1)]
    elif (start == "a(li/zw(A)"):
        start = "a(li/zw"
    elif (start == "e)piqeia/zw)" or start == "e(ka^tostobabra/zw)"):
        start = start[:-1]
    elif (not(re.search(paraskeuaRegex, core) == None)):
        start = "paraskeua/zw"
    elif (start == "metame/lei"):
        start = "metame/lw"
    elif not(re.search(aoristNoPresentRegex, start) == None):
        return aoristNoPresentHandler(start, core, classification)

    pos = utils.POS.VERB
    division = ""
    contractVowel = ""

    if (start[-2:] == "aw" or start[-3:] == "a/w"):
        contractVowel = "a"
        classification = utils.ENDING_TYPES.VERB.A_CONTRACT
    elif (start[-2:] == "ew" or start[-3:] == "e/w"):
        contractVowel = "e"
        classification = utils.ENDING_TYPES.VERB.E_CONTRACT
    elif (start[-2:] == "ow" or start[-3:] == "o/w"):
        contractVowel = "o"
        classification = utils.ENDING_TYPES.VERB.O_CONTRACT
    else:
        classification = utils.ENDING_TYPES.VERB.THEMATIC
    endingType = classification
    stemSplitter = re.compile("(a|e|o)?/?w[=/\\\\]?$")


    (myStems, stem, stemDivision) = processVerbStandard(start, stemSplitter, contractVowel, core, classification)

    irregular = False
    (restOfCore, link) = ("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def verbDeponent(start, core, classification):
    pos = utils.POS.VERB
    division = ""
    contractVowel = ""
    if start == "u(peido/mhn":
        endingType = utils.ENDING_TYPES.VERB.DEPONENT_OMAI
        stem = {
            "aor": {
                "mid": {"n": "u(peid", "y": "u(peid"},
            }
        }
        stemDivision= {
            "aor": {
                "mid": {"n": ["?", "l"], "y": ["?", "l"]},
            }
        }
        irregular = False
        (restOfCore, link) = ("", "")
        if VERY_VERBOSE:
            printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
        return pos, division, endingType, stem, stemDivision, irregular, link
    if start[-1] == "_":
        start = start[:-1]
    if start == "b":
        start = "e)ru/omai"


    if (start[-4:] == "omai" or start[-5:] == "o/mai"):
        classification = utils.ENDING_TYPES.VERB.DEPONENT_OMAI
    elif (start[-5:] == "eimai" or start[-6:] == "ei=mai"):
        contractVowel = "ei"
        classification = utils.ENDING_TYPES.VERB.DEPONENT_EIMAI
    elif (start[-5:] == "a^mai"):
        contractVowel = "a"
        classification = utils.ENDING_TYPES.VERB.DEPONENT_AsMAI
    elif (start[-4:] == "amai"):
        contractVowel = "a"
        classification = utils.ENDING_TYPES.VERB.DEPONENT_A_MAI
    elif (start[-4:] == "hmai" or start[-5:] == "h=mai" or start == "h(=mai"):
        contractVowel = "e"
        classification = utils.ENDING_TYPES.VERB.DEPONENT_HMAI
    elif (start[-4:] == "emai"):
        classification = utils.ENDING_TYPES.VERB.DEPONENT_EMAI
    elif (start[-5:] == "w=mai"):
        classification = utils.ENDING_TYPES.VERB.DEPONENT_WMAI
        contractVowel = "a"
    else:
        classification = utils.ENDING_TYPES.VERB.DEPONENT
    endingType = classification
    stemSplitter = re.compile("(o/?|ei=?|a\^|a|h\(?=?|e|w=)mai$")


    (myStems, stem, stemDivision) = processVerbStandard(start, stemSplitter, contractVowel, core, classification)

    irregular = False
    (restOfCore, link) = ("", "") #TODO
    if (re.search(stemSplitter, start) == None):
        #printMatchFail(start, core, classification)
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def verbUmi(start, core, classification):
    if start == "paralou=mai" or start == "steu=mai" or start == "la_seu=mai" or start == "shmeioskopou=mai" or start == "sunepiskopou=mai":
        return verbDeponent(start, core, utils.ENDING_TYPES.VERB.DEPONENT)
    elif (start == "c" or start == "e(/sqhn" or start == "a)/rhai" or start == "sune/rrwga" or start == "plegnu/menos"
          or start == "katehgw/s" or start == "ei(me/nos" or start == "ei(=tai" or start == "e(/sso" or start == "e(/ssa"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    pos = utils.POS.VERB
    division = ""
    contractVowel = ""
    endingType = classification
    stemSplitter = re.compile("u[_\^]?m(ai|i)$")


    (myStems, stem, stemDivision) = processVerbUmi(start, stemSplitter, contractVowel, core, classification)

    irregular = False
    (restOfCore, link) = ("", "") #TODO
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link


eimiRegex = re.compile("^([^\s]+)eimi$")
isthmiRegex = re.compile("^([^\s]*)i\+?\)?/sthmi$")
didwmiRegex = re.compile("^([^\s]*)di/dwmi$")
ihmiRegex = re.compile("^([^\s]*)i\+?\(?/hmi$")
tiqhmiRegex = re.compile("^([^\s]*)ti/qhmi$")
fhmiRegex = re.compile("^([^\s]*)fhmi/?$")
hmiRegex = re.compile("^([^\s]*)h\)?mi/?$")
wmiRegex = re.compile("^([^\s]+)wmi$")
def verbAthematic(start, core, classification):
    if not(re.search(aoristNoPresentRegex, start) == None):
        return aoristNoPresentHandler(start, core, classification)
    elif (start[-5:] == "menai" or start == "pa/resan" or  start == "su/ni^san" or start == "e(/nto" or start == "e(/sta^ka" or start == "sth/menai" or start == "pa^rei/s" or start == "kati/men" or start == "e)ce/men" or start == "e)skixre/men" or start == "meteisa/menos" or start == "e)/neimen" or start == "ei(=sqai" or start == "pare/mmenai" or start == "e)ci/menai" or start == "e(/sqai"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    pos = utils.POS.VERB
    division = ""
    contractVowel = ""

    if not(re.search(eimiRegex, start) == None):
        classification = utils.ENDING_TYPES.VERB.EIMI
        irregular = True
        (myStems, stem, stemDivision) = processVerbEimi(start, eimiRegex, contractVowel, core, classification)
    elif not(re.search(isthmiRegex, start) == None):
        classification = utils.ENDING_TYPES.VERB.ISTHMI
        irregular = False
        (myStems, stem, stemDivision) = processVerbIsthmi(start, isthmiRegex, contractVowel, core, classification)
    elif not(re.search(didwmiRegex, start) == None):
        classification = utils.ENDING_TYPES.VERB.DIDWMI
        irregular = False
        (myStems, stem, stemDivision) = processVerbDidwmi(start, didwmiRegex, contractVowel, core, classification)
    elif not(re.search(ihmiRegex, start) == None):
        classification = utils.ENDING_TYPES.VERB.IHMI
        irregular = False
        (myStems, stem, stemDivision) = processVerbIhmi(start, ihmiRegex, contractVowel, core, classification)
    elif not(re.search(tiqhmiRegex, start) == None):
        classification = utils.ENDING_TYPES.VERB.TIQHMI
        irregular = False
        (myStems, stem, stemDivision) = processVerbTiqhmi(start, tiqhmiRegex, contractVowel, core, classification)
    elif not(re.search(fhmiRegex, start) == None):
        classification = utils.ENDING_TYPES.VERB.FHMI
        irregular = False
        (myStems, stem, stemDivision) = processVerbFhmi(start, fhmiRegex, contractVowel, core, classification)
    elif not(re.search(hmiRegex, start) == None):
        classification = utils.ENDING_TYPES.VERB.TIQHMI
        irregular = False
        (myStems, stem, stemDivision) = processVerbHmi(start, hmiRegex, contractVowel, core, classification)
    elif not(re.search(wmiRegex, start) == None):
        classification = utils.ENDING_TYPES.VERB.DIDWMI
        irregular = False
        (myStems, stem, stemDivision) = processVerbWmi(start, wmiRegex, contractVowel, core, classification)
    else:
        irregular = False
        printMatchFail(start, core, classification)
        stemSplitter = re.compile("nevergonnamatch$")


        (myStems, stem, stemDivision) = processVerbUmi(start, stemSplitter, contractVowel, core, classification)

    endingType = classification
    (restOfCore, link) = ("", "") #TODO
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def verbInfinitive(start, core, classification):
    if start == "e)kei=nos":
        return threeTermHHandler(start, core, utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H)
    elif (start == "deinauch=sai" or start == "mazeino\\s" or start == "te/reinos" or start == "tei=nde" or start == "e)da^feino/s" or start == "dei=nos" or start == "a(lieinh\\"):
        return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    elif start == "la/ppein)":
        start = "la/ppein"
    elif start == "a)natlh=nai":
        return aoristNoPresentHandler("a)ne/tlhn", core, utils.ENDING_TYPES.VERB.THEMATIC)

    pos = utils.POS.VERB
    division = ""
    contractVowel = ""

    endingType = classification
    stemSplitter = re.compile("(ei=?n)$")


    (myStems, stem, stemDivision) = processVerbInfinitive(start, stemSplitter, contractVowel, core, classification)

    irregular = False
    (restOfCore, link) = ("", "")
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
        #return placeholder(start, core, utils.ENDING_TYPES.OTHER)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def verbalAdjective(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("(on|a)$")

    starts = getMultipleStarts(start, core, classification)

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'on,', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link

def pplWn(start, core, classification):
    pos = utils.POS.ADJECTIVE
    division = ""
    endingType = classification
    stemSplitter = re.compile("wn$")

    starts = getMultipleStarts(start, core, classification)

    def femStemFunc(s):
        return s + "ous"
    def femLensFunc(ls):
        ls.append(utils.VOWEL_LEN.LONG)
        return ls

    (myStems, stem, stemDivision) = doStemWorkAdj(starts, core, classification, stemSplitter, defaultStemFunc, defaultStemFunc, defaultStemFunc, femStemFunc, defaultStemFunc, defaultLensFunc, defaultLensFunc, defaultLensFunc, femLensFunc, defaultLensFunc)

    irregular = False
    (restOfCore, link) = fullFindLink(r'ousa', core)
    if (re.search(stemSplitter, start) == None):
        printMatchFail(start, core, classification)
    if VERY_VERBOSE:
        printAllHandlerStuff(start, core, myStems, stem, stemDivision, restOfCore, link)
    return pos, division, endingType, stem, stemDivision, irregular, link


# list of step two functions to call
step2Functions = {
    utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION: twoTermHandler,
    utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_A_CONTRACT: twoTermAHandler,
    utils.ENDING_TYPES.ADJECTIVE.TWO_TERMINATION_O_CONTRACT: twoTermOHandler,
    utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A: threeTermAHandler,
    utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H: threeTermHHandler,
    utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_A_E_CONTRACT: threeTermeAHandler,
    utils.ENDING_TYPES.ADJECTIVE.THREE_TERMINATION_H_E_CONTRACT: threeTermeHHandler,
    utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_HS: adj3HSHandler,
    utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_WN: adj3WNHandler,
    utils.ENDING_TYPES.ADJECTIVE.THIRD_DECLENSION_US: adj3USHandler,
    utils.ENDING_TYPES.ADJECTIVE.POUS_FOOT: adj3PousHandler,
    utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA: adj3EisHandler,
    utils.ENDING_TYPES.ADJECTIVE.MIXED_EIS_ESSA_O_CONTRACT: adj3oEisHandler,
    utils.ENDING_TYPES.ADJECTIVE.MIXED_AS_AINA: adj3ASHandler,
    utils.ENDING_TYPES.ADJECTIVE.MIXED_WS_UIA_OS: adj3WSHandler,
    utils.ENDING_TYPES.ADJECTIVE.IS_I: adjIS_IHandler,
    utils.ENDING_TYPES.ADJECTIVE.PAS: adjPasHandler,
    utils.ENDING_TYPES.ADJECTIVE.AUTOU_COMPOUNDS: adjAutouHandler,
    utils.ENDING_TYPES.ADJECTIVE.OSDE_H: adjOsdeHHandler,
    utils.ENDING_TYPES.ADJECTIVE.OSDE_A: adjOsdeAHandler,
    utils.ENDING_TYPES.ADJECTIVE.EIS: adjEisHandler,
    utils.ENDING_TYPES.ADJECTIVE.TIS: adjTisHandler,
    utils.ENDING_TYPES.ADJECTIVE.MEGAS: adjMegasHandler,
    utils.ENDING_TYPES.ADJECTIVE.POLUS: adjPolusHandler,
    utils.ENDING_TYPES.NOUN.FIRST_A_UNKNOWN: noun1A,
    utils.ENDING_TYPES.NOUN.FIRST_A_LONG: placeholder,
    utils.ENDING_TYPES.NOUN.FIRST_A_SHORT: placeholder,
    utils.ENDING_TYPES.NOUN.FIRST_H: noun1H,
    utils.ENDING_TYPES.NOUN.SECOND_OS: noun2os,
    utils.ENDING_TYPES.NOUN.SECOND_HS: noun2hs,
    utils.ENDING_TYPES.NOUN.SECOND_AS: noun2as,
    utils.ENDING_TYPES.NOUN.SECOND_ON: noun2on,
    utils.ENDING_TYPES.NOUN.THIRD_CONSONANT: noun3c,
    utils.ENDING_TYPES.NOUN.THIRD_EPSILON: noun3e,
    utils.ENDING_TYPES.NOUN.THIRD_IOTA: noun3i,
    utils.ENDING_TYPES.NOUN.THIRD_SIGMA_MF: noun3smf,
    utils.ENDING_TYPES.NOUN.THIRD_SIGMA_N: noun3sn,
    utils.ENDING_TYPES.NOUN.THIRD_DIGAMMA: noun3digamma,
    utils.ENDING_TYPES.NOUN.THIRD_IS_FEM: noun3is_f,
    utils.ENDING_TYPES.NOUN.THIRD_OUS: noun3ous,
    utils.ENDING_TYPES.NOUN.THIRD_ES_OUS_TO: noun3es,
    utils.ENDING_TYPES.NOUN.THIRD_I_TO: noun3i_to,
    utils.ENDING_TYPES.NOUN.THIRD_HDU_TYPE: noun3hdu,
    utils.ENDING_TYPES.VERB.THEMATIC: verbThematic,
    utils.ENDING_TYPES.VERB.A_CONTRACT: placeholder,
    utils.ENDING_TYPES.VERB.E_CONTRACT: placeholder,
    utils.ENDING_TYPES.VERB.O_CONTRACT: placeholder,
    utils.ENDING_TYPES.VERB.DEPONENT: verbDeponent,
    utils.ENDING_TYPES.VERB.A_CONTRACT_DEPONENT: placeholder,
    utils.ENDING_TYPES.VERB.E_CONTRACT_DEPONENT: placeholder,
    utils.ENDING_TYPES.VERB.O_CONTRACT_DEPONENT: placeholder,
    utils.ENDING_TYPES.VERB.UMI: verbUmi,
    utils.ENDING_TYPES.VERB.ATHEMATIC: verbAthematic,
    utils.ENDING_TYPES.VERB.INFINITIVE: verbInfinitive,
    utils.ENDING_TYPES.VERBAL_ADJECTIVE: verbalAdjective,
    utils.ENDING_TYPES.PARTICIPLE.WN: pplWn,
    "rest": placeholder
}


# process raw XML and intermediate stuff into a full dictionary (step 2)
def processDict2(dictName):
    inName = utils.getProcessedDictionaryFn(dictName+"_intermediate_1")
    intermediates = utils.getContent(inName, True)["dict"]

    output = {"name": dictName}
    outputDict = {}

    count = -1
    # 6 is for rest:
    currentIndex = 58 #(57 total)
    singleTypeOnly = False#True#


    i = 0
    maxIterations = 1
    useMax = False#True#
    printInterval = 5000
    printAtIntervals = True
    totalLen = 0

    # count the number of entries we'll be looking at
    for key in intermediates.keys():
        count += 1

        if singleTypeOnly and not(count == currentIndex):
            continue

        entries = intermediates[key]

        totalLen += len(entries)

    # reset count
    count = -1

    for key in intermediates.keys():

        count += 1

        myFun = step2Functions[key]

        if singleTypeOnly and not(count == currentIndex):
            continue


        if singleTypeOnly:
            print "TYPE:"
            print key
            print "Function: " + myFun.__name__
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

        entries = intermediates[key]


        for key2 in entries:
            if useMax:
                if (i >= maxIterations):
                    break
            i += 1
            if (printAtIntervals and (i % printInterval == 0)):
                print str(i) + "/" + str(totalLen) + " (" + str(round((100.0*i)/totalLen, 1)) + "%)"

            data = entries[key2]

            entryXML = data["entryXML"]
            core = data["core"]
            start = data["start"]
            classification = data["classification"]

            # get properly formatted string
            (xml, parsed) = getStringSafe(entryXML)
            if not(parsed):
                continue


            if (dictName == utils.DICTIONARY_NAMES.LSJ):
                div = xml.find("text").find("body").find("div0")
                entry = div.find("entryFree")

                key = entry.attrib["key"]
                sortKey = entry.attrib["id"]
                betacode = entry.attrib["key"]
                letter = div.attrib["n"]
                #senses = parseSenses(entry.findall("sense"))
                (pos, division, endingType, stem, stemDivision, irregular, link) = myFun(start, core, classification)

            val = {
            "letter": letter,
            #"division": division,
            #"senses": senses,
            "key": key,
            "betacode": betacode,
            "sortKey": sortKey,
            "pos": pos,
            "endingType": endingType,
            "stem": stem,
            "stemDivision": stemDivision,
            "irregular": irregular,
            "link": link
            }
            outputDict[key] = val

    output["dict"] = outputDict;

    outFileName = utils.getProcessedDictionaryFn(dictName)
    utils.safeWrite(outFileName, json.dumps(output, sort_keys=True))
