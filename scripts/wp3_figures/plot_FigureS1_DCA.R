args <- commandArgs(trailingOnly = FALSE)
fa <- args[grepl("^--file=", args)]
script_dir <- if (length(fa)) dirname(normalizePath(sub("^--file=", "", fa[1]))) else getwd()
source_root <- normalizePath(file.path(script_dir, ".."))
output_dir <- if (basename(source_root) == "05_SOURCE_TRACEABILITY") {
  normalizePath(file.path(source_root, "..", "04_FIGURES"))
} else source_root
source(file.path(script_dir, "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
d <- read.csv(file.path(source_root, "source_data", "FigureS1_dca_source.csv"))
d$threshold_probability <- round(d$threshold_probability, 2)
d$model <- factor(d$model, levels = c("Treat none", "Treat all", "Clinical only",
  "Clinical + PIV", "Clinical + Core-7", "Clinical + Enhanced"))
cols <- c("Treat none" = "#333333", "Treat all" = "#888888", "Clinical only" = "#B34747",
  "Clinical + PIV" = "#C28E2C", "Clinical + Core-7" = "#176D8A", "Clinical + Enhanced" = "#267A5A")
p <- ggplot(d, aes(threshold_probability, net_benefit, color = model)) +
  geom_hline(yintercept = 0, color = "#7D858B", linewidth = .4) +
  geom_line(linewidth = .72) + scale_color_manual(values = cols) +
  scale_x_continuous(limits = c(.05, .50), breaks = seq(.05, .50, .05)) +
  labs(title = "Exploratory decision-curve analysis",
    subtitle = "Fibrinogen-complete cohort; descriptive net benefit only",
    x = "Threshold probability", y = "Net benefit") +
  wp3_theme() + theme(legend.position = "bottom", legend.text = element_text(size = 8),
    plot.margin = margin(8, 10, 8, 8))
save_figure_set(p, "FigureS1_DCA", output_dir, 8.0, 5.8)
