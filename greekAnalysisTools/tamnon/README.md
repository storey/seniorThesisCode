# Tamnon
This folder contains the code for Tamnon, a rules-based dialect analyzer for ancient Greek texts (currently it only analyzes Ionic vs. Aeolic (with some archaic "Homeric" features like 2nd declension genitive in -oio recognized as well).

For the previous version of Tamnon, for Attic/Doric differentiation, [see here](https://github.com/storey/tamnon).

The files are:
- *process.py* provides the public interfaces for running Tamnon on a given text.
- *core.py* contains the core code used to analyze texts.
- *rules.py* contains the list of rules used.
- *utils.py* contains constants and utility functions.
- *getTestTorms.py* downloads the information needed for testing the rules.
- *testRules.py* is used to download texts from Perseus.
