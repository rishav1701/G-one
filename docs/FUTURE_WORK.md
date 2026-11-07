# Future work

G One is a simulated software demonstration, not for clinical use. NEWS2 requires qualified local clinical review before any clinical deployment. The ward-oriented ML feature contract is still fixture-tested; it has not been trained or validated for ward patients.

## Separate ICU research model

A public-data hackathon candidate from PhysioNet Challenge 2019 is packaged at `models/research/physionet-challenge-2019-sepsis/`. It predicts the challenge-defined sepsis label for ICU records, is uncalibrated, had a 2.75% PPV at the exploratory threshold, and is explicitly unaccepted and inactive. It is not compatible with the ward feature contract and must never be promoted to `models/active` or described as a ward deterioration model. Full patient-level source files remain local and ignored under `.tools/physionet-challenge-2019/`.

## Model work still required

- Identify a public or institutionally approved ward cohort that matches G One’s population, measurements, and deterioration outcome before training a ward model.
- Set ward-specific acceptance criteria before viewing held-out test results, then validate patient-level and temporal separation, leakage, calibration, missingness, and subgroup performance.
- Obtain prospective external validation and qualified local clinical review before making clinical claims or considering operational use.
- Promote only a reviewed artifact whose manifest has `acceptance_passed: true` and whose hashes and feature contract verify. A model remains secondary to NEWS2 and must never automatically drive clinical actions.
- Synthetic scenario outcomes remain software-behaviour demonstrations, not clinical performance evidence.

## Product work still open

- Docker Compose startup and clean-clone container packaging remain unverified because the local Docker Desktop engine did not return a server response.
- A qualified clinician must verify NEWS2 thresholds, missing-data behavior, labels, and local escalation language before any clinical use.
- Release-hosted TLS, backups, operational monitoring, and paging integration are outside this local demonstration.
