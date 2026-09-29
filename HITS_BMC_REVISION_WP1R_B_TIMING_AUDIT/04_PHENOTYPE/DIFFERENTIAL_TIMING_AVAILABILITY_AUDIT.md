# Differential Timing Availability Audit

## Clinical Episode Timing

Defensible index-episode timing is unavailable in both phenotype groups: AMI 0/453; non-AMI CAD 0/1,367. Direct, unique-stay-window, and partial clinical linkage are each zero in both groups. Thus there is no measured differential availability of *verified* clinical timing; there is also no timing basis for adjustment.

## Raw Field Availability

| Field | AMI | Non-AMI CAD | Absolute difference |
|---|---:|---:|---:|
| Selected CBC timestamp | 453/453 (100.00%) | 1,367/1,367 (100.00%) | 0.00 percentage points |
| CBC timestamp + listed admission date | 33/453 (7.28%) | 97/1,367 (7.10%) | 0.18 percentage points |
| Fibrinogen timestamp | 427/453 (94.26%) | 1,280/1,367 (93.64%) | 0.62 percentage points |
| Fibrinogen and CBC timestamps | 427/453 (94.26%) | 1,280/1,367 (93.64%) | 0.62 percentage points |

These are field-availability comparisons only. Neither availability nor a close/same-day timestamp proves the result belongs to the index CAG hospitalization. No hypothesis test was run and no arbitrary imbalance threshold was imposed. `POTENTIAL_DIFFERENTIAL_TIMING_AVAILABILITY` for defensible index linkage: **NO; both groups have 0 linked timing**. Availability of unlinked date fields is reported descriptively and remains a limitation.

## Admission-Date Comparisons

Among CBC/admission-date pairs, AMI: 20/33 CBC dates precede, 11/33 share the calendar date, and 2/33 follow the listed admission date. Non-AMI CAD: 79/97 precede, 8/97 share the date, and 10/97 follow. These comparisons are date-level only; `admission_date` is sparse and not verified as the index CAG admission. They must not be read as pre-admission or same-hospitalization rates.
