#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) {
  stop("Usage: Rscript wp3_rebuild_table1_age.R <restricted-master.csv> <aggregate-output.csv>")
}
input_path <- args[[1]]
output_path <- args[[2]]
if (!file.exists(input_path)) stop("Input source was not found.")

parse_num <- function(x) {
  x <- trimws(as.character(x))
  x[x %in% c("", "NA", "N/A", "NULL")] <- NA_character_
  x <- gsub(",", "", x, fixed = TRUE)
  x <- sub("^[<>]=?[[:space:]]*", "", x)
  suppressWarnings(as.numeric(x))
}

parse_dt <- function(x) {
  s <- trimws(as.character(x))
  s[s %in% c("", "NA", "N/A")] <- NA_character_
  out <- as.POSIXct(rep(NA_real_, length(s)), origin = "1970-01-01", tz = "UTC")
  formats <- c(
    "%Y-%m-%d %H:%M:%OS", "%Y-%m-%d", "%Y/%m/%d %H:%M:%OS",
    "%Y/%m/%d", "%m/%d/%Y %H:%M:%OS", "%m/%d/%Y", "%Y%m%d"
  )
  for (fmt in formats) {
    idx <- is.na(out) & !is.na(s)
    if (!any(idx)) break
    parsed <- strptime(s[idx], format = fmt, tz = "UTC")
    out[idx] <- as.POSIXct(parsed, tz = "UTC")
  }
  numeric <- suppressWarnings(as.numeric(s))
  excel <- is.na(out) & !is.na(numeric) & numeric > 20000 & numeric < 70000
  out[excel] <- as.POSIXct("1899-12-30", tz = "UTC") + numeric[excel] * 86400
  out
}

mi_re <- "(?<![A-Za-z])(?:STEMI|NSTEMI|MI)(?![A-Za-z])|心肌梗(?:死|塞)|myocardial[[:space:]]+infarction"
uncertain_re <- "待排|疑似|疑诊|考虑|可能|待查|排除|rule[[:space:]]+out|suspected"
old_re <- "陈旧|既往|病史|old|prior|previous|history[[:space:]]+of"
cad_re <- "冠状动脉粥样硬化性心脏病|冠心病|冠状动脉疾病|coronary[[:space:]]+artery[[:space:]]+disease|(?<![A-Za-z])CAD(?![A-Za-z])|稳定型?心绞痛|不稳定型?心绞痛|stable[[:space:]]+angina|unstable[[:space:]]+angina|PCI|冠状动脉支架|冠脉支架|冠状动脉旁路|CABG|冠脉搭桥|急性冠脉综合征|acute[[:space:]]+coronary[[:space:]]+syndrome"
strict_cad_re <- "冠状动脉粥样硬化性心脏病|冠心病|冠状动脉疾病|coronary[[:space:]]+artery[[:space:]]+disease|(?<![A-Za-z])CAD(?![A-Za-z])|稳定型?心绞痛|不稳定型?心绞痛|stable[[:space:]]+angina|unstable[[:space:]]+angina|PCI|冠状动脉支架|冠脉支架|冠状动脉旁路|CABG|冠脉搭桥"
negated_re <- "(?:无|否认|未见|没有).{0,4}(?:心肌梗(?:死|塞)|myocardial[[:space:]]+infarction|MI)"

has_re <- function(x, pattern) grepl(pattern, x, perl = TRUE, ignore.case = TRUE)
classify <- function(text) {
  text <- if (is.na(text)) "" else trimws(as.character(text))
  if (!nzchar(text)) return("C_ambiguous_or_review")
  components <- unlist(strsplit(text, "[,，;；。|]+", perl = TRUE), use.names = FALSE)
  components <- trimws(components[nzchar(trimws(components))])
  mi_components <- components[vapply(components, has_re, logical(1), pattern = mi_re)]
  any_mi <- length(mi_components) > 0L || has_re(text, mi_re)
  if (any_mi && has_re(text, negated_re)) {
    any_mi <- FALSE
    mi_components <- character()
  }
  acute_pattern <- paste0(
    "(?:急性|亚急(?:性)?|acute|subacute).{0,20}(?:心肌梗(?:死|塞)|myocardial[[:space:]]+infarction)|",
    "(?:心肌梗(?:死|塞)|myocardial[[:space:]]+infarction).{0,12}(?:急性|亚急(?:性)?|acute|subacute)|",
    "(?:STEMI|NSTEMI|ST[[:space:]]*段[[:space:]]*(?:抬高|非抬高)|非ST[[:space:]]*段[[:space:]]*(?:抬高|非抬高)).{0,18}(?:心肌梗(?:死|塞)|myocardial[[:space:]]+infarction)|",
    "(?:心肌梗(?:死|塞)|myocardial[[:space:]]+infarction).{0,18}(?:STEMI|NSTEMI)"
  )
  acute <- any(vapply(mi_components, has_re, logical(1), pattern = acute_pattern))
  if (!acute) {
    acute <- has_re(text, "(?:急性|亚急(?:性)?|acute|subacute).{0,20}(?:心肌梗(?:死|塞)|myocardial[[:space:]]+infarction)|(?:STEMI|NSTEMI).{0,20}(?:心肌梗(?:死|塞)|myocardial[[:space:]]+infarction)")
  }
  old <- any(vapply(mi_components, has_re, logical(1), pattern = old_re))
  uncertain <- any(vapply(mi_components, has_re, logical(1), pattern = uncertain_re))
  acute_uncertain <- uncertain || has_re(text, "(?:急性|亚急(?:性)?).{0,12}(?:待排|疑似|疑诊|考虑|可能)")
  if (acute && acute_uncertain) {
    "C_ambiguous_or_review"
  } else if (acute) {
    "A_definite_AMI"
  } else if (any_mi && old) {
    "B_definite_nonAMI_CAD"
  } else if (any_mi) {
    "C_ambiguous_or_review"
  } else if (has_re(text, cad_re)) {
    "B_definite_nonAMI_CAD"
  } else {
    "out_of_scope_nonCAD"
  }
}

