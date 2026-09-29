args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) args[[1]] else stop("Pass the WP3 package directory.")
source(file.path(root, "05_SOURCE_TRACEABILITY", "figure_scripts", "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
d <- read.csv(file.path(root, "05_SOURCE_TRACEABILITY", "source_data", "Figure5_robustness_source.csv"))
d$analysis <- factor(d$analysis, levels = c(
  "Symmetric +/-182-day guard-band", "High-specificity phenotype", "Conservative +/-365-day buffer"
), labels = c("Date-axis sensitivity (symmetric +/-182 days)",
  "High-specificity phenotype comparison", "Date-axis sensitivity (conservative +/-365 days)"))
d$model <- factor(d$model, levels = c("PIV", "Core-7", "Enhanced"))
cols <- c("PIV" = "#B34747", "Core-7" = "#176D8A", "Enhanced" = "#267A5A")
p <- ggplot(d, aes(AUC, model, color = model)) +
  geom_segment(aes(x = CI_lower, xend = CI_upper, y = model, yend = model), linewidth = .75) +
  geom_point(size = 2.1) +
  geom_text(aes(label = sprintf("%.3f (%.3f-%.3f)", AUC, CI_lower, CI_upper)),
    nudge_y = .25, show.legend = FALSE, size = 2.8, color = "#26343C") +
  facet_wrap(~analysis, ncol = 1, scales = "free_y") +
  scale_color_manual(values = cols) +
  scale_x_continuous(limits = c(.58, .88), breaks = seq(.6, .85, .05)) +
  labs(title = "AUCs across prespecified sensitivity comparisons", x = "AUC (95% CI)", y = NULL) +
  wp3_theme() +
  theme(legend.position = "none", strip.text = element_text(face = "bold", hjust = 0),
    panel.spacing = grid::unit(0.65, "lines"), plot.margin = margin(8, 16, 8, 8))
save_figure_set(p, "Figure5_Revised", file.path(root, "04_FIGURES"), 8.2, 8.0)
