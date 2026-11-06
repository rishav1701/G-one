# Clinical methodology: NEWS2 demonstration

## Intended use and limits

G One calculates a NEWS2 demonstration score from entered or simulated adult ward observations. It supports clinical judgement and does not diagnose, prescribe, or replace local escalation policy. The implementation is not clinically validated and is not for clinical use.

**The NEWS2 table and implementation must be verified by a qualified clinician against the official chart before any clinical use.** The G One project reference is the Royal College of Physicians (RCP), *National Early Warning Score (NEWS) 2: Standardising the assessment of acute-illness severity in the NHS*, updated report, London: RCP, 2017. The official chart is available on the [RCP NEWS2 resource page](https://www.rcp.ac.uk/resources/national-early-warning-score-news-2/).

The supplied bands were compared with RCP Chart 1. No threshold difference was found. The RCP chart confirms the respiration, Scale 1 and Scale 2 oxygen saturation, oxygen, systolic pressure, pulse, consciousness, and temperature bands implemented here. This comparison is a specification check, not clinical approval.

## Scoring

Each available parameter is scored with version `NEWS2-RCP-2017-v1`:

| Parameter | Score bands |
|---|---|
| Respiration rate / minute | ≤8: 3; 9–11: 1; 12–20: 0; 21–24: 2; ≥25: 3 |
| SpO₂ Scale 1 | ≤91: 3; 92–93: 2; 94–95: 1; ≥96: 0 |
| SpO₂ Scale 2 | ≤83: 3; 84–85: 2; 86–87: 1; 88–92: 0; ≥93 on air: 0; 93–94 on oxygen: 1; 95–96 on oxygen: 2; ≥97 on oxygen: 3 |
| Supplemental oxygen | Oxygen: 2; air: 0 |
| Systolic pressure (mmHg) | ≤90: 3; 91–100: 2; 101–110: 1; 111–219: 0; ≥220: 3 |
| Pulse / minute | ≤40: 3; 41–50: 1; 51–90: 0; 91–110: 1; 111–130: 2; ≥131: 3 |
| Consciousness | Alert: 0; new confusion, Voice, Pain, or Unresponsive: 3 |
| Temperature (°C) | ≤35.0: 3; 35.1–36.0: 1; 36.1–38.0: 0; 38.1–39.0: 1; ≥39.1: 2 |

Totals map to HIGH at 7 or more, MEDIUM at 5–6, LOW_MEDIUM at 0–4 with any parameter score of 3, and LOW at 0–4 without a parameter score of 3. MEDIUM takes precedence over LOW_MEDIUM when the total is at least 5.

## Missing and stale observations

Missing measurements are omitted; they are never imputed as normal. The assessment stores the number of scored parameters out of seven and the available parameter scores. If the partial total is at least 5, the resulting MEDIUM or HIGH level stands. A partial total below 5 is LOW_MEDIUM if any parameter scores 3; otherwise it is INCOMPLETE (shown as “Assessment limited”), never LOW. No valid observation produces NO_DATA. When the newest valid observation is older than the configured stale window, the state is STALE. The current technical default stale window is 24 hours (`OBSERVATION_STALE_HOURS`).

For each parameter, the service selects the most recent valid measurement within the stale window. Accepted observations remain immutable in the application API; out-of-order measurements are retained and do not replace a newer parameter value. Each observation carries its own measurement timestamp.

## Input validation

Inputs use integer precision for respiration, SpO₂, systolic pressure, and pulse, and one decimal place for temperature. Technical hard-rejection defaults are respiration 1–100/minute, SpO₂ 50–100%, systolic pressure 30–300 mmHg, pulse 20–300/minute, and temperature 25.0–45.0 °C. These are configurable with the `OBSERVATION_HARD_LIMITS` JSON environment setting; they are engineering bounds, not clinical thresholds.

Configurable plausibility-warning defaults are respiration 9–24/minute, SpO₂ 94–100%, systolic pressure 101–219 mmHg, pulse 51–110/minute, and temperature 36.1–38.0 °C (`OBSERVATION_PLAUSIBILITY_LIMITS`). These are technical review cues only and do not change scoring or reject a measurement. Rejections record a fixed reason code, source, and time without storing rejected values or free text.

## Explanation and persistence

An assessment stores its scoring version, input observation IDs, SpO₂ scale, per-parameter scores, completeness, level, total, computation timestamp, and deterministic score breakdown. Recomputing from those stored observation IDs and the recorded scale reproduces the same result. No model output contributes to this score or its explanation.

## Clinical review status

Clinician verification is pending. Local escalation pathways, training, prospective validation, and suitability for any regulated or clinical deployment are outside this demonstration.
