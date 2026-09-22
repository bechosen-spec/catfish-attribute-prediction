# Catfish validation improvement plan

## Decision

Do **not** replace the current production MobileNetV2 gate yet. It remains a
conservative generic-fish safeguard paired with file and image-quality checks.
It is not a catfish recognizer: ImageNet-1K has no `catfish`, `Clarias`, or
`Siluriformes` label. Its available fish labels include `tench`, `goldfish`,
sharks/rays, `barracouta`, `eel`, `coho`, `rock_beauty`, `anemone_fish`,
`sturgeon`, `gar`, `lionfish`, and `puffer`. This label mismatch explains why
the supplied catfish-named images receive bird, insect, reptile, and mollusc
labels rather than a fish label.

## Local evidence

| Asset | Defensible label | Quality result | MobileNetV2 top result | Gate result |
|---|---|---|---|---|
| `sample_inputs/adult_sample.png` | filename says adult; species not independently verified | passes | kite, 17.47% | uncertain |
| `sample_inputs/juvenile_sample.png` | filename says juvenile; species not independently verified | passes | ground beetle, 17.12% | uncertain |
| `sample_inputs/fingerling_sample.png` | filename says fingerling; species not independently verified | mean brightness 251.85, above 247 | not used by gate | rejected |
| Notebook figures / UI screenshots | charts, composites, or generated UI output | not suitable | not evaluated as input photos | excluded |

The repository contains no standalone photographs with source metadata and
independently defensible catfish labels. Therefore there are no valid local
true-positive/false-negative counts for catfish recognition, and no precision,
recall, F1 score, or confusion matrix can be reported for a proposed model.

## Recommended replacement: two-stage local detector + classifier

Build a new, **independent** validator outside the attribute model:

1. Keep the current safe file decoder and quality checks.
2. Use a fish detector to require a fish bounding box with a calibrated score.
3. Run a catfish-vs-other-fish-vs-non-fish classifier on the detected crop.
4. Accept only `catfish` at a threshold chosen on a held-out test set; reject
   or mark uncertain otherwise. Preserve all raw scores and model version.

Detection is preferable to whole-image classification because farm photographs
often include water, hands, nets, containers, or multiple objects. Fish4Knowledge
offers ground-truth material for fish target detection and species recognition,
but its underwater domain must not be assumed to represent catfish farm imagery.
FishNet is a larger benchmark for fish recognition/detection, likewise useful
for transfer learning and negative examples rather than proof of catfish-farm
performance.

## Data acquisition and governance

Create a manifest for every image with: immutable image hash, source URL or
owner consent, licence, taxon label and labeler, capture setting, fish ID/batch,
date, and intended split. iNaturalist supports observation queries, photo-license
filters, research-grade filtering, and taxon filters. Use only records whose
photo licence permits the intended use; retain attribution and the original
licence in the manifest. Do not scrape at high volume: iNaturalist recommends
its data exports/datasets for bulk work.

Target minimum classes:

- catfish: the exact production taxa (for example, *Clarias gariepinus*) across
  fingerling/juvenile/adult stages and capture conditions;
- other fish: at least the visually confusable local aquaculture species;
- non-fish: nets, hands, tanks, feed, water-only scenes, tools, insects, birds,
  and ordinary objects;
- unsafe/poor quality: blur, glare, darkness, empty scenes, corrupt files.

Use fish/batch-grouped splits, never random-image splits: all photos of one fish
or capture event must remain in one split. Deduplicate exact hashes and apply
near-duplicate review before splitting. Reserve a final untouched test set
covering farms, cameras, backgrounds, and lighting not represented in training.

## Evaluation release gate

Before production replacement, publish a locked test manifest and confusion
matrix for (catfish, other fish, non-fish). Report TP, FP, TN, FN, precision,
recall, F1, and confidence intervals where practical. Select the acceptance
threshold based on a predefined false-acceptance limit for non-fish, not on the
same images used to train or tune. Evaluate quality-gate interactions separately.
Compare the candidate with the current gate on precisely the same held-out
images. No accuracy claim should be made until that evaluation exists.

## Sources

- [Fish4Knowledge ground-truth datasets](https://homepages.inf.ed.ac.uk/rbf/Fish4Knowledge/GROUNDTRUTH/)
- [FishNet ICCV 2023 paper](https://openaccess.thecvf.com/content/ICCV2023/papers/Khan_FishNet_A_Large-scale_Dataset_and_Benchmark_for_Fish_Recognition_Detection_ICCV_2023_paper.pdf)
- [iNaturalist API reference](https://www.inaturalist.org/api)
- [iNaturalist developer dataset and licence guidance](https://www.inaturalist.org/pages/developers)
