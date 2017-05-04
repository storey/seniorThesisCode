
# empty class for creating constants
class Constant:
    pass


# constants for metrical feet
FOOT = Constant()
FOOT.DACTYL = "Dactyl"
FOOT.SPONDEE = "Spondee"
FOOT.FINAL = "Final"

APPROACH = Constant()
APPROACH.STUDENT = "version_student"
APPROACH.NATIVE_SPEAKER = "version_native_speaker"
APPROACH.FALLBACK = "version_fallback"

SYL = Constant()
SYL.UNKNOWN = 0
SYL.SHORT = 1
SYL.LONG = 2

VERBOSE = False#True#
VERY_VERBOSE = False