raw <- read.csv(input_path, check.names = FALSE, stringsAsFactors = FALSE, na.strings = c("", "NA", "N/A", "NULL"), fileEncoding = "UTF-8")
needed <- c(
  "patient_sn", "discharge_diagnosis", "admission_date", "birth_date", "基线_birth_date",
  "lab_blood_routine_examination_WBC_test_time", "lab_blood_routine_examination_Neut_test_result__dup02",
  "lab_blood_routine_examination_Lymph_test_result__dup02", "lab_blood_routine_examination_Mono_test_result__dup02",
  "lab_blood_routine_examination_PLT_test_result", "qc_nonmissing_count"
)
missing_fields <- setdiff(needed, names(raw))
if (length(missing_fields)) stop(paste("Missing required fields:", paste(missing_fields, collapse = ", ")))

row_id <- seq_len(nrow(raw))
diagnosis <- trimws(ifelse(is.na(raw$discharge_diagnosis), "", as.character(raw$discharge_diagnosis)))
core <- cbind(
  parse_num(raw$lab_blood_routine_examination_Neut_test_result__dup02),
  parse_num(raw$lab_blood_routine_examination_Lymph_test_result__dup02),
  parse_num(raw$lab_blood_routine_examination_Mono_test_result__dup02),
  parse_num(raw$lab_blood_routine_examination_PLT_test_result)
)
core_count <- rowSums(!is.na(core))
has_time <- !is.na(parse_dt(raw$lab_blood_routine_examination_WBC_test_time))
qc <- parse_num(raw$qc_nonmissing_count)
qc[is.na(qc)] <- 0
patient <- as.character(raw$patient_sn)
ord <- order(patient, -as.integer(nzchar(diagnosis)), -core_count, -as.integer(has_time), -qc, row_id, na.last = TRUE, method = "radix")
sorted <- raw[ord, , drop = FALSE]
sorted_patient <- patient[ord]
keep <- !duplicated(sorted_patient)
selected <- sorted[keep, , drop = FALSE]

pheno <- vapply(selected$discharge_diagnosis, classify, character(1), USE.NAMES = FALSE)
core_selected <- cbind(
  parse_num(selected$lab_blood_routine_examination_Neut_test_result__dup02),
  parse_num(selected$lab_blood_routine_examination_Lymph_test_result__dup02),
  parse_num(selected$lab_blood_routine_examination_Mono_test_result__dup02),
  parse_num(selected$lab_blood_routine_examination_PLT_test_result)
)
primary <- rowSums(!is.na(core_selected)) == 4L & pheno %in% c("A_definite_AMI", "B_definite_nonAMI_CAD")
selected <- selected[primary, , drop = FALSE]
pheno <- pheno[primary]

birth <- parse_dt(selected$birth_date)
birth[is.na(birth)] <- parse_dt(selected$基线_birth_date)[is.na(birth)]
reference <- parse_dt(selected$admission_date)
cbc_time <- parse_dt(selected$lab_blood_routine_examination_WBC_test_time)
reference[is.na(reference)] <- cbc_time[is.na(reference)]
# Match the frozen pandas Timedelta.dt.days derivation exactly.
age_elapsed_days <- floor(as.numeric(difftime(reference, birth, units = "days")))
age <- age_elapsed_days / 365.2425
age[!is.finite(age) | age < 18 | age > 120] <- NA_real_

summ <- function(x) {
  q <- as.numeric(quantile(x, c(0.25, 0.5, 0.75), na.rm = TRUE, type = 7, names = FALSE))
  c(n = sum(!is.na(x)), median = q[[2]], q1 = q[[1]], q3 = q[[3]])
}
groups <- list(
  overall = age,
  AMI = age[pheno == "A_definite_AMI"],
  non_AMI_CAD = age[pheno == "B_definite_nonAMI_CAD"]
)
summary <- do.call(rbind, lapply(names(groups), function(g) {
  s <- summ(groups[[g]])
  data.frame(group = g, age_available_n = s[["n"]], analysis_n = length(groups[[g]]),
    median = s[["median"]], q1 = s[["q1"]], q3 = s[["q3"]], stringsAsFactors = FALSE)
}))
ami_age <- age[pheno == "A_definite_AMI"]
nonami_age <- age[pheno == "B_definite_nonAMI_CAD"]
p_value <- wilcox.test(ami_age, nonami_age, exact = FALSE, correct = TRUE)$p.value
summary$p_value <- c(p_value, NA_real_, NA_real_)

if (nrow(raw) != 2548L || nrow(selected) != 1820L ||
    sum(pheno == "A_definite_AMI") != 453L || sum(pheno == "B_definite_nonAMI_CAD") != 1367L ||
    any(summary$age_available_n != summary$analysis_n)) {
  stop("Rebuilt cohort/age invariants do not match the frozen cohort.")
}
dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)
write.csv(summary, output_path, row.names = FALSE, na = "", fileEncoding = "UTF-8")
cat("raw_rows=", nrow(raw), " selected_unique_patients=", length(unique(sorted_patient)),
    " primary_n=", nrow(selected), " AMI_n=", sum(pheno == "A_definite_AMI"),
    " non_AMI_n=", sum(pheno == "B_definite_nonAMI_CAD"), " age_n=", sum(!is.na(age)),
    " p=", format(p_value, digits = 8), "\n", sep = "")
