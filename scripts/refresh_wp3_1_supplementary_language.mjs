import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const runtimeModules = path.join(
  os.homedir(),
  ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules",
);
const require = createRequire(path.join(runtimeModules, "__artifact_tool_resolver__.cjs"));
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(require.resolve("@oai/artifact-tool")).href);
const workbookPath = process.argv[2];

if (!workbookPath) throw new Error("Expected the supplementary workbook path");

const edits = [
  {
    sheet: "S4_Indices",
    cell: "A12",
    before: "All estimates use the frozen repeated nested-OOF outputs and absolute counts. PIV was prespecified as the primary comparator; no new index hypothesis tests were performed.",
    after: "All estimates use repeated nested cross-validation results and absolute counts. PIV was prespecified as the primary comparator; no additional index hypotheses were tested.",
  },
  {
    sheet: "S6_Resampling",
    cell: "A47",
    before: "Calibration groups and summaries are descriptive summaries of frozen patient-level mean held-out predictions; they are not recalculated model estimates.",
    after: "Calibration groups and summaries describe the patient-level mean held-out predictions; they are not recalculated model estimates.",
  },
  {
    sheet: "S10_HighSpecificity",
    cell: "A8",
    before: "The 138 AMI records met the frozen strict discharge-diagnosis text criteria; 40 later-group AMI records did not. These 40 were not adjudicated as misclassifications. The comparison is text-based, not independent clinical adjudication.",
    after: "The 138 AMI records met the strict discharge-diagnosis text criteria; 40 later-group AMI records did not. These 40 were not adjudicated as misclassifications. The comparison is text-based, not independent clinical adjudication.",
  },
];

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
for (const edit of edits) {
  const cell = workbook.worksheets.getItem(edit.sheet).getRange(edit.cell);
  const current = cell.values[0][0];
  if (current !== edit.before) {
    throw new Error(`Unexpected source text in ${edit.sheet}!${edit.cell}: ${String(current)}`);
  }
  cell.values = [[edit.after]];
}
workbook.recalculate();
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(workbookPath);

const check = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
for (const edit of edits) {
  const current = check.worksheets.getItem(edit.sheet).getRange(edit.cell).values[0][0];
  if (current !== edit.after) {
    throw new Error(`Post-export verification failed for ${edit.sheet}!${edit.cell}`);
  }
}
console.log(`Updated and verified ${edits.length} supplementary-table notes; no analysis values changed.`);
