# -*- coding: utf-8 -*-
# Code for getting the various results

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_pdf import PdfPages

from sklearn import decomposition
from sklearn import datasets
from sklearn import preprocessing
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import ShuffleSplit
from sklearn.model_selection import KFold
from sklearn.feature_selection import SelectFromModel
from sklearn.linear_model import LassoCV
from sklearn import svm
from sklearn import linear_model
from sklearn import neighbors
from sklearn import ensemble


#from utils import getFeatureMatrixFn, getFinalResultsOutputDir
import utils
import json
import copy

# empty class for creating constants
class Constant:
    pass

class Dataset:
    def __init__(self, data, target):
        self.data = data
        self.target = target


# a variety of data sets
DATA_SETS = Constant()

# example datasets from scikitlearn
DATA_SETS.DIGITS = "digits" # digits
DATA_SETS.FLOWERS = "flowers" # flowers (iris)
DATA_SETS.FLOWERS_BI = "flowers_2_types" # flowers with only two types
DATA_SETS.ILIAD_ODYSSEY = "iliad_odyssey_only" # only the iliad and the odyssey
DATA_SETS.DIONYSIACA_SPLIT = "dionysiaca_split" # split the dionysiaca into the first and second halves
DATA_SETS.AUTHORS_SPLIT = "authors_split" # look at Cyngetica vs Halieutica
DATA_SETS.ILIAD_ODYSSEY_NO_TARGET = "iliad_odyssey_only_no_target" # the iliad and odyssey with no information about which book is which type.
DATA_SETS.BOOKS_ONLY = "books_only" # only look at the individual books
DATA_SETS.ALL_OVERALLS = "all_overalls" # all the overall texts, no books
DATA_SETS.ALL_OVERALLS_SUB_BOOKS = "all_overalls_test_books" # train on overall books, view data with text books
DATA_SETS.CLOSER_ONLY = "closer_only" # remove dionysiaca, abduciton of helen, hymn 1,
DATA_SETS.CLOSER_ONLY_HERMES_LOOK = "closer_only_hymns" # remove dionysiaca, abduction of helen, hymn 1, plus only show the sub-books of the hymns
DATA_SETS.CLOSER_ONLY_HERMES_LOOK_DIONYSIACA_AS_TEST = "closer_only_hymns_dio_as_test"# look at dionysiaca, moschus, bion, but don't train on it
DATA_SETS.CLOSER_ONLY_HERMES_LOOK_DIONYSIACA_AS_TEST_1 = "closer_only_hymns_dio_as_test_1"# look at dionysiaca, moschus, bion, abduction of helen, taking of ilios but don't train on it


# these train on only overall
DATA_SETS.HOMER_HESIOD_AND_THE_HYMNS = "homer_hesiod_hymns"
DATA_SETS.HOMER_TEST_HESIOD_AND_THE_HYMNS = "homer_test_hesiod_hymns"
DATA_SETS.HOMER_AND_THE_HYMNS = "homer_hymns"
# these train on books as well
DATA_SETS.HOMER_HESIOD_AND_THE_HYMNS_ALL = "homer_hesiod_hymns_all"
DATA_SETS.HOMER_TEST_HESIOD_AND_THE_HYMNS_ALL = "homer_test_hesiod_hymns_all"
DATA_SETS.HOMER_AND_THE_HYMNS_ALL = "homer_hymns_all"

# a variety of subdata sets; for now we only use 3 and 6

# remove some unneeded texts, train on all texts and books, but don't label the books
DATA_SETS.CLASSIFY_3 = "classify_3"
# remove some unneeded texts, train on all texts and books, label the books
DATA_SETS.CLASSIFY_6 = "classify_6"

DATA_SETS.CLASSIFY_1 = "classify_1"
DATA_SETS.CLASSIFY_2 = "classify_2"
DATA_SETS.CLASSIFY_4 = "classify_4"
DATA_SETS.CLASSIFY_5 = "classify_5"


