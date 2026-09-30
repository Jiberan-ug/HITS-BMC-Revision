args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) args[[1]] else stop("Pass the WP3 package directory.")
source(file.path(root, "05_SOURCE_TRACEABILITY", "figure_scripts", "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
d <- read.csv(file.path(root, "05_SOURCE_TRACEABILITY", "source_data", "FigureS1_dca_source.csv"))
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
save_figure_set(p, "FigureS1_DCA", file.path(root, "04_FIGURES"), 8.0, 5.8)
