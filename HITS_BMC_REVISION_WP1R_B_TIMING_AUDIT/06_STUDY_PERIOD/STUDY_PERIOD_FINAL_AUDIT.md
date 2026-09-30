# Study Period: Final Audit

**Final status: `AUTHOR_CONFIRMED_BUT_NOT_MACHINE_VERIFIED`.**

The author confirms that eligibility was based on patients undergoing coronary angiography in the Coronary Heart Disease Unit I database at the First Affiliated Hospital of Xinjiang Medical University during 2020–2026. The local primary filename includes a 20–26 range label, but the recovered mother file has no CAG/procedure date to verify actual eligibility dates. The Scheme C source bundle, field dictionary, source-recovery inventory, and prior lineage package did not provide an extraction query, export note with validated date bounds, raw procedure register, admission/discharge range, or index-angiography field that supports `2020-01-01` through `2026-01-01`.

No CBC year distribution was used to invalidate or machine-verify the cohort period. CBC `test_time` is a laboratory date, not a substitute for angiography date or cohort-entry date. Therefore the period remains author-confirmed only.

Ethics status is separate: `ETHICS_GATE = PASS` based on author-confirmed approval K202602-10 and the Committee-approved waiver; no source documents were reviewed in this timing audit.