# get the data for a given name
# see explanations of what they are above.
def getData(dataName):
    def generalGrab(func):
        data = []
        target = []
        names = []
        testData = []
        testTarget = []
        testNames = []
        fName = utils.getFeatureMatrixFn()
        matrixStorage = utils.getContent(fName, True)
        oldNames = matrixStorage["rowNames"]
        matrixData = matrixStorage["matrix"]
        for i in range(len(oldNames)):
            split = oldNames[i].split(": ")
            skip, isTest, includeName, targetVal = func(oldNames[i], split[0], split[1])
            if skip:
                continue

            if isTest:
                testData.append(matrixData[i])
                testTarget.append(targetVal)
                if (includeName):
                    myName = oldNames[i]
                else:
                    myName = ""
                testNames.append(myName)
            else:
                data.append(matrixData[i])
                target.append(targetVal)
                if (includeName):
                    myName = oldNames[i]
                else:
                    myName = ""
                names.append(myName)

        npData = np.array(data)
        npTarget = np.array(target)
        res = Dataset(npData, npTarget)
        npData = np.array(testData)
        npTarget = np.array(testTarget)
        testRes = Dataset(npData, npTarget)
        return res, names, testRes, testNames

    if (dataName == DATA_SETS.DIGITS):
        # data, which is the features
        # target, which is the target (e.g. the class of the source)
        digits = datasets.load_digits()
        names = []
        for i in range(len(digits.data)):
            names.append("Digit " + str(i))
        testData = []
        testTarget = []
        testNames = []
        npData = np.array(testData)
        npTarget = np.array(testTarget)
        testRes = Dataset(npData, npTarget)
        return digits, names, testRes, testNames
    if (dataName == DATA_SETS.FLOWERS):
        # data, which is the features
        # target, which is the target (e.g. the class of the source)
        iris = datasets.load_iris()
        names = []
        for i in range(len(iris.data)):
            names.append("Flower " + str(i))
        testData = []
        testTarget = []
        testNames = []
        npData = np.array(testData)
        npTarget = np.array(testTarget)
        testRes = Dataset(npData, npTarget)
        return iris, names, testRes, testNames
    elif (dataName == DATA_SETS.FLOWERS_BI):
        # data, which is the features
        # target, which is the target (e.g. the class of the source)
        iris = datasets.load_iris()
        t = iris.target
        d = iris.data
        data = []
        target = []
        names = []
        testData = []
        testTarget = []
        testNames = []
        for i in range(len(t)):
            if (t[i] != 2):
                names.append("Flower " + str(i))
                data.append(d[i])
                target.append(t[i])

        npData = np.array(data)
        npTarget = np.array(target)
        res = Dataset(npData, npTarget)
        npData = np.array(testData)
        npTarget = np.array(testTarget)
        testRes = Dataset(npData, npTarget)
        return res, names, testRes, testNames
    elif (dataName == DATA_SETS.ILIAD_ODYSSEY):
        def func(name, textName, subName):
            # skip
            if (subName == "Overall") or (textName != "Iliad" and textName != "Odyssey"):
                return True, False, False, 0
            # non test data
            else:
                isTestData = False
                showNames = True
                if (textName == "Iliad"):
                    targetVal = 0
                else: #odyssey
                    targetVal = 1
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.DIONYSIACA_SPLIT):
        def func(name, textName, subName):
            # skip
            if (subName == "Overall") or (textName != "Dionysiaca"):
                return True, False, False, 0
            # non test data
            else:
                isTestData = False
                showNames = True
                if (int(subName.split("Book ")[1]) <= 24):
                    targetVal = 0
                else: #second half
                    targetVal = 1
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.AUTHORS_SPLIT):
        def func(name, textName, subName):
            # skip
            if (subName == "Overall") or (textName != "Dionysiaca" and textName != "Fall of Troy"):
                return True, False, False, 0
            # non test data
            else:
                isTestData = False
                showNames = True
                if (textName == "Dionysiaca"):
                    targetVal = 0
                else: #fall of troy
                    targetVal = 1
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.ILIAD_ODYSSEY_NO_TARGET):
        def func(name, textName, subName):
            # skip
            if (subName == "Overall") or (textName != "Iliad" and textName != "Odyssey"):
                return True, False, False, 0
            # non test data
            else:
                isTestData = False
                showNames = True
                targetVal = 0
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.BOOKS_ONLY):
        def func(name, textName, subName):
            # skip
            if (subName == "Overall"):
                return True, False, False, 0
            # non test data
            else:
                isTestData = False
                showNames = True
                targetVal = 0
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.ALL_OVERALLS):
        def func(name, textName, subName):
            testStr = "Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (subName != "Overall"):
                return True, False, False, 0
            # non test data
            else:
                isTestData = False
                showNames = True
                targetVal = 2
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.ALL_OVERALLS_SUB_BOOKS):
        def func(name, textName, subName):
            testStr = "Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1):
                return True, False, False, 0

            # test data
            if (subName != "Overall"):
                isTestData = True
                showNames = True#False
                if textName == "Iliad":
                    targetVal = 0
                    return False, isTestData, showNames, targetVal
                elif textName == "Odyssey":
                    targetVal = 1
                    return False, isTestData, showNames, targetVal
                elif textName == "HymnsLong":
                    targetVal = 2
                    return False, isTestData, showNames, targetVal
                elif textName == "Dionysiaca":
                    targetVal = 7
                    return False, isTestData, showNames, targetVal
                elif textName == "Argonautica":
                    targetVal = 5
                    return False, isTestData, showNames, targetVal
                else:
                    targetVal = 8
                    return False, isTestData, showNames, targetVal
            # non test data
            else:
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    targetVal = 2
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    targetVal = 3
                elif textName == "CallimachusHymns":
                    targetVal = 5
                elif textName == "Idylls_Eidulia":
                    targetVal = 5
                elif textName == "Cynegetica":
                    targetVal = 8 # oppian was 1st/2nd century ad greco-roman
                elif textName == "Halieutica":
                    targetVal = 8 # oppian was 1st/2nd century ad greco-roman
                elif textName == "Fall of Troy":
                    targetVal = 8 # Quintus was 4th? century ad greco-roman
                elif textName == "The Taking of Ilios":
                    targetVal = 8 # Roman
                elif textName == "Dionysiaca":
                    targetVal = 7
                elif textName == "Argonautica":
                    targetVal = 5 # alexandrian, sure
                elif textName == "Phaenomena":
                    targetVal = 8
                elif textName == "Idylls":
                    targetVal = 5
                elif textName == "Works of Bion":
                    targetVal = 8 # a little after Alexandria, 1/2 bc
                elif textName == "Works of Moschus":
                    targetVal = 8 # a little after Alexandria, 2 bc
                isTestData = False
                showNames = True
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLOSER_ONLY):
        def func(name, textName, subName):
            testStr = "Dionysiaca, Abduction of Helen, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # test data
            if (subName != "Overall"):
                isTestData = True
                showNames = True
                if textName == "Iliad":
                    targetVal = 1
                    return False, isTestData, showNames, targetVal
                elif textName == "Odyssey":
                    targetVal = 2
                    return False, isTestData, showNames, targetVal
                elif textName == "HymnsLong":
                    targetVal = 3
                    return False, isTestData, showNames, targetVal
                elif textName == "Dionysiaca":
                    targetVal = 4
                    return False, isTestData, showNames, targetVal
                elif textName == "Argonautica":
                    targetVal = 5
                    return False, isTestData, showNames, targetVal
                else:
                    targetVal = 0
                    return False, isTestData, showNames, targetVal
            # non test data
            else:
                isTestData = False
                showNames = True
                targetVal = 2
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLOSER_ONLY_HERMES_LOOK):
        def func(name, textName, subName):
            testStr = "Dionysiaca, Abduction of Helen, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # test data
            if (subName != "Overall"):
                isTestData = True
                if textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "Iliad":
                    showNames = False
                    targetVal = 0
                elif textName == "Odyssey":
                    showNames = False
                    targetVal = 1
                else:
                    # skip
                    return True, False, False, 0
                return False, isTestData, showNames, targetVal
            #
            else:
                isTestData = False
                showNames = True
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    targetVal = 2
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    targetVal = 3
                elif textName == "CallimachusHymns":
                    targetVal = 5
                elif textName == "Idylls_Eidulia":
                    targetVal = 5
                elif textName == "Cynegetica":
                    targetVal = 8 # oppian was 1st/2nd century ad greco-roman
                elif textName == "Halieutica":
                    targetVal = 8 # oppian was 1st/2nd century ad greco-roman
                elif textName == "Fall of Troy":
                    targetVal = 8 # Quintus was 4th? century ad greco-roman
                elif textName == "The Taking of Ilios":
                    targetVal = 8 # Roman
                elif textName == "Argonautica":
                    targetVal = 5 # alexandrian, sure
                elif textName == "Phaenomena":
                    targetVal = 8 # alexandrian, sure
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLOSER_ONLY_HERMES_LOOK_DIONYSIACA_AS_TEST):
        def func(name, textName, subName):
            testStr = "Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # test data
            if (subName != "Overall" or textName == "Dionysiaca"
                or textName == "Works of Moschus" or textName == "Works of Bion"):
                isTestData = True
                if textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "Iliad":
                    showNames = False
                    targetVal = 0
                elif textName == "Odyssey":
                    showNames = False
                    targetVal = 1
                elif textName == "Dionysiaca":
                    showNames = False
                    targetVal = 7
                elif textName == "Abduction of Helen":
                    showNames = True
                    targetVal = 8
                elif textName == "Cynegetica":
                    showNames = True
                    targetVal = 8
                elif textName == "Halieutica":
                    showNames = True
                    targetVal = 8
                elif textName == "Fall of Troy":
                    showNames = True
                    targetVal = 8
                elif textName == "The Taking of Ilios":
                    showNames = True
                    targetVal = 8 # Roman
                elif textName == "Works of Bion":
                    showNames = True
                    targetVal = 8 # a little after Alexandria, 1/2 bc
                elif textName == "Works of Moschus":
                    showNames = True
                    targetVal = 8 # a little after Alexandria, 2 bc
                else:
                    # skip
                    return True, False, False, 8
                return False, isTestData, showNames, targetVal
            #
            else:
                isTestData = False
                showNames = True
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    targetVal = 2
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    targetVal = 3
                elif textName == "CallimachusHymns":
                    targetVal = 5
                elif textName == "Idylls_Eidulia":
                    targetVal = 5
                elif textName == "Cynegetica":
                    targetVal = 8 # oppian was 1st/2nd century ad greco-roman
                elif textName == "Halieutica":
                    targetVal = 8 # oppian was 1st/2nd century ad greco-roman
                elif textName == "Fall of Troy":
                    targetVal = 8 # Quintus was 4th? century ad greco-roman
                elif textName == "The Taking of Ilios":
                    targetVal = 8 # Roman
                elif textName == "Dionysiaca":
                    targetVal = 7
                elif textName == "Argonautica":
                    targetVal = 5 # alexandrian, sure
                elif textName == "Phaenomena":
                    targetVal = 8 # alexandrian, sure
                elif textName == "Idylls":
                    targetVal = 5
                elif textName == "Works of Bion":
                    targetVal = 8 # a little after Alexandria, 1/2 bc
                elif textName == "Works of Moschus":
                    targetVal = 8 # a little after Alexandria, 2 bc
                elif textName == "Abduction of Helen":
                    targetVal = 8
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLOSER_ONLY_HERMES_LOOK_DIONYSIACA_AS_TEST_1):
        def func(name, textName, subName):
            testStr = "Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # test data
            if (subName != "Overall" or textName == "Dionysiaca"
                or textName == "Works of Moschus" or textName == "Works of Bion"
                or textName == "Abduction of Helen" or textName == "The Taking of Ilios"):
                isTestData = True
                if textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "Iliad":
                    showNames = False
                    targetVal = 0
                elif textName == "Odyssey":
                    showNames = False
                    targetVal = 1
                elif textName == "Dionysiaca":
                    showNames = False
                    targetVal = 7
                elif textName == "Abduction of Helen":
                    showNames = True
                    targetVal = 8
                elif textName == "Cynegetica":
                    showNames = True
                    targetVal = 8
                elif textName == "Halieutica":
                    showNames = True
                    targetVal = 8
                elif textName == "Fall of Troy":
                    showNames = True
                    targetVal = 8
                elif textName == "The Taking of Ilios":
                    showNames = True
                    targetVal = 8 # Roman
                elif textName == "Works of Bion":
                    showNames = True
                    targetVal = 8 # a little after Alexandria, 1/2 bc
                elif textName == "Works of Moschus":
                    showNames = True
                    targetVal = 8 # a little after Alexandria, 2 bc
                else:
                    # skip
                    return True, False, False, 8
                return False, isTestData, showNames, targetVal
            #
            else:
                isTestData = False
                showNames = True
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    targetVal = 2
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    targetVal = 3
                elif textName == "CallimachusHymns":
                    targetVal = 5
                elif textName == "Idylls_Eidulia":
                    targetVal = 5
                elif textName == "Cynegetica":
                    targetVal = 8 # oppian was 1st/2nd century ad greco-roman
                elif textName == "Halieutica":
                    targetVal = 8 # oppian was 1st/2nd century ad greco-roman
                elif textName == "Fall of Troy":
                    targetVal = 8 # Quintus was 4th? century ad greco-roman
                elif textName == "The Taking of Ilios":
                    targetVal = 8 # Roman
                elif textName == "Dionysiaca":
                    targetVal = 7
                elif textName == "Argonautica":
                    targetVal = 5 # alexandrian, sure
                elif textName == "Phaenomena":
                    targetVal = 8 # alexandrian, sure
                elif textName == "Idylls":
                    targetVal = 5
                elif textName == "Works of Bion":
                    targetVal = 8 # a little after Alexandria, 1/2 bc
                elif textName == "Works of Moschus":
                    targetVal = 8 # a little after Alexandria, 2 bc
                elif textName == "Abduction of Helen":
                    targetVal = 8
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.HOMER_HESIOD_AND_THE_HYMNS):
        def func(name, textName, subName):
            testStr = "Cynegetica, Halieutica, Fall of Troy, The Taking of Ilios, Dionysiaca, Argonautica, Phaenomena, Idylls, Works of Bion, Works of Moschus, Abduction of Helen, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # test data
            if (subName != "Overall" or textName == "CallimachusHymns"):
                isTestData = True
                if textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "Iliad":
                    showNames = False
                    targetVal = 0
                elif textName == "Odyssey":
                    showNames = False
                    targetVal = 1
                elif textName == "CallimachusHymns":
                    showNames = True
                    targetVal = 8
                else:
                    # skip
                    return True, False, False, 8
                return False, isTestData, showNames, targetVal
            #
            else:
                isTestData = False
                showNames = True
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    targetVal = 3
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    targetVal = 2
                elif textName == "CallimachusHymns":
                    targetVal = 8
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.HOMER_AND_THE_HYMNS):
        def func(name, textName, subName):
            testStr = "Cynegetica, Halieutica, Fall of Troy, The Taking of Ilios, Dionysiaca, Argonautica, Phaenomena, Idylls, Works of Bion, Works of Moschus, Abduction of Helen, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # test data
            if (subName != "Overall" or textName == "CallimachusHymns" or textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony"):
                isTestData = True
                if textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "Iliad":
                    showNames = False
                    targetVal = 0
                elif textName == "Odyssey":
                    showNames = False
                    targetVal = 1
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    showNames = True
                    targetVal = 3
                elif textName == "CallimachusHymns":
                    showNames = True
                    targetVal = 8
                else:
                    # skip
                    return True, False, False, 8
                return False, isTestData, showNames, targetVal
            #
            else:
                isTestData = False
                showNames = True
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    targetVal = 2
                elif textName == "CallimachusHymns":
                    targetVal = 8
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.HOMER_TEST_HESIOD_AND_THE_HYMNS):
        def func(name, textName, subName):
            testStr = "Cynegetica, Halieutica, Fall of Troy, The Taking of Ilios, Dionysiaca, Argonautica, Phaenomena, Idylls, Works of Bion, Works of Moschus, Abduction of Helen, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # test data
            if (subName != "Overall" or textName == "CallimachusHymns" or textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony" or textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong"):
                isTestData = True
                if textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "Iliad":
                    showNames = False
                    targetVal = 0
                elif textName == "Odyssey":
                    showNames = False
                    targetVal = 1
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    showNames = True
                    targetVal = 3
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "CallimachusHymns":
                    showNames = True
                    targetVal = 8
                else:
                    # skip
                    return True, False, False, 8
                return False, isTestData, showNames, targetVal
            #
            else:
                isTestData = False
                showNames = True
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "CallimachusHymns":
                    targetVal = 8
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.HOMER_HESIOD_AND_THE_HYMNS_ALL):
        def func(name, textName, subName):
            testStr = "Cynegetica, Halieutica, Fall of Troy, The Taking of Ilios, Dionysiaca, Argonautica, Phaenomena, Idylls, Works of Bion, Works of Moschus, Abduction of Helen, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # test data
            if (textName == "CallimachusHymns"):
                isTestData = True
                if textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "Iliad":
                    showNames = False
                    targetVal = 0
                elif textName == "Odyssey":
                    showNames = False
                    targetVal = 1
                elif textName == "CallimachusHymns":
                    showNames = True
                    targetVal = 8
                else:
                    # skip
                    return True, False, False, 8
                return False, isTestData, showNames, targetVal
            #
            else:
                isTestData = False
                showNames = True
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    targetVal = 3
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    targetVal = 2
                elif textName == "CallimachusHymns":
                    targetVal = 8
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.HOMER_AND_THE_HYMNS_ALL):
        def func(name, textName, subName):
            testStr = "Cynegetica, Halieutica, Fall of Troy, The Taking of Ilios, Dionysiaca, Argonautica, Phaenomena, Idylls, Works of Bion, Works of Moschus, Abduction of Helen, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # test data
            if (textName == "CallimachusHymns" or textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony"):
                isTestData = True
                if textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "Iliad":
                    showNames = False
                    targetVal = 0
                elif textName == "Odyssey":
                    showNames = False
                    targetVal = 1
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    showNames = True
                    targetVal = 3
                elif textName == "CallimachusHymns":
                    showNames = True
                    targetVal = 8
                else:
                    # skip
                    return True, False, False, 8
                return False, isTestData, showNames, targetVal
            #
            else:
                isTestData = False
                showNames = True
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    targetVal = 2
                elif textName == "CallimachusHymns":
                    targetVal = 8
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.HOMER_TEST_HESIOD_AND_THE_HYMNS_ALL):
        def func(name, textName, subName):
            testStr = "Cynegetica, Halieutica, Fall of Troy, The Taking of Ilios, Dionysiaca, Argonautica, Phaenomena, Idylls, Works of Bion, Works of Moschus, Abduction of Helen, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0


            # test data
            if (textName == "CallimachusHymns" or textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony" or textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong"):
                isTestData = True
                if textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "Iliad":
                    showNames = False
                    targetVal = 0
                elif textName == "Odyssey":
                    showNames = False
                    targetVal = 1
                elif textName == "Works and Days" or textName == "Shield of Heracles" or textName == "Theogony":
                    showNames = True
                    targetVal = 3
                elif textName == "Hymns" or textName == "HymnsShort" or textName == "HymnsLong":
                    showNames = True
                    targetVal = 2
                elif textName == "CallimachusHymns":
                    showNames = True
                    targetVal = 8
                else:
                    # skip
                    return True, False, False, 8
                return False, isTestData, showNames, targetVal
            #
            else:
                isTestData = False
                showNames = True
                targetVal = 8
                # When we have 8:
                # 0 is red, 1 is blue, 2 is green, 3 is purple, 4 is orange
                # 5 is yellow, six is brown, 7 is pink, 8 is gray
                if textName == "Iliad":
                    targetVal = 0
                elif textName == "Odyssey":
                    targetVal = 1
                elif textName == "CallimachusHymns":
                    targetVal = 8
                return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLASSIFY_1):
        def func(name, textName, subName):
            testStr = "Hymns, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # don't include the overall for things we have subdivided
            if (textName == "Iliad" or textName == "Odyssey"
                or textName == "HymnsLong" or textName == "Dionysiaca"
                or textName == "Argonautica") and subName == "Overall":
                    return True, False, False, 0

            if textName == "Iliad" or textName == "Odyssey":
                targetVal = 1
            else:
                targetVal = 0
            isTestData = False
            showNames = True
            return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLASSIFY_2):
        def func(name, textName, subName):
            testStr = "HymnsLong, HymnsShort, Hymns, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # don't include the overall for things we have subdivided
            if (textName == "Iliad" or textName == "Odyssey"
                or textName == "HymnsLong" or textName == "Dionysiaca"
                or textName == "Argonautica") and subName == "Overall":
                    return True, False, False, 0

            if (textName != "Iliad" and textName != "Odyssey"
                and textName != "Dionysiaca"):
                    return True, False, False, 0

            if textName == "Iliad" or textName == "Odyssey":
                targetVal = 1
            else:
                targetVal = 0
            isTestData = False
            showNames = True
            return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLASSIFY_3):
        def func(name, textName, subName):
            #Works and Days, Theogony, Shield of Heracles, HymnsLong, HymnsShort,
            testStr = "Hymns, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # don't include the overall for things we have subdivided
            if ((textName == "Iliad" or textName == "Odyssey"
                or textName == "HymnsLong" or textName == "Dionysiaca"
                or textName == "Argonautica" or textName == "Cynegetica"
                or textName == "Halieutica" or textName == "Fall of Troy")
                and subName == "Overall"):
                    return True, False, False, 0

            isTestData = False
            showNames = True
            if textName == "Dionysiaca":
                showNames = False
            if textName == "Iliad" or textName == "Odyssey":
                showNames = False
                targetVal = 1
            else:
                targetVal = 0
            return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLASSIFY_4):
        def func(name, textName, subName):
            #Works and Days, Theogony, Shield of Heracles, HymnsLong, HymnsShort,
            testStr = "Hymns, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # don't include the overall for things we have subdivided
            if (textName == "Iliad" or textName == "Odyssey"
                or textName == "HymnsLong" or textName == "Dionysiaca"
                or textName == "Argonautica") and subName == "Overall":
                    return True, False, False, 0
            # skip
            if (name == "HymnsLong: Book 5" or name == "HymnsLong: Book 3" or name == "Shield of Heracles: Overall" or name == "Idylls_Eidulia: Overall"):
                return True, False, False, 0

            if textName == "Iliad" or textName == "Odyssey":
                targetVal = 1
            else:
                targetVal = 0
            isTestData = False
            showNames = True
            return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLASSIFY_5):
        def func(name, textName, subName):
            #Works and Days, Theogony, Shield of Heracles, HymnsLong, HymnsShort,
            testStr = "Hymns, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # don't include the overall for things we have subdivided
            if (textName == "Iliad" or textName == "Odyssey"
                or textName == "HymnsLong" or textName == "Dionysiaca"
                or textName == "Argonautica") and subName == "Overall":
                    return True, False, False, 0

            #  name == "Idylls_Eidulia: Overall"
            if not(textName == "Iliad" or textName == "Odyssey" or name == "HymnsLong: Book 5" or name == "HymnsLong: Book 3" or name == "Shield of Heracles: Overall"):
                return True, False, False, 0

            isTestData = False
            showNames = True
            if textName == "Iliad" or textName == "Odyssey":
                showNames = False
                targetVal = 1
            else:
                targetVal = 0
            return False, isTestData, showNames, targetVal
        return generalGrab(func)
    elif (dataName == DATA_SETS.CLASSIFY_6): # 3 but with names
        def func(name, textName, subName):
            #Works and Days, Theogony, Shield of Heracles, HymnsLong, HymnsShort,
            testStr = "Hymns, Epitaphius Bios, Eros Drapeta, Europa, Megara, Idylls_Epigrams, Epithalamium Achillis et Deidameiae, Epitaphius Adonis, Fragmenta"
            # skip
            if (testStr.find(textName) != -1) or (name == "HymnsLong: Book 1"):
                return True, False, False, 0

            # don't include the overall for things we have subdivided
            if ((textName == "Iliad" or textName == "Odyssey"
                or textName == "HymnsLong" or textName == "Dionysiaca"
                or textName == "Argonautica" or textName == "Cynegetica"
                or textName == "Halieutica" or textName == "Fall of Troy")
                and subName == "Overall"):
                    return True, False, False, 0

            isTestData = False
            showNames = True
            if textName == "Iliad" or textName == "Odyssey":
                targetVal = 1
            else:
                targetVal = 0
            return False, isTestData, showNames, targetVal
        return generalGrab(func)
    return {"data": [], "target": []}, [], [], []


