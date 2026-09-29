import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = new URL("../HITS_BMC_MINOR_REVISION_WP3_FINAL/", import.meta.url).pathname;
const wp2 = new URL("../HITS_BMC_MINOR_REVISION_WP2_TARGETED_ANALYSES/", import.meta.url).pathname;
const workbookPath = root + "03_SUPPLEMENT/Additional_file_2_Revised_Supplementary_Tables.xlsx";

async function csvRows(relativePath) {
  const csvText = await fs.readFile(wp2 + relativePath, "utf8");
  const sourceBook = await Workbook.fromCSV(csvText, { sheetName: "Source" });
  const values = sourceBook.worksheets.getItem("Source").getUsedRange().values;
  const headers = values[0].map((x) => String(x ?? ""));
  return values.slice(1).filter((row) => row.some((x) => x !== null && x !== "")).map((row) =>
    Object.fromEntries(headers.map((header, i) => [header, row[i] ?? ""]))
  );
}

const asNum = (value) => Number(value);
const fmt3 = (value) => asNum(value).toFixed(3);
const fmt4 = (value) => asNum(value).toFixed(4);
const fmt2 = (value) => asNum(value).toFixed(2);
const ci = (row, est, lo, hi) => fmt3(row[est]) + " (" + fmt3(row[lo]) + "-" + fmt3(row[hi]) + ")";
const exact = (rows, fields) => {
  const matches = rows.filter((row) => Object.entries(fields).every(([key, value]) => String(row[key]) === String(value)));
  if (matches.length !== 1) throw new Error("Expected one source row for " + JSON.stringify(fields) + "; got " + matches.length);
  return matches[0];
};
const blankMatrix = (rows, cols) => Array.from({ length: rows }, () => Array(cols).fill(null));
const writeBlock = (sheet, address, values) => { sheet.getRange(address).values = values; };
const styleHeader = (sheet, address) => {
  const range = sheet.getRange(address);
  range.format = {
    fill: "#D9EAF7",
    font: { bold: true, color: "#203040" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
  };
};
const styleNote = (sheet, address) => {
  const range = sheet.getRange(address);
  range.format = { wrapText: true, font: { italic: true, color: "#404040" } };
};
const title = (sheet, address, text) => { sheet.getRange(address).values = [[text]]; };
const columnWidths = (sheet, widths) => {
  for (const [col, width] of Object.entries(widths)) sheet.getRange(col + ":" + col).format.columnWidth = width;
};

const sources = {
  perf: await csvRows("03_PRIMARY_PERFORMANCE/PRIMARY_MODEL_PERFORMANCE_CANONICAL.csv"),
  deltas: await csvRows("03_PRIMARY_PERFORMANCE/PRIMARY_PAIRED_DELTAS_CANONICAL.csv"),
  clinical: await csvRows("04_CLINICAL_INCREMENTAL/CLINICAL_INCREMENTAL_PERFORMANCE_CANONICAL.csv"),
  clinicalMissing: await csvRows("04_CLINICAL_INCREMENTAL/CLINICAL_COVARIATE_MISSINGNESS_FINAL.csv"),
  fbgMissing: await csvRows("05_FIBRINOGEN/FIBRINOGEN_MISSINGNESS_FINAL.csv"),
  traditional: await csvRows("06_TRADITIONAL_INDICES/TRADITIONAL_INDEX_CANONICAL_PERFORMANCE.csv"),
  calibration: await csvRows("08_CALIBRATION/CALIBRATION_CANONICAL_SOURCE.csv"),
  calGroups: await csvRows("08_CALIBRATION/CALIBRATION_GROUP_COUNTS.csv"),
  probability: await csvRows("08_CALIBRATION/PREDICTED_PROBABILITY_SUMMARY.csv"),
  highFlow: await csvRows("10_HIGH_SPECIFICITY/HIGH_SPECIFICITY_FLOW_FINAL.csv"),
  figure5: await csvRows("11_FIGURE5/FIGURE5_FINAL_CI_TABLE.csv"),
  dateAxis: await csvRows("12_TEMPORAL_CONTEXT/DATE_AXIS_SENSITIVITY_FINAL_FACTS.csv"),
};

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const before = (await workbook.inspect({ kind: "sheet", include: "id,name" })).ndjson
  .split("\n").filter(Boolean).map((line) => JSON.parse(line).name);
const expectedSheets = [
  "S1_Variables", "S2_Phenotype", "S3_Missingness", "S4_Indices", "S5_Preprocess",
  "S6_Resampling", "S7_Stability", "S8_Clinical", "S9_Fibrinogen",
  "S10_HighSpecificity", "S11_Temporal", "S12_Simplified", "S13_ModelSpec",
];
if (JSON.stringify(before) !== JSON.stringify(expectedSheets)) throw new Error("Unexpected source workbook sheet structure");

const s3 = workbook.worksheets.getItem("S3_Missingness");
title(s3, "A1", "Supplementary Table S3. Missingness in the primary cohort");
writeBlock(s3, "A3:F3", [["Cohort", "Variable", "Denominator (n)", "Available (n)", "Missing (n)", "Missing (%)"]]);
styleHeader(s3, "A3:F3");
const fbgByGroup = Object.fromEntries(sources.fbgMissing.map((r) => [r.group, r]));
const clinMiss = Object.fromEntries(sources.clinicalMissing.map((r) => [r.group + "|" + r.variable, r]));
const cohortDefs = [
  { key: "overall", label: "Overall", n: 1820, amiN: 453, nonN: 1367 },
  { key: "AMI", label: "Definite AMI", n: 453, amiN: 453, nonN: 0 },
  { key: "non_AMI", label: "Definite non-AMI CAD", n: 1367, amiN: 0, nonN: 1367 },
];
const variables = ["Neutrophils", "Lymphocytes", "Monocytes", "Platelets", "MPV", "RDW", "Hemoglobin", "Fibrinogen", "Age", "Male sex", "Hypertension", "Diabetes", "Smoking (not captured)"];
const rowsS3 = [];
for (const cohort of cohortDefs) {
  for (const variable of variables) {
    let missing = 0;
    let available = cohort.n;
    let pct = 0;
    if (variable === "Fibrinogen") {
      const r = fbgByGroup[cohort.key];
      available = asNum(r.available_n);
      missing = asNum(r.missing_n);
      pct = asNum(r.missing_pct);
    } else if (variable === "Hypertension" || variable === "Diabetes") {
      const key = variable === "Hypertension" ? "hypertension" : "diabetes";
      const r = clinMiss[cohort.key + "|" + key];
      available = asNum(r.available_n);
      missing = asNum(r.missing_n);
      pct = asNum(r.missing_pct);
    } else if (variable === "Smoking (not captured)") {
      available = 0;
      missing = cohort.n;
      pct = 100;
    }
    rowsS3.push([cohort.label, variable, cohort.n, available, missing, Number(pct.toFixed(2))]);
  }
}
s3.getRange("A4:F73").values = blankMatrix(70, 6);
writeBlock(s3, "A4:F42", rowsS3);
s3.getRange("F4:F42").format.numberFormat = "0.00";
styleNote(s3, "A44:F44");
writeBlock(s3, "A44", [["Core-7 measurements and age/sex were complete in the primary cohort. Smoking was not present in the source extract; it is not treated as an observed variable with missing individual values."]]);
columnWidths(s3, { A: 23, B: 23, C: 17, D: 16, E: 15, F: 14 });

const s4 = workbook.worksheets.getItem("S4_Indices");
title(s4, "A1", "Supplementary Table S4. Conventional index performance");
writeBlock(s4, "A3:G3", [["Index", "Formula", "AUC (95% CI)", "N", "AMI (n)", "Brier score", "Role"]]);
const indexRows = sources.traditional.map((r) => [
  r.index, r.formula, ci(r, "AUC", "AUC_CI_lower", "AUC_CI_upper"),
  asNum(r.N), asNum(r.AMI_n), asNum(r.Brier),
  r.index === "PIV" ? "Prespecified primary conventional comparator" : "Supplementary benchmark",
]);
writeBlock(s4, "A4:G10", indexRows);
s4.getRange("C4:C10").format.numberFormat = "@";
s4.getRange("F4:F10").format.numberFormat = "0.000";
styleHeader(s4, "A3:G3");
styleNote(s4, "A12:G12");
writeBlock(s4, "A12", [["All estimates use the frozen repeated nested-OOF outputs and absolute counts. PIV was prespecified as the primary comparator; no new index hypothesis tests were performed."]]);
columnWidths(s4, { A: 13, B: 31, C: 23, D: 11, E: 12, F: 15, G: 38 });

const s6 = workbook.worksheets.getItem("S6_Resampling");
title(s6, "A1", "Supplementary Table S6. Validation and calibration details");
writeBlock(s6, "A3:B3", [["Specification", "Value"]]);
const specs = [
  ["Primary outcome", "Definite AMI vs definite non-AMI CAD discharge-text phenotype"],
  ["Primary cohort", "N=1,820; AMI=453; non-AMI CAD=1,367"],
  ["Core-7 predictors", "Neutrophils, lymphocytes, monocytes, platelets, MPV, RDW, hemoglobin"],
  ["Enhanced model", "Core-7 plus fibrinogen"],
  ["Outer validation", "Stratified 5-fold cross-validation repeated 10 times"],
  ["Inner tuning", "5-fold cross-validation within each outer training set"],
  ["Prediction aggregation", "Arithmetic mean of each patient's 10 held-out probabilities"],
  ["Paired comparisons", "Same outer partitions and same-patient mean held-out predictions where applicable"],
  ["Preprocessing", "Imputation, transformation, centering/scaling, and tuning estimated within training folds only"],
  ["Elastic-net grid", "C: 0.10, 1.00, 10.00; mixing parameter: 0.25, 0.50, 0.75"],
  ["Bootstrap interval", "1,000 patient resamples of fixed mean predictions and outcomes; no model refits"],
  ["Interval scope", "Conditional on the fixed cross-validated predictions; excludes full model-development uncertainty"],
  ["Clinical baseline", "Age, sex, hypertension, diabetes; smoking unavailable"],
  ["Outcome timing", "Patient-level AMI phenotype discrimination; no uniform prospective index time"],
];
writeBlock(s6, "A4:B17", specs);
writeBlock(s6, "A19:F19", [["Calibration group counts and observed/predicted values", null, null, null, null, null]]);
styleHeader(s6, "A19:F19");
writeBlock(s6, "A20:F20", [["Model", "Quantile group", "N", "AMI (n)", "Mean predicted probability", "Observed AMI proportion"]]);
styleHeader(s6, "A20:F20");
const calRows = sources.calibration.filter((r) =>
  (r.model === "Core-7" && r.analysis_id === "primary_core") ||
  (r.model === "Enhanced (full cohort)" && r.analysis_id === "primary_enhanced_imputed")
);
const groupRows = calRows.map((r) => [
  r.model, asNum(r.bin), asNum(r.N), asNum(r.AMI_n), asNum(r.mean_predicted), asNum(r.observed_rate),
]);
writeBlock(s6, "A21:F40", groupRows);
s6.getRange("E21:F40").format.numberFormat = "0.000";
writeBlock(s6, "A42:J42", [["Predicted-probability distribution summary", null, null, null, null, null, null, null, null, null]]);
styleHeader(s6, "A42:J42");
writeBlock(s6, "A43:J43", [["Model", "N", "AMI (n)", "Mean", "SD", "Minimum", "25th percentile", "Median", "75th percentile", "Maximum"]]);
styleHeader(s6, "A43:J43");
const probabilityRows = sources.probability.filter((r) =>
  (r.model === "Core-7" && r.analysis_id === "primary_core") ||
  (r.model === "Enhanced (full cohort)" && r.analysis_id === "primary_enhanced_imputed")
);
writeBlock(s6, "A44:J45", probabilityRows.map((r) => [
  r.model, asNum(r.N), asNum(r.AMI_n), asNum(r.mean_probability), asNum(r.sd_probability),
  asNum(r.min_probability), asNum(r.p25_probability), asNum(r.median_probability),
  asNum(r.p75_probability), asNum(r.max_probability),
]));
s6.getRange("D44:J45").format.numberFormat = "0.000";
styleHeader(s6, "A3:B3");
styleNote(s6, "A47:J47");
writeBlock(s6, "A47", [["Calibration groups and summaries are descriptive summaries of frozen patient-level mean held-out predictions; they are not recalculated model estimates."]]);
columnWidths(s6, { A: 34, B: 45, C: 13, D: 14, E: 24, F: 22, G: 17, H: 15, I: 17, J: 15 });

const s8 = workbook.worksheets.getItem("S8_Clinical");
title(s8, "A1", "Supplementary Table S8. Same-sample clinical incremental comparison");
writeBlock(s8, "A8:H22", blankMatrix(15, 8));
writeBlock(s8, "H3:H7", blankMatrix(5, 1));
writeBlock(s8, "A3:G3", [["Model", "N", "AMI (n)", "AUC (95% CI)", "Brier score", "Calibration intercept", "Calibration slope"]]);
const clinCC = sources.clinical.filter((r) =>
  r.record_type === "model_performance" && r.cohort_version === "fibrinogen_complete_case_1705"
);
const clinOrder = ["Clinical only", "Clinical + PIV", "Clinical + Core-7", "Clinical + Enhanced"];
writeBlock(s8, "A4:G7", clinOrder.map((name) => {
  const r = exact(clinCC, { model: name });
  return [name, asNum(r.N), asNum(r.AMI_n), ci(r, "AUC", "AUC_CI_lower", "AUC_CI_upper"),
    asNum(r.Brier), asNum(r.calibration_intercept), asNum(r.calibration_slope)];
}));
title(s8, "A9", "Paired AUC differences on the same 1,705 patients");
writeBlock(s8, "A10:E10", [["Comparison", "ΔAUC", "95% CI", "Common N", "Fold pairing"]]);
styleHeader(s8, "A10:E10");
const clinicalComparisons = [
  ["Fibrinogen-complete cohort Clinical_Plus_PIV minus Clinical", "Clinical + PIV vs Clinical"],
  ["Fibrinogen-complete cohort Clinical_Plus_Core minus Clinical", "Clinical + Core-7 vs Clinical"],
  ["Fibrinogen-complete cohort Clinical_Plus_Enhanced minus Clinical", "Clinical + Enhanced vs Clinical"],
  ["Fibrinogen-complete cohort Clinical_Plus_Core minus Clinical_Plus_PIV", "Clinical + Core-7 vs Clinical + PIV"],
  ["Fibrinogen-complete cohort Clinical_Plus_Enhanced minus Clinical_Plus_PIV", "Clinical + Enhanced vs Clinical + PIV"],
  ["Fibrinogen-complete cohort Clinical_Plus_Enhanced minus Clinical_Plus_Core", "Clinical + Enhanced vs Clinical + Core-7"],
];
writeBlock(s8, "A11:E16", clinicalComparisons.map(([key, label]) => {
  const r = exact(sources.deltas, { comparison: key });
  return [label, fmt4(r.delta_auc_a_minus_b),
    fmt4(r.delta_auc_ci_lower) + "-" + fmt4(r.delta_auc_ci_upper), asNum(r.n_common), r.outer_fold_identity];
}));
s8.getRange("E4:G7").format.numberFormat = "0.000";
s8.getRange("B11:B16").format.numberFormat = "0.0000";
styleHeader(s8, "A3:G3");
styleNote(s8, "A18:G18");
writeBlock(s8, "A18", [["Clinical variables were age, sex, hypertension, and diabetes; hypertension and diabetes were imputed using training-fold medians. Smoking was unavailable. All four models use the same complete-case cohort and validation partitions."]]);
columnWidths(s8, { A: 42, B: 13, C: 12, D: 24, E: 15, F: 21, G: 20, H: 18 });

const s9 = workbook.worksheets.getItem("S9_Fibrinogen");
title(s9, "A1", "Supplementary Table S9. Fibrinogen availability and complete-case comparison");
s9.getRange("A3:H20").values = blankMatrix(18, 8);
writeBlock(s9, "A3:F3", [["Group", "Analysis N", "Available", "Missing", "Missing (%)", "AMI / non-AMI complete"]]);
styleHeader(s9, "A3:F3");
const missRows = ["overall", "AMI", "non_AMI"].map((group) => exact(sources.fbgMissing, { group }));
writeBlock(s9, "A4:F6", missRows.map((r) => [
  r.group === "non_AMI" ? "Definite non-AMI CAD" : r.group === "AMI" ? "Definite AMI" : "Overall",
  asNum(r.analysis_n), asNum(r.available_n), asNum(r.missing_n), asNum(r.missing_pct),
  r.group === "AMI" ? "426 AMI / 1,279 non-AMI overall complete-case" : "",
]));
const perfCoreCC = exact(sources.perf, { analysis_id: "primary_fbg_complete_case", model: "Core-7" });
const perfEnhCC = exact(sources.perf, { analysis_id: "primary_fbg_complete_case", model: "Enhanced" });
const fbgDelta = exact(sources.deltas, { comparison: "Primary Fibrinogen complete-case Enhanced minus Core" });
writeBlock(s9, "A9:H9", [["Complete-case paired comparison", "N", "AMI", "Non-AMI", "Core-7 AUC (95% CI)", "Enhanced AUC (95% CI)", "ΔAUC (95% CI)", "ΔBrier (Enhanced - Core-7)"]]);
styleHeader(s9, "A9:H9");
writeBlock(s9, "A10:H10", [[
  "Enhanced vs Core-7; same patients/folds", asNum(perfEnhCC.N), asNum(perfEnhCC.AMI_n), asNum(perfEnhCC.non_AMI_n),
  ci(perfCoreCC, "AUC", "AUC_CI_lower", "AUC_CI_upper"),
  ci(perfEnhCC, "AUC", "AUC_CI_lower", "AUC_CI_upper"),
  fmt3(fbgDelta.delta_auc_a_minus_b) + " (" + fmt3(fbgDelta.delta_auc_ci_lower) + "-" + fmt3(fbgDelta.delta_auc_ci_upper) + ")",
  asNum(fbgDelta.brier_delta_a_minus_b),
]]);
styleNote(s9, "A12:H12");
writeBlock(s9, "A12", [["All paired estimates use identical complete-case patients and identical outer-fold partitions; no fibrinogen imputation was used in this comparison."]]);
columnWidths(s9, { A: 45, B: 14, C: 13, D: 13, E: 25, F: 27, G: 24, H: 27 });

const s10 = workbook.worksheets.getItem("S10_HighSpecificity");
title(s10, "A1", "Supplementary Table S10. High-specificity phenotype comparison");
s10.getRange("A3:H10").values = blankMatrix(8, 8);
writeBlock(s10, "A3:E3", [["Model", "N", "AMI (n)", "Strict controls (n)", "AUC (95% CI)"]]);
styleHeader(s10, "A3:E3");
const hsModels = ["Core-7", "Enhanced", "PIV"];
writeBlock(s10, "A4:E6", hsModels.map((model) => {
  const r = exact(sources.figure5, { analysis: "High-specificity phenotype", model });
  return [model, asNum(r.N), 138, 288, ci(r, "AUC", "CI_lower", "CI_upper")];
}));
styleNote(s10, "A8:H8");
writeBlock(s10, "A8", [["The 138 AMI records met the frozen strict discharge-diagnosis text criteria; 40 later-group AMI records did not. These 40 were not adjudicated as misclassifications. The comparison is text-based, not independent clinical adjudication."]]);
columnWidths(s10, { A: 28, B: 13, C: 14, D: 22, E: 28 });

const s11 = workbook.worksheets.getItem("S11_Temporal");
title(s11, "A1", "Supplementary Table S11. Date-axis and phenotype sensitivity analyses");
writeBlock(s11, "G3:H12", blankMatrix(10, 2));
writeBlock(s11, "A13:H16", blankMatrix(4, 8));
writeBlock(s11, "A21:D22", blankMatrix(2, 4));
writeBlock(s11, "A3:F3", [["Analysis", "N", "AMI (n)", "Controls (n)", "Model", "AUC (95% CI)"]]);
styleHeader(s11, "A3:F3");
const groups = [
  { analysis: "Symmetric +/-182-day guard-band", label: "Exploratory deidentified date-axis: later group", N: 548, AMI: 178, controls: 370 },
  { analysis: "High-specificity phenotype", label: "High-specificity phenotype comparison", N: 426, AMI: 138, controls: 288 },
  { analysis: "Conservative +/-365-day buffer", label: "Conservative +/-365-day date-axis sensitivity", N: 361, AMI: "Not reported", controls: "Not reported" },
];
const sensRows = [];
for (const group of groups) {
  for (const model of ["PIV", "Core-7", "Enhanced"]) {
    const r = exact(sources.figure5, { analysis: group.analysis, model });
    sensRows.push([group.label, group.N, group.AMI, group.controls, model, ci(r, "AUC", "CI_lower", "CI_upper")]);
  }
}
writeBlock(s11, "A4:F12", sensRows);
styleNote(s11, "A14:H14");
writeBlock(s11, "A14", [["The conservative +/-365-day output supplies total N and model AUCs/intervals but not an approved AMI/control decomposition; none is inferred here. Date-axis analyses are not formal temporal validation because selected measurement dates were not uniformly linked to the index angiography hospitalization."]]);
title(s11, "A17", "Paired AUC comparison available from the date-axis source");
writeBlock(s11, "A19:D19", [["Analysis", "N", "Comparison", "ΔAUC (95% CI)"]]);
styleHeader(s11, "A19:D19");
const later = exact(sources.dateAxis, { stage: "later" });
writeBlock(s11, "A20:D20", [[
  "Exploratory deidentified date-axis: later group", asNum(later.N), "Core-7 minus PIV",
  fmt3(later.Core_minus_PIV_delta_AUC) + " (" + fmt3(later.delta_CI_lower) + "-" + fmt3(later.delta_CI_upper) + ")",
]]);
writeBlock(s11, "A21:D22", blankMatrix(2, 4));
columnWidths(s11, { A: 45, B: 14, C: 18, D: 22, E: 22, F: 26, G: 18, H: 18 });

workbook.recalculate();
const previews = ["S3_Missingness", "S4_Indices", "S6_Resampling", "S8_Clinical", "S9_Fibrinogen", "S10_HighSpecificity", "S11_Temporal"];
for (const sheetName of previews) {
  const image = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile("/tmp/" + sheetName + "_wp3_after.png", new Uint8Array(await image.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(workbookPath);
const verified = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const after = (await verified.inspect({ kind: "sheet", include: "id,name" })).ndjson
  .split("\n").filter(Boolean).map((line) => JSON.parse(line).name);
if (JSON.stringify(after) !== JSON.stringify(expectedSheets)) throw new Error("Workbook sheet structure changed unexpectedly");
const checkS8 = verified.worksheets.getItem("S8_Clinical").getRange("A3:E16").values;
if (Number(checkS8[1][1]) !== 1705 || Number(checkS8[1][2]) !== 426) throw new Error("S8 complete-case cohort verification failed");
const checkS10 = verified.worksheets.getItem("S10_HighSpecificity").getRange("A4:E6").values;
if (checkS10.some((r) => Number(r[1]) !== 426 || Number(r[2]) !== 138 || Number(r[3]) !== 288)) throw new Error("S10 cohort verification failed");
const checkS3 = verified.worksheets.getItem("S3_Missingness").getRange("A4:F42").values;
if (checkS3.length !== 39 || checkS3.some((r) => !r[1])) throw new Error("S3 missingness rows failed");
const checkS4 = verified.worksheets.getItem("S4_Indices").getRange("A4:G10").values;
if (checkS4.length !== 7 || checkS4.some((r, i) =>
  r[0] !== sources.traditional[i].index ||
  String(r[2]) !== ci(sources.traditional[i], "AUC", "AUC_CI_lower", "AUC_CI_upper") ||
  Math.abs(Number(r[5]) - asNum(sources.traditional[i].Brier)) > 1e-12
)) throw new Error("S4 index estimates differ from the approved source");
const checkS6 = verified.worksheets.getItem("S6_Resampling").getRange("A21:F40").values;
const sourceCalRows = sources.calibration.filter((r) =>
  (r.model === "Core-7" && r.analysis_id === "primary_core") ||
  (r.model === "Enhanced (full cohort)" && r.analysis_id === "primary_enhanced_imputed")
);
if (checkS6.length !== 20 || checkS6.some((r, i) =>
  r[0] !== sourceCalRows[i].model || Number(r[1]) !== asNum(sourceCalRows[i].bin) ||
  Number(r[2]) !== asNum(sourceCalRows[i].N) || Number(r[3]) !== asNum(sourceCalRows[i].AMI_n) ||
  Math.abs(Number(r[4]) - asNum(sourceCalRows[i].mean_predicted)) > 1e-12 ||
  Math.abs(Number(r[5]) - asNum(sourceCalRows[i].observed_rate)) > 1e-12
)) throw new Error("S6 calibration values differ from the approved source");
const checkS8Models = verified.worksheets.getItem("S8_Clinical").getRange("A4:G7").values;
if (checkS8Models.length !== 4 || checkS8Models.some((r) => Number(r[1]) !== 1705 || Number(r[2]) !== 426)) {
  throw new Error("S8 same-sample model rows failed");
}
if (checkS8Models.some((r, i) => {
  const source = exact(clinCC, { model: clinOrder[i] });
  return String(r[3]) !== ci(source, "AUC", "AUC_CI_lower", "AUC_CI_upper") ||
    Math.abs(Number(r[4]) - asNum(source.Brier)) > 1e-12 ||
    Math.abs(Number(r[5]) - asNum(source.calibration_intercept)) > 1e-12 ||
    Math.abs(Number(r[6]) - asNum(source.calibration_slope)) > 1e-12;
})) throw new Error("S8 performance values differ from the approved source");
const checkS8Deltas = verified.worksheets.getItem("S8_Clinical").getRange("A11:E16").values;
if (checkS8Deltas.length !== 6 || checkS8Deltas.some((r) => Number(r[3]) !== 1705)) throw new Error("S8 paired comparisons failed");
if (checkS8Deltas.some((r, i) => {
  const source = exact(sources.deltas, { comparison: clinicalComparisons[i][0] });
  const expectedCI = fmt4(source.delta_auc_ci_lower) + "-" + fmt4(source.delta_auc_ci_upper);
  return Math.abs(Number(r[1]) - asNum(source.delta_auc_a_minus_b)) > 0.000051 || String(r[2]) !== expectedCI;
})) throw new Error("S8 paired AUC differences differ from the approved source");
const checkS9 = verified.worksheets.getItem("S9_Fibrinogen").getRange("A10:H10").values[0];
if (Number(checkS9[1]) !== 1705 || Number(checkS9[2]) !== 426 || Number(checkS9[3]) !== 1279) {
  throw new Error("S9 complete-case cohort failed");
}
const sourceCoreCC = exact(sources.perf, { analysis_id: "primary_fbg_complete_case", model: "Core-7" });
const sourceEnhCC = exact(sources.perf, { analysis_id: "primary_fbg_complete_case", model: "Enhanced" });
const sourceFbgDelta = exact(sources.deltas, { comparison: "Primary Fibrinogen complete-case Enhanced minus Core" });
if (String(checkS9[4]) !== ci(sourceCoreCC, "AUC", "AUC_CI_lower", "AUC_CI_upper") ||
    String(checkS9[5]) !== ci(sourceEnhCC, "AUC", "AUC_CI_lower", "AUC_CI_upper") ||
    String(checkS9[6]) !== fmt3(sourceFbgDelta.delta_auc_a_minus_b) + " (" +
      fmt3(sourceFbgDelta.delta_auc_ci_lower) + "-" + fmt3(sourceFbgDelta.delta_auc_ci_upper) + ")") {
  throw new Error("S9 fibrinogen performance values differ from the approved source");
}
const checkS11 = verified.worksheets.getItem("S11_Temporal").getRange("A4:F12").values;
if (checkS11.length !== 9 || Number(checkS11[0][1]) !== 548 || Number(checkS11[3][1]) !== 426 ||
    Number(checkS11[6][1]) !== 361 || !String(checkS11[6][2]).includes("Not reported") ||
    !String(checkS11[6][3]).includes("Not reported")) {
  throw new Error("S11 date-axis/phenotype rows failed");
}
if (checkS11.some((r, i) => {
  const group = groups[Math.floor(i / 3)];
  const model = ["PIV", "Core-7", "Enhanced"][i % 3];
  const source = exact(sources.figure5, { analysis: group.analysis, model });
  return String(r[5]) !== ci(source, "AUC", "CI_lower", "CI_upper");
})) throw new Error("S11 sensitivity estimates differ from the approved source");
const checks = {
  workbookPath,
  worksheets: after,
  checks: {
    S3_missingness_rows: checkS3.length,
    S4_traditional_indices: checkS4.length,
    S6_calibration_groups: checkS6.length,
    S8_same_sample_models: checkS8Models.length,
    S8_paired_deltas: checkS8Deltas.length,
    S9_complete_case: [checkS9[1], checkS9[2], checkS9[3]],
    S10_high_specificity_rows: checkS10.length,
    S11_sensitivity_rows: checkS11.length,
    canonical_value_checks: ["S4 all 7 index AUCs/CIs/Briers", "S6 all 20 calibration groups",
      "S8 four clinical models and six paired deltas", "S9 complete-case AUCs and delta",
      "S11 all nine sensitivity AUCs/CIs"],
  },
  previews,
};
await fs.writeFile(root + "07_QA/WP3_SUPPLEMENT_WORKBOOK_VALIDATION.json", JSON.stringify(checks, null, 2));
console.log(JSON.stringify(checks));
