# Shared Code
This folder contains three main sets of code.

(1) General utility functions and shared constants, stored in *utils.py*

(2) Preprocessing code shared by Odikon and Tamnon:
- *downloadText.py* is used to download texts from Perseus.
- *preprocess.py* cleans the tokens in a text and grabs the associated morphological and lemma information

(3) Postprocessing code for producing results:
- *postprocess.py* does some minor postprocessing of the features extracted by Tamnon and Odikon, then combines their results into a single feature vector for a given text.
- *getResults.py* takes the postprocessed feature vectors and performs our various analyses on them.