# run preprocessing before pca
# adapted from code by Manoj Kumar <mks542@nyu.edu>
def pcaPreprocess(X, X2, y, preprocessType, saveResults, saveDir):
    fName = utils.getFeatureMatrixFn()
    matrixStorage = utils.getContent(fName, True)
    featureNames = matrixStorage["featureNames"]

    if preprocessType > 0.0:
        clf = LassoCV()
        # .15 -> 29
        # .25 -> 26
        # .4 -> 25
        # .6 -> 23
        sfm = SelectFromModel(clf, threshold=preprocessType)
        sfm.fit(X, y)
        n_features = sfm.transform(X).shape[1]

        indices = sfm.get_support(True)

        newX = X[:,indices]

        if len(X2) == 0 or X2.shape[0] == 0:
            newX2 = X2
        else:
            newX2 = X2[:,indices]

        newFeatureNames = np.array(featureNames)[indices]

        if (saveResults):
            output = []
            output.append(str(indices.shape))
            for nfn in newFeatureNames:
                output.append("  " + nfn)

            s = "\n".join(output)
            filename = saveDir + "featuresChosenByPreprocessing.txt"
            utils.safeWrite(filename, s)

        return newX, newX2, newFeatureNames

    return X, X2, featureNames

# do PCA down to 3 components, then visualize
# Portions of this adapted from code written by Gaël Varoquaux

