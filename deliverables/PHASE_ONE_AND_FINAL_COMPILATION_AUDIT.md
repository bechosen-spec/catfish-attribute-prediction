# Project Compilation Audit

Student: Ameh Joseph Junior  
Registration number: PG/MSC/19/89745  
Programme: M.Sc. Computer Science  
Institution: University of Nigeria, Nsukka  
Supervisor: Prof. Collins Udanor  
Repository: https://github.com/bechosen-spec/catfish-attribute-prediction

## Sources used

- `PROJECT MAIN WORK CORRECTED.docx` (original preserved in Downloads)
- `catfish_multitask_colab.ipynb` and its embedded outputs
- `chapter_4_5_materials/` extracted notebook figures, tables and screenshots
- Repository source files, model weights and automated tests

## Evidence decisions

- The notebook's evaluated EfficientNetB0 model is reported as the research model.
- The saved InceptionV3 weights and Streamlit screenshots are reported separately as the local application implementation.
- Image-level and fish-level metrics are labelled separately because 357 images represent 117 independent fish.
- The fish-grouped split is reported: 249/51/57 images and 81/17/19 fish for training/validation/test.
- The zero-fish-overlap and zero-cross-split-exact-duplicate checks are reported.
- Grad-CAM is reported as failed (0/6 successful), not as a successful result.
- Regression is reported as weak and as failing to beat the class-mean baseline.
- No public deployment, database, authentication, prediction history or independent expert-comparison study is claimed.

## Material corrections made

- Expanded the aim to include SL, TL and weight estimation.
- Revised the deployment objective to a verified local implementation.
- Standardized the experimental image size at 224 x 224.
- Standardized biometric terminology as standard length, total length and weight.
- Replaced unsupported MSE wording with the notebook's Huber-loss implementation.
- Replaced unsupported separate HTML/CSS/JavaScript and database claims with the verified Streamlit architecture.
- Added preliminary pages, abstract, headings, contents/list fields, Chapters Four and Five, references and appendices.

## Remaining submission checks

- Several recent empirical sources cited in the supplied Chapter Two do not contain enough bibliographic information in the manuscript. Their source copies should be checked before institutional submission; details were not invented.
- Word/LibreOffice should be used to refresh the automatic table of contents, list of tables and list of figures.
- Signature and approval pages remain unsigned.
- The original dataset ZIP/spreadsheets, EfficientNetB0 checkpoint and fitted scalers should be archived if available.
