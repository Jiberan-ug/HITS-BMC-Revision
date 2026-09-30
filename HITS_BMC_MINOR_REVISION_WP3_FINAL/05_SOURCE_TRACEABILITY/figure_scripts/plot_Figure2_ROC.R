args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) args[[1]] else stop("Pass the WP3 package directory.")
source(file.path(root, "05_SOURCE_TRACEABILITY", "figure_scripts", "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
d <- read.csv(file.path(root, "05_SOURCE_TRACEABILITY", "source_data", "Figure2_roc_source.csv"))
labels <- unique(d[c("model", "auc", "auc_ci_lower", "auc_ci_upper")])
labels$label <- sprintf("%s  AUC %.3f (95%% CI %.3f-%.3f)",
  labels$model, labels$auc, labels$auc_ci_lower, labels$auc_ci_upper)
legend_labels <- stats::setNames(labels$label, labels$model)
labels$model <- factor(labels$model, levels = c("PIV", "Core-7", "Enhanced"))
d$model <- factor(d$model, levels = c("PIV", "Core-7", "Enhanced"))
label_colors <- c("PIV" = "#B34747", "Core-7" = "#176D8A", "Enhanced" = "#267A5A")
p <- ggplot(d, aes(false_positive_rate, true_positive_rate, color = model)) +
  geom_abline(slope = 1, intercept = 0, linetype = 2, color = "#A8B0B6", linewidth = 0.45) +
  geom_line(linewidth = 1) +
  scale_color_manual(values = label_colors, breaks = levels(d$model),
    labels = legend_labels[levels(d$model)], name = NULL) +
  scale_x_continuous(limits = c(0, 1), breaks = seq(0, 1, .2), expand = c(0, 0)) +
  scale_y_continuous(limits = c(0, 1), breaks = seq(0, 1, .2), expand = c(0, 0)) +
  coord_equal() +
  labs(title = "Internal discrimination from repeated cross-validation",
    x = "1 - specificity", y = "Sensitivity") +
  wp3_theme() +
  theme(legend.position = "right", legend.text = element_text(size = 8.5),
    legend.key.width = grid::unit(0.8, "cm"), plot.margin = margin(8, 8, 8, 8))
save_figure_set(p, "Figure2_Revised", file.path(root, "04_FIGURES"), 8.4, 6.5)