# dataSet is the list of data to train on, with names as an array of names for those feature vectors
# testSet is the list of data to test on, with testNames as an array of names for those feature vectors
# includeNames is true if we want to print the names in the figure
# saveOutput is true if we want to save the feature to a file rather than view it
# preprocessType refers to the type of preprocessing to do
#   (it is a float specifying the lasso feature selection cutoff, or 0 for no selection)
def pca3Viz(dataSet, names, testSet, testNames, includeNames, saveOutput, saveDir, preprocessType):
    np.random.seed(5)

    X = dataSet.data
    y = dataSet.target
    X2 = testSet.data
    y2 = testSet.target

    X, X2, _ = pcaPreprocess(X, X2, y, preprocessType, False, saveDir)


    # set figure size
    plt.clf()
    if saveOutput:
        fig = plt.figure()
        fig.set_size_inches((11.), (8.5))
    else:
        fig = plt.figure(1, figsize=(8, 6))

    # set 3d axes
    ax = Axes3D(fig, rect=[0, 0, .95, 1], elev=48, azim=134)

    # train PCA
    plt.cla()
    pca = decomposition.PCA(n_components=3)
    pca.fit(X)
    if (False):
        for i in range(len(names)):
            print names[i]
            print pca.transform([X[i]])
        print "---"
        print pca.explained_variance_
        cpts = pca.components_[0]
        for i in range(len(cpts)):
            if (cpts[i] < -0.014):
                print "%d : %f" % (i, cpts[i])
        for i in range(len(names)):
            print names[i] + ": " + str(X[i][65])

    # transform the training and test data
    X = pca.transform(X)
    if (len(testNames) > 0):
        X2 = pca.transform(X2)

    # get the final sets to display
    if (len(testNames) > 0):
        Xfinal = np.append(X, X2, axis=0)
        yFinal = np.append(y, y2, axis=0)
        namesFinal = np.append(names, testNames, axis=0)
    else:
        Xfinal = X
        yFinal = y
        namesFinal = names

    # if we include names, print them
    if (includeNames):
        for i in range(len(Xfinal)):
            name = namesFinal[i]
            ax.text3D(Xfinal[i, 0], Xfinal[i, 1], (Xfinal[i, 2] + 0.01),
                      name,
                      horizontalalignment='center', size=8)


    # plot the data.
    ax.scatter(Xfinal[:, 0], Xfinal[:, 1], Xfinal[:, 2], c=yFinal, cmap=plt.get_cmap("Set1"))

    ax.w_xaxis.set_ticklabels([])
    ax.w_yaxis.set_ticklabels([])
    ax.w_zaxis.set_ticklabels([])


    # save or show the data
    if saveOutput:
        if includeNames:
            labelText = "_labels"
        else:
            labelText = "_no_labels"
        filename = saveDir + "pca3D" + labelText + ".pdf"
        utils.check_and_create_path(filename)
        pp = PdfPages(filename)
        pp.savefig()
        pp.close()
    else:
        plt.show()

# do PCA down to 2 components, then visualize
# Portions of this adapted from code written by Gaël Varoquaux

