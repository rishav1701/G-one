# PhysioNet Challenge 2019 Research Run

A separate ICU sepsis research model was trained for the hackathon using PhysioNet Challenge 2019 v1.0.0 (CC BY 4.0). The recursive public download is in ignored `.tools/physionet-challenge-2019/`: 40,496 files totaling 1,713,740,738 bytes. This includes the 40,336 patient files in training sets A and B plus the supplementary Challenge files. Only training sets A and B were used for model fitting; none of the dataset files are committed.

## Reproduce

On Windows with the project’s isolated Python runtime:

```powershell
.tools/python311/python.exe scripts/download_physionet2019.py
.tools/python311/python.exe backend/ml/train_physionet2019.py
.tools/python311/python.exe scripts/package_physionet_candidate.py
```

The training script writes its run outputs under ignored `.tools/physionet-challenge-2019/candidate/`. The reviewed hackathon artifact and aggregate-only metrics are in `models/research/physionet-challenge-2019-sepsis/`. Keep it there: G One loads only accepted artifacts from `models/active`; NEWS2 remains the only operational risk score.

## Result summary

The model was selected on validation AUPRC using a deterministic patient-grouped stratified 70/15/15 split (seed 1729). The split was checked for zero patient overlap and at least 100 positive patients per partition. Test AUROC was 0.834 and AUPRC was 0.110 at 0.962% positive landmarks. At a validation-selected threshold targeting at least 80% sensitivity, test sensitivity was 81.4%, specificity 72.1%, and PPV 2.75%. The low PPV and uncalibrated probabilities make this an educational research result only.

See the artifact’s model card for attribution, target definition, cohort counts, metric details, and limitations. No clinical acceptance criteria were met or claimed. The artifact is not compatible with G One’s ward NEWS2 model contract and must not be activated.
