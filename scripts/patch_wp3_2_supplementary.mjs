import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const runtimeModules = path.join(
  os.homedir(),
  ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules",
);
const require = createRequire(path.join(runtimeModules, "__artifact_tool_resolver__.cjs"));
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(require.resolve("@oai/artifact-tool")).href);

const workbookPath = process.argv[2];
const outputPath = process.argv[3];
const previewPath = process.argv[4];
if (!workbookPath || !outputPath || !previewPath) {
  throw new Error("Expected input workbook, output workbook, and preview PNG paths");
}

const edits = [
  {
    cell: "A14",
    before: "The conservative +/-365-day output supplies total N and model AUCs/intervals but not an approved AMI/control decomposition; none is inferred here. Temporal sensitivity analyses used institutionally deidentified hospitalization/coronary-angiography dates from the study period and are not formal temporal validation. Exact CBC sampling times relative to admission, angiography, or AMI diagnosis could not be reconstructed uniformly.",
    after: "The conservative +/-365-day output supplies total N and model AUCs/intervals but not an approved AMI/control decomposition; none is inferred here. The six-month temporal sensitivity analysis used institutionally deidentified hospitalization/coronary-angiography dates from the 2020-2026 study period with patient-specific shifts within +/-182 days. Its retained output records group roles and counts but not a source-verified calendar cutpoint; the stale cutoff from an earlier draft is not reported. These analyses are not formal temporal validation. Exact CBC sampling times relative to admission, angiography, or AMI diagnosis could not be reconstructed uniformly.",
  },
];

function snapshot(wb) {
  const numeric = [];
  const formulas = [];
  for (const sheet of wb.worksheets.items) {
    const used = sheet.getUsedRange();
    if (!used) continue;
    const values = used.values;
    const formulaMatrix = used.formulas;
    for (let r = 0; r < values.length; r++) {
      for (let c = 0; c < (values[r]?.length ?? 0); c++) {
        const value = values[r][c];
        if (typeof value === "number") numeric.push([sheet.name, r, c, value]);
        const formula = formulaMatrix?.[r]?.[c];
        if (typeof formula === "string" && formula.startsWith("=")) formulas.push([sheet.name, r, c, formula]);
      }
    }
  }
  return { numeric: JSON.stringify(numeric), formulas: JSON.stringify(formulas) };
}

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const sheet = workbook.worksheets.getItem("S11_Temporal");
const beforeState = snapshot(workbook);
for (const edit of edits) {
  const cell = sheet.getRange(edit.cell);
  const current = cell.values[0][0];
  if (current !== edit.before) throw new Error(`Unexpected text at S11_Temporal!${edit.cell}: ${String(current)}`);
  cell.values = [[edit.after]];
}

workbook.recalculate();
const afterState = snapshot(workbook);
if (beforeState.numeric !== afterState.numeric) throw new Error("A numeric value changed during the label-only edit");
if (beforeState.formulas !== afterState.formulas) throw new Error("A formula changed during the label-only edit");

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
const check = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
const checkSheet = check.worksheets.getItem("S11_Temporal");
for (const edit of edits) {
  const current = checkSheet.getRange(edit.cell).values[0][0];
  if (current !== edit.after) throw new Error(`Post-export verification failed for S11_Temporal!${edit.cell}`);
}
const exportedState = snapshot(check);
if (beforeState.numeric !== exportedState.numeric) throw new Error("Numeric values differ after XLSX export/import");
if (beforeState.formulas !== exportedState.formulas) throw new Error("Formulas differ after XLSX export/import");

const preview = await check.render({ sheetName: "S11_Temporal", range: "A1:F22", scale: 1, format: "png" });
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
console.log(`Updated ${edits.length} temporal-source labels/notes; all numeric cells and formulas are unchanged.`);