# dataSet is the list of data to train on, with names as an array of names for those feature vectors
# testSet is the list of data to test on, with testNames as an array of names for those feature vectors
# includeNames is true if we want to print the names in the figure
# saveOutput is true if we want to save the feature to a file rather than view it
# preprocessType refers to the type of preprocessing to do
#   (it is a float specifying the lasso feature selection cutoff, or 0 for no selection)
# oneThree is true if we are examining axes 1 and 3 rather than 1 and 2
def pca2Viz(dataSet, names, testSet, testNames, includeNames, saveOutput, saveDir, preprocessType, oneThree):
    np.random.seed(5)

    X = dataSet.data
    y = dataSet.target
    X2 = testSet.data
    y2 = testSet.target

    X, X2, _ = pcaPreprocess(X, X2, y, preprocessType, False, saveDir)

    # set figure size
    plt.clf()
    if saveOutput:
        fig = plt.figure()
        fig.set_size_inches((11.), (8.5))
    else:
        fig = plt.figure(1, figsize=(8, 6))


    # get the proper axes to examine
    if (oneThree):
        ax0 = 0
        ax1 = 2
        numComponents = 3
    else:
        ax0 = 0
        ax1 = 1
        numComponents = 2

    # train PCA and transform data
    pca = decomposition.PCA(n_components=numComponents)
    pca.fit(X)
    X = pca.transform(X)
    if (len(testNames) > 0):
        X2 = pca.transform(X2)

    # get the final sets to display
    if (len(testNames) > 0):
        Xfinal = np.append(X, X2, axis=0)
        yFinal = np.append(y, y2, axis=0)
        namesFinal = np.append(names, testNames, axis=0)
    else:
        Xfinal = X
        yFinal = y
        namesFinal = names


    # if we include names, print them
    if (includeNames):
        for i in range(len(Xfinal)):
            name = namesFinal[i]
            plt.text(Xfinal[i, ax0], (Xfinal[i, ax1] + 0.01),
                      name,
                      horizontalalignment='center', size=8)

    # plot the data.
    plt.scatter(Xfinal[:, ax0], Xfinal[:, ax1], s=49, c=yFinal, cmap=plt.get_cmap("Set1"))

    # save or show the data
    if saveOutput:
        if includeNames:
            labelText = "_labels"
        else:
            labelText = "_no_labels"
        if (oneThree):
            oneThreeText = "_1_3"
        else:
            oneThreeText = ""
        filename = saveDir + "pca2D" + oneThreeText + labelText + ".pdf"
        utils.check_and_create_path(filename)
        pp = PdfPages(filename)
        pp.savefig()
        pp.close()
    else:
        plt.show()
    plt.close()

# do PCA down to 2 components, then visualize
# Portions of this adapted from code written by Gaël Varoquaux

# dataSet is the list of data to train on, with names as an array of names for those feature vectors
# testSet is the list of data to test on, with testNames as an array of names for those feature vectors
# includeNames is true if we want to print the names in the figure
# saveOutput is true if we want to save the feature to a file rather than view it
# preprocessType refers to the type of preprocessing to do
#   (it is a float specifying the lasso feature selection cutoff, or 0 for no selection)
def pca4Viz(dataSet, names, testSet, testNames, includeNames, saveOutput, saveDir, preprocessType):
    np.random.seed(5)

    X = dataSet.data
    y = dataSet.target
    X2 = testSet.data
    y2 = testSet.target

    X, X2, _ = pcaPreprocess(X, X2, y, preprocessType, False, saveDir)

    # set figure size
    plt.clf()
    if saveOutput:
        fig, axes = plt.subplots(2)
        fig.set_size_inches((8.5), (11))
    else:
        fig, axes = plt.subplots(2)

    # train and apply PCA
    pca = decomposition.PCA(n_components=4)
    pca.fit(X)
    X = pca.transform(X)
    if (len(testNames) > 0):
        X2 = pca.transform(X2)



    # get the final sets to display
    if (len(testNames) > 0):
        Xfinal = np.append(X, X2, axis=0)
        yFinal = np.append(y, y2, axis=0)
        namesFinal = np.append(names, testNames, axis=0)
    else:
        Xfinal = X
        yFinal = y
        namesFinal = names

    # make the two plots, with names if we are including names
    for k in range(len(axes)):
        ax = axes[k]
        offset = k*2
        secondStartIndex = 1
        if (includeNames):
            for i in range(len(Xfinal)):
                name = namesFinal[i]
                ax.text(Xfinal[i, 0+offset], (Xfinal[i, secondStartIndex+offset] + 0.01),
                          name,
                          horizontalalignment='center', size=8)

        ax.scatter(Xfinal[:, 0+offset], Xfinal[:, secondStartIndex+offset], s=49, c=yFinal, cmap=plt.get_cmap("Set1"))

    # save or show the data
    if saveOutput:
        if includeNames:
            labelText = "_labels"
        else:
            labelText = "_no_labels"
        filename = saveDir + "pca4D" + labelText + ".pdf"
        utils.check_and_create_path(filename)
        pp = PdfPages(filename)
        pp.savefig()
        pp.close()
    else:
        plt.show()

    plt.close()

# report on the features used in this level of PCA
# same as pcaViz above, but just saves a report rather than printing a graph.
def pcaReport(dataSet, names, dimensions, saveOutput, saveDir, preprocessType):
    np.random.seed(5)

    X = dataSet.data
    y = dataSet.target

    X, _, featureNames = pcaPreprocess(X, [], y, preprocessType, True, saveDir)

    pca = decomposition.PCA(n_components=dimensions)
    pca.fit(X)

    output = []
    for i in range(len(pca.components_)):
        output.append("Component %d" % i)
        component = pca.components_[i]
        indices = range(len(component))
        zipped = np.dstack((component, indices, featureNames))



        sortedZipped = sorted(zipped.tolist()[0], key=lambda x: abs(float(x[0])), reverse=True)

        for item in sortedZipped:
            if (float(item[0]) != 0.0):
                output.append("  %s: %s" % (item[0], item[2]))

        output.append("===============")

    s = "\n".join(output)

    if saveOutput:
        filename = saveDir + "pcaReport" + str(dimensions) + ".txt"
        utils.safeWrite(filename, s)
    else:
        print s

# Save a large amount of specific data on how the components of the PCA
# apply to each text for closer analysis of what they are picking for components.
def pcaCheck(dataSet, names, dimensions, saveOutput, saveDir, preprocessType):
    np.random.seed(5)

    X = dataSet.data
    y = dataSet.target

    X, _, featureNames = pcaPreprocess(X, [], y, preprocessType, True, saveDir)


    pca = decomposition.PCA(n_components=dimensions)
    pca.fit(X)

    X2 = pca.transform(X)

    output = []

    for i in range(len(names)):
        name = names[i]
        data = X2[i]
        output.append("%s: [%s]" % (name, ", ".join(map(str, data))))

    flipped = np.swapaxes(X, 0, 1)

    for i in range(len(pca.components_)):
        output.append("Component %d" % i)
        component = pca.components_[i]
        flip = flipped
        flipWeighted = []
        for text in X:
            flipWeighted.append(np.multiply(text, component))
        flipWeighted = np.swapaxes(np.array(flipWeighted), 0, 1)
        indices = range(len(component))
        zipped = np.dstack((component, indices, featureNames))



        sortedZipped = sorted(zipped.tolist()[0], key=lambda x: abs(float(x[0])), reverse=True)

        runningCounts = []
        for name in names:
            label = name[0] + name.split(": ")[1].replace("Book ", "")
            runningCounts.append([0.0, label])

        for item in sortedZipped:
            if (float(item[0]) != 0.0):
                output.append("  %s: %s" % (item[0], item[2]))
                myIndex = int(item[1])
                myFlip = flip[myIndex]
                myWeighted = flipWeighted[myIndex]
                #output.append("  [%s]" % ", ".join(map(str, myFlip)))
                #output.append("  [%s]" % ", ".join(map(str, myWeighted)))

                for j in range(len(myWeighted)):
                    runningCounts[j][0] += float(myWeighted[j])

                subZipped = np.dstack((myWeighted, names))
                sortedWeighted = sorted(subZipped.tolist()[0], key=lambda x: abs(float(x[0])), reverse=True)
                s = []
                for subItem in sortedWeighted:
                    val = float(subItem[0])
                    name = subItem[1]
                    label = name[0] + name.split(": ")[1].replace("Book ", "")
                    s.append("%s: %.5f" % (label, val))
                output.append("  This Component: [" + ", ".join(s) + "]")

                sortedRunning = sorted(copy.deepcopy(runningCounts), key=lambda x: float(x[0]), reverse=True)
                s = []
                for subItem in sortedRunning:
                    val = float(subItem[0])
                    label = subItem[1]
                    s.append("%s: %.5f" % (label, val))
                output.append("  Running Total: [" + ", ".join(s) + "]")
                output.append("  ------")

        output.append("===============")

    s = "\n".join(output)

    if saveOutput:
        filename = saveDir + "pca" + str(dimensions) + "ReportWithTextResults.txt"
        utils.safeWrite(filename, s)
    else:
        print s


