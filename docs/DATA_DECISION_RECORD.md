# Public Research Dataset Decision (M0)

- Dataset and version: PhysioNet/Computing in Cardiology Challenge 2019, v1.0.0; training sets A and B.
- Access and license: Public access, Creative Commons Attribution 4.0 International. Local research/hackathon use is permitted subject to attribution; no credentials or data-use agreement are required on the dataset page. Preserve the downloaded license and checksum metadata.
- Population: ICU stays; not adult general medical/surgical ward observations.
- Inclusion: Each available training patient file with a valid hourly `SepsisLabel` column.
- Exclusion: Empty/malformed records; after the first positive label, all follow-up is excluded to avoid learning established sepsis. No file rows are copied to generated reports.
- Outcome and horizon: Challenge `SepsisLabel`, the challenge-defined onset window six hours before clinical sepsis onset. This is not the G One deterioration outcome.
- Features and cadence: Numeric Challenge variables at six-hour landmarks; current measurements and trailing six-record summaries for available vital signs. Only records at or before each prediction landmark are used.
- Split and pre-result criteria: Deterministic 70/15/15 patient-grouped stratified train/validation/test split (seed 1729); no patient file may cross a split. Compare logistic regression and histogram gradient boosting by validation AUPRC; inspect test once after choosing the model. Report discrimination, Brier score, and test sensitivity/PPV at a threshold selected on validation for an exploratory 80% sensitivity target. Require at least 100 sepsis-positive patients in each split; otherwise stop and report the split as underpowered. No clinical acceptance threshold is asserted.
- Mismatch and mitigation: The trained candidate is explicitly ICU sepsis research only. It must never be loaded into `models/active`, drive NEWS2, emit ward deterioration claims, or be described as clinical validation. G One's NEWS2 workflow remains the only operational scoring path.
- Data handling: Full downloaded patient-level files remain under ignored `.tools/physionet-challenge-2019` and are not committed. The aggregate metrics and attributed, inactive research model are packaged separately in `models/research/physionet-challenge-2019-sepsis`; the model is not in `models/active`.
- Verified split counts: train 28,235 patients (2,052 positive), validation 6,050 (440 positive), test 6,051 (440 positive); zero overlap. The predeclared 100-positive-per-split minimum passed.
- Attribution: Reyna et al., “Early Prediction of Sepsis from Clinical Data: The PhysioNet/Computing in Cardiology Challenge 2019,” v1.0.0, PhysioNet, doi:10.13026/v64v-d857.