# get the pieces for a classifying pipeline.
def getClassifierPipelinePieces(IncludeAllTypes):
    preps = [
    ["Standard Scaler", lambda: preprocessing.StandardScaler()]
    ]

    for comp in [2, 3, 4]:
        name = "PCA %d" % comp
        preps.append([name, lambda: decomposition.PCA(n_components=comp)])

    featureSelectors = []

    # can also include .6, but doesn't add much value for the time cost;
    if (IncludeAllTypes):
        thresholds = [0.0, .15, .25, .4]
    else:
        thresholds = [0.0, .25]

    #thresholds = [0.0]

    for threshold in thresholds:
        if (threshold > 0):
            name = "Lasso CV, threshold %.2f" % threshold
        else:
            name = "No Feature Selection"
        featureSelectors.append([name, threshold])



    #,
    #["Linear SVC", lambda: decomposition.PCA(n_components=4)]
    #for threshold in [.15, .25, .4, .6]:
    #clf = LassoCV()
    #sfm = SelectFromModel(clf, threshold=preprocessType)

    classifiers = [
    ["Logistic Regression", lambda: linear_model.LogisticRegression()],
    ["SVM (Linear)", lambda: svm.SVC(kernel='linear')],
    ["SVM (RBF)", lambda: svm.SVC(kernel='rbf')],
    ["Random Forest", lambda: ensemble.RandomForestClassifier()]
    ]
    for i in range(2,6):
        classifiers.append(["KNN (" + str(i) + ", By Distance)", lambda: neighbors.KNeighborsClassifier(n_neighbors=i)])
        classifiers.append(["KNN (" + str(i) + ")", lambda: neighbors.KNeighborsClassifier(n_neighbors=i, weights='distance')])

    return featureSelectors, preps, classifiers

# run crossfold validation for the checkers on the provided data
# dataSet is the list of data to train on, with names as an array of names for those feature vectors
# testSet is the list of data to test on, with testNames as an array of names for those feature vectors
# includeNames is true if we want to print the names in the figure
# saveOutput is true if we want to save the feature to a file rather than view it
# saveDir is the directory in which to save the info
def crossValidateClassifiers(dataSet, names, testSet, testNames, includeNames, saveOutput, saveDir):
    data = dataSet.data
    target = dataSet.target
    if (False):
        clf = make_pipeline(preprocessing.StandardScaler(), svm.SVC(C=1))
        print cross_val_score(clf, data, target, cv=5)


    featureSelectors, preps, classifiers = getClassifierPipelinePieces(False)

    #print data.shape

    cv = ShuffleSplit(n_splits=5, test_size=.1)

    output = []

    total = 0
    sumAvgs = 0.0

    for f in featureSelectors:
        data, _, _ = pcaPreprocess(data, [], target, f[1], False, "")
        for p in preps:
            subTotal = 0
            subAvg = 0.0
            for c in classifiers:
                if ((f[0][0:5] == "Lasso" and p[0].find("PCA") == -1) and (c[0] == "SVM (RBF)")):
                    continue
                pipe = make_pipeline(p[1](), c[1]())
                name =  "%s -> %s -> %s" % (f[0], p[0], c[0])
                print name
                scores = cross_val_score(pipe, data, target, cv=cv)
                avg = np.mean(scores)
                total += 1
                subTotal += 1
                sumAvgs += avg
                subAvg += avg
                output.append("%s Scores: [%s] - %f" % (name, ", ".join(map(str, scores)), avg))

                output.append("-----")
            output.append("Avg for this prep: %f" % (subAvg/subTotal))
            output.append("=============")

    output.append("Total avg: %f" % (sumAvgs/total))

    s = "\n".join(output)
    if saveOutput:
        fn = saveDir + "CrossValidateClassifiers.txt"
        utils.safeWrite(fn, s)
    else:
        print s
    # SVM is about finding a plane to maximize the margin; we sortof have this
    # w/ 4 dimensions.
    # svc = svm.SVC(kernel='linear')
    # or, in 3 dimensions, the RBF kernel (svc = svm.SVC(kernel='rbf'))
    # looks good

    if (False):
        n_samples = len(data)

        X_train = data[:.9 * n_samples]
        y_train = target[:.9 * n_samples]
        X_test = data[.9 * n_samples:]
        y_test = target[.9 * n_samples:]

        knn = neighbors.KNeighborsClassifier()
        logistic = linear_model.LogisticRegression()

        print('KNN score: %f' % knn.fit(X_train, y_train).score(X_test, y_test))
        print('LogisticRegression score: %f' % logistic.fit(X_train, y_train).score(X_test, y_test))


# run all the classifiers on the data and either print or save the output
def runClassifiers(data, saveOutput, saveName):
    # set up classifiers
    (X_Train, X_Test, y_Train, y_Test, n_Train, n_Test, names) = data

    featureSelectors, preps, classifiers = getClassifierPipelinePieces(True)

    results = []

    for f in featureSelectors:
        for p in preps:
            for c in classifiers:
                name = "%s -> %s -> %s Scores:" % (f[0], p[0], c[0])
                if ((f[0][0:5] == "Lasso" and p[0].find("PCA") == -1) and (c[0] == "SVM (RBF)")):
                    continue
                myRes = []
                failures = []
                results.append([name, myRes, failures])

    # prepare the info per text
    resultsByText = []
    resultsByTextIndices = {}
    for ii in range(len(names)):
        name = names[ii]
        resultsByText.append([name, 0, []])
        resultsByTextIndices[name] = ii

    for fold in range(len(X_Train)):
        xTr = X_Train[fold]
        yTr = y_Train[fold]
        xTe = X_Test[fold]
        yTe = y_Test[fold]
        nTe = n_Test[fold]

        k = 0
        for f in featureSelectors:
            xTrSelected, xTeSelected, _ = pcaPreprocess(xTr, xTe, yTr, f[1], False, "")
            for p in preps:
                for c in classifiers:
                    if ((f[0][0:5] == "Lasso" and p[0].find("PCA") == -1) and (c[0] == "SVM (RBF)")):
                        continue
                    print str(fold) + ": " + results[k][0]
                    pipe = make_pipeline(p[1](), c[1]())
                    pipe.fit(xTrSelected, yTr)
                    total = 0
                    success = 0
                    reports = []
                    for j in range(len(xTe)):
                        test = xTeSelected[j]
                        target = yTe[j]
                        name = nTe[j]
                        pred = pipe.predict([test])
                        total += 1
                        if (pred != target):
                            report = "  %s: Mismatch. Predicted %d, Actually %d" % (name, pred, target)
                            # report that this text was misidentified
                            index = resultsByTextIndices[name]
                            resultsByText[index][1] = resultsByText[index][1] + 1
                            resultsByText[index][2].append(results[k][0][:-1])
                            reports.append(report)
                        else:
                            success += 1
                    acc = (success*1.0)/total
                    results[k][1].append(acc)
                    results[k][2].append("\n".join(reports))

                    k += 1


    # report on the classifiers
    output = []
    total = 0
    sumAvgs = 0.0
    for res in results:
        name = res[0]
        accuracy = res[1]
        reports = res[2]
        output.append(name)
        mean = np.mean(accuracy)
        total += 1
        sumAvgs += mean
        output.append("Avg: %f" % (mean))
        output.append("[" + ", ".join(map(str, accuracy)) + "]")
        output.append("  ----")
        for i in range(len(reports)):
            rep = reports[i]
            if (rep != ""):
                output.append("  " + str(accuracy[i]))
                output.append(rep)
                output.append("  ----")
        output.append("=========")

    output.append("Overall accuracy: %f" % (sumAvgs/total))
    s1 = "\n".join(output)

    output = []
    tableOutput = []
    numClassifiers = k
    # report on the texts
    for res in resultsByText:
        name = res[0]
        failures = res[1]
        failedOn = res[2]

        output.append("Text " + name + ":")
        output.append("Failed on %d out of %d." % (failures, numClassifiers))
        output.append("(" + ", ".join(failedOn) + ")")
        output.append("===========")
        tableOutput.append([name, "%.0f\%% (%d/%d)" % (failures*100.0/numClassifiers, failures, numClassifiers)])

    s2 = "\n".join(output)

    if saveOutput:
        fn1 = saveName + "_ByClassifier.txt"
        fn2 = saveName + "_ByText.txt"
        utils.safeWrite(fn1, s1)
        utils.safeWrite(fn2, s2)
    else:
        print s1
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        print s2

    return tableOutput


# run a custom crossfold validation that evenly splits up Homeric,
# Pseudo-Homeric, and Non-Homeric texts.
def classifySpecialCrossfold(dataSet, names, testSet, testNames, includeNames, saveOutput, saveDir):
    Homeric = []
    hNames = []
    hTargets = []
    PseudoHomeric = []
    phNames = []
    phTargets = []
    NonHomeric = []
    nhNames = []
    nhTargets = []
    for i in range(len(names)):
        split = names[i].split(": ")
        if split[0] == "Iliad" or split[0] == "Odyssey":
            Homeric.append(dataSet.data[i])
            hNames.append(names[i])
            hTargets.append(0)
        elif split[0][0:5] == "Hymns":
            PseudoHomeric.append(dataSet.data[i])
            phNames.append(names[i])
            phTargets.append(1)
        else:
            NonHomeric.append(dataSet.data[i])
            nhNames.append(names[i])
            nhTargets.append(1)

    Homeric = np.array(Homeric)
    PseudoHomeric = np.array(PseudoHomeric)
    NonHomeric = np.array(NonHomeric)

    hNames = np.array(hNames)
    phNames = np.array(phNames)
    nhNames = np.array(nhNames)

    hTargets = np.array(hTargets)
    phTargets = np.array(phTargets)
    nhTargets = np.array(nhTargets)

    # set up folds
    kf = KFold(n_splits=5, shuffle=True, random_state=10)
    hSplit = kf.split(Homeric)
    phSplit = kf.split(PseudoHomeric)
    nhSplit = kf.split(NonHomeric)

    X_Train = []
    X_Test = []
    y_Train = []
    y_Test = []
    n_Train = []
    n_Test = []
    for hTrain, hTest in hSplit:
        X1_Train, X1_Test = Homeric[hTrain], Homeric[hTest]
        y1_Train, y1_Test = hTargets[hTrain], hTargets[hTest]
        n1_Train, n1_Test = hNames[hTrain], hNames[hTest]
        X_Train.append(X1_Train)
        X_Test.append(X1_Test)

        y_Train.append(y1_Train)
        y_Test.append(y1_Test)

        n_Train.append(n1_Train)
        n_Test.append(n1_Test)
    j = 0
    for phTrain, phTest in phSplit:
        X2_Train, X2_Test = PseudoHomeric[phTrain], PseudoHomeric[phTest]
        y2_Train, y2_Test = phTargets[phTrain], phTargets[phTest]
        n2_Train, n2_Test = phNames[phTrain], phNames[phTest]
        X_Train[j] = np.append(X_Train[j], X2_Train, axis=0)
        X_Test[j] = np.append(X_Test[j], X2_Test, axis=0)

        y_Train[j] = np.append(y_Train[j], y2_Train, axis=0)
        y_Test[j] = np.append(y_Test[j], y2_Test, axis=0)

        n_Train[j] = np.append(n_Train[j], n2_Train, axis=0)
        n_Test[j] = np.append(n_Test[j], n2_Test, axis=0)
        j += 1
    j = 0
    for nhTrain, nhTest in nhSplit:
        X3_Train, X3_Test = NonHomeric[nhTrain], NonHomeric[nhTest]
        y3_Train, y3_Test = nhTargets[nhTrain], nhTargets[nhTest]
        n3_Train, n3_Test = nhNames[nhTrain], nhNames[nhTest]
        X_Train[j] = np.append(X_Train[j], X3_Train, axis=0)
        X_Test[j] = np.append(X_Test[j], X3_Test, axis=0)

        y_Train[j] = np.append(y_Train[j], y3_Train, axis=0)
        y_Test[j] = np.append(y_Test[j], y3_Test, axis=0)

        n_Train[j] = np.append(n_Train[j], n3_Train, axis=0)
        n_Test[j] = np.append(n_Test[j], n3_Test, axis=0)
        j += 1

    data = (X_Train, X_Test, y_Train, y_Test, n_Train, n_Test, names)
    saveName = saveDir + "classifiersKFoldResults"
    return runClassifiers(data, saveOutput, saveName)

# check the entire classifier against one text that has been held out
def classifyOneHeldOut(dataSet, names, testSet, testNames, includeNames, saveOutput, saveDir):

    data = dataSet.data
    targets = dataSet.target
    names = np.array(names)

    # set up folds
    kf = KFold(n_splits=data.shape[0])

    X_Train = []
    X_Test = []
    y_Train = []
    y_Test = []
    n_Train = []
    n_Test = []
    for train, test in kf.split(data):
        xTr, xTe = data[train], data[test]
        yTr, yTe = targets[train], targets[test]
        nTr, nTe = names[train], names[test]
        X_Train.append(xTr)
        X_Test.append(xTe)
        y_Train.append(yTr)
        y_Test.append(yTe)
        n_Train.append(nTr)
        n_Test.append(nTe)

    data = (X_Train, X_Test, y_Train, y_Test, n_Train, n_Test, names)
    saveName = saveDir + "classifiersOneHeldOutResults"
    return runClassifiers(data, saveOutput, saveName)


# run a custom crossfold validation where we hold out the books of the
# Iliad/Odyssey for training, then run the classifier on the held out books.
def classifyIOHeldOut(dataSet, names, testSet, testNames, includeNames, saveOutput, saveDir):

    X_Train = []
    X_Test = []
    y_Train = []
    y_Test = []
    n_Train = []
    n_Test = []
    for leaveOutName in ["Iliad", "Odyssey"]:
        X1_Train = []
        X1_Test = []
        y1_Train = []
        y1_Test = []
        n1_Train = []
        n1_Test = []

        for i in range(len(names)):
            split = names[i].split(": ")
            if split[0] == leaveOutName:
                X1_Test.append(dataSet.data[i])
                y1_Test.append(dataSet.target[i])
                n1_Test.append(names[i])
            else:
                X1_Train.append(dataSet.data[i])
                y1_Train.append(dataSet.target[i])
                n1_Train.append(names[i])


        X1_Train = np.array(X1_Train)
        X1_Test = np.array(X1_Test)
        y1_Train = np.array(y1_Train)
        y1_Test = np.array(y1_Test)
        n1_Train = np.array(n1_Train)
        n1_Test = np.array(n1_Test)

        X_Train.append(X1_Train)
        X_Test.append(X1_Test)
        y_Train.append(y1_Train)
        y_Test.append(y1_Test)
        n_Train.append(n1_Train)
        n_Test.append(n1_Test)


    data = (X_Train, X_Test, y_Train, y_Test, n_Train, n_Test, names)
    saveName = saveDir + "classifiersIOHeldOutResults"
    return runClassifiers(data, saveOutput, saveName)

# build resulting latex tables
def buildResultLatexTables(r1, r2, r3, saveDir):
    table1Lines = []
    table2Lines = []
    table3Lines = []
    for ii in range(len(r1)):
        name = r1[ii][0]
        foldResult = r1[ii][1]
        holdResult = r2[ii][1]
        ioResult =   r3[ii][1]

        nameSplit = name.split(": ")
        if (nameSplit[1] == "Overall"):
            resultName = "\\textit{%s}" % nameSplit[0]
        else:
            resultName = "\\textit{%s}: %s" % (nameSplit[0], nameSplit[1])


        t12Str = "%s & %s & %s" % (name, foldResult, holdResult)
        t3Str = "%s & %s" % (name, ioResult)

        if (name[0:5] == "Iliad"):
            table1Lines.append(t12Str)
            table3Lines.append(t3Str)
        elif (name[0:7] == "Odyssey"):
            oldI = ii - 24
            table1Lines[oldI] = table1Lines[oldI] + " & " + t12Str + "\\\\ \\hline"
            table3Lines[oldI] = table3Lines[oldI] + " & " + t3Str + "\\\\ \\hline"
        elif (name[0:10] != "Dionysiaca"):
            table2Lines.append(t12Str + "\\\\ \\hline")

    table1Str = "\n".join(table1Lines)
    table2Str = "\n".join(table2Lines)
    table3Str = "\n".join(table3Lines)

    s1 = table1Str + "\n\n\n" + table2Str
    s2 = table3Str

    fn1 = saveDir + "classifierResultsLatexTablePiece.txt"
    fn2 = saveDir + "ioClassifierResultsLatexTablePiece.txt"
    utils.safeWrite(fn1, s1)
    utils.safeWrite(fn2, s2)

# function for testing a single results grab
def getResults(dataName):
    data, names, test, testNames = getData(dataName)
    saveDir = utils.getFinalResultsOutputDir(dataName);


    dataName = DATA_SETS.AUTHORS_SPLIT
    data, names, test, testNames = getData(dataName)
    saveDir = utils.getFinalResultsOutputDir(dataName)
    crossValidateClassifiers(data, names, test, testNames, True, True, saveDir)

    if (False):
        threshold = 0.6

        myDir = saveDir + "0dot" + ("%.2f_" % threshold)[2:]
        pca4Viz(data, names, test, testNames, False, True, myDir, threshold)
        pca4Viz(data, names, test, testNames, True, True, myDir, threshold)

    #pca2Viz(data, names, test, testNames, True, False, saveDir, 0, False)
    #pca2Viz(data, names, test, testNames, True, True, saveDir, 0, True)
    #pca3Viz(data, names, test, testNames, True, False, saveDir, 0)
    #pca4Viz(data, names, test, testNames, True, False, saveDir, 0)
    #pcaReport(data, names, 4, True, saveDir, 0)

    #pcaCheck(data, names, 3, True, saveDir, 0)
    #pcaCheck(data, names, 3, True, saveDir, 1)
    #pca3Viz(data, names, test, testNames, True, False, saveDir, 1)

    #classifySpecialCrossfold(data, names, test, testNames, True, True, saveDir)

    #crossValidateClassifiers(data, names, test, testNames, True, True, saveDir)


    # use dataset 6 for the following
    #classifySpecialCrossfold(data, names, test, testNames, True, True, saveDir)
    #classifyOneHeldOut(data, names, test, testNames, True, True, saveDir)
    #classifyIOHeldOut(data, names, test, testNames, True, True, saveDir)


# run all of our results analyses
# skipBlockingSteps is true if we want to skip the 3D graphs that
# block execution
def resultsPipeline(skipBlockingSteps):
    verbose = True
    if (True):
        dataSets = [
        DATA_SETS.ALL_OVERALLS_SUB_BOOKS,
        DATA_SETS.CLOSER_ONLY_HERMES_LOOK_DIONYSIACA_AS_TEST,
        DATA_SETS.CLASSIFY_3,
        DATA_SETS.ILIAD_ODYSSEY,
        DATA_SETS.HOMER_HESIOD_AND_THE_HYMNS_ALL
        ]
        for dataName in dataSets:
            data, names, test, testNames = getData(dataName)
            saveDir = utils.getFinalResultsOutputDir(dataName)
            pca2Viz(data, names, test, testNames, True, True, saveDir, 0, False)
            pca2Viz(data, names, test, testNames, False, True, saveDir, 0, False)
            pca2Viz(data, names, test, testNames, True, True, saveDir, 0, True)
            pca2Viz(data, names, test, testNames, False, True, saveDir, 0, True)
            if not(skipBlockingSteps):
                print "PCA3 for data set %s" % (dataName)
                # we show this twice so the first time I can grab book names,
                # the second time I can take nicer result screenshots
                pca3Viz(data, names, test, testNames, True, False, saveDir, 0)
                pca3Viz(data, names, test, testNames, False, False, saveDir, 0)
            pca4Viz(data, names, test, testNames, True, True, saveDir, 0)
            pca4Viz(data, names, test, testNames, False, True, saveDir, 0)

            # PCA report
            pcaReport(data, names, 4, True, saveDir, 0)
            if verbose:
                print "  Done with visualizations for %s" % dataName

    if (True):
        dataSets = [
        DATA_SETS.CLASSIFY_6,
        DATA_SETS.HOMER_HESIOD_AND_THE_HYMNS_ALL
        ]
        for dataName in dataSets:
            data, names, test, testNames = getData(dataName)
            saveDir = utils.getFinalResultsOutputDir(dataName)
            # PCA report to let us know why things end up where they are
            #pca3Viz(data, names, test, testNames, True, False, saveDir, 0)

            # threshold to features
            # .15 -> 29
            # .25 -> 26
            # .4 -> 25
            # .6 -> 23
            for threshold in [.15, .25, .4, .6]:
                myDir = saveDir + "0dot" + ("%.2f_" % threshold)[2:]
                pcaCheck(data, names, 3, True, myDir, threshold)
                if not(skipBlockingSteps):
                    print "PCA3 for data set %s, preprocessing w/ threshold %.2f" % (dataName, threshold)
                    pca3Viz(data, names, test, testNames, True, False, myDir, threshold)
                    pca3Viz(data, names, test, testNames, False, False, myDir, threshold)
                pca2Viz(data, names, test, testNames, False, True, myDir, threshold, False)
                pca2Viz(data, names, test, testNames, True, True, myDir, threshold, False)
                # 1/3 versions
                pca2Viz(data, names, test, testNames, True, True, myDir, threshold, True)
                pca2Viz(data, names, test, testNames, False, True, myDir, threshold, True)

                if verbose:
                    print "  Done with visualizations for %s, (threshold %.2f)" % (dataName, threshold)
        if verbose:
            print "Done with threshold visualizations"

        dataSets = [
        DATA_SETS.ILIAD_ODYSSEY,
        DATA_SETS.CLASSIFY_6,
        DATA_SETS.HOMER_HESIOD_AND_THE_HYMNS_ALL
        ]
        for dataName in dataSets:
            data, names, test, testNames = getData(dataName)
            saveDir = utils.getFinalResultsOutputDir(dataName)
            # PCA report to let us know why things end up where they are
            pcaCheck(data, names, 3, True, saveDir, 0)
            #pca3Viz(data, names, test, testNames, True, False, saveDir, 0)
            #pca2Viz(data, names, test, testNames, True, True, saveDir, 0, False)
            if verbose:
                print "Done with pca rundown for %s" % dataName
        if verbose:
            print "Done with pca rundowns"


    if (True):
        # Analyze how good classifiers are at detecting iliad/odyssey stuff
        dataName = DATA_SETS.CLASSIFY_6
        data, names, test, testNames = getData(dataName)
        saveDir = utils.getFinalResultsOutputDir(dataName)
        r1 = classifySpecialCrossfold(data, names, test, testNames, True, True, saveDir)
        if verbose:
            print "  Special crossfold done"
        r2 = classifyOneHeldOut(data, names, test, testNames, True, True, saveDir)
        if verbose:
            print "  Hold one out done"
        r3 = classifyIOHeldOut(data, names, test, testNames, True, True, saveDir)
        if verbose:
            print "  Iliad/Odyssey held out done"

        buildResultLatexTables(r1, r2, r3, saveDir)

        if verbose:
            print "  Iliad/Odyssey self compare starting"
        dataName = DATA_SETS.ILIAD_ODYSSEY
        data, names, test, testNames = getData(dataName)
        saveDir = utils.getFinalResultsOutputDir(dataName)
        crossValidateClassifiers(data, names, test, testNames, True, True, saveDir)

        if verbose:
            print "  Iliad/Odyssey self compare done."
            print "  Dionysiaca self compare starting"


        dataName = DATA_SETS.DIONYSIACA_SPLIT
        data, names, test, testNames = getData(dataName)
        saveDir = utils.getFinalResultsOutputDir(dataName)
        crossValidateClassifiers(data, names, test, testNames, True, True, saveDir)
        if verbose:
            print "  Dionysiaca self compare done."
            print "  Dionysiaca/Fall of Troy self compare starting"


        dataName = DATA_SETS.AUTHORS_SPLIT
        data, names, test, testNames = getData(dataName)
        saveDir = utils.getFinalResultsOutputDir(dataName)
        crossValidateClassifiers(data, names, test, testNames, True, True, saveDir)
        if verbose:
            print "  Dionysiaca/Fall of Troy self compare done."
