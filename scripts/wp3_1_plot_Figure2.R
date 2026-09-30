#!/usr/bin/env Rscript
suppressPackageStartupMessages(library(ggplot2))

args <- commandArgs(trailingOnly = FALSE)
fa <- args[grepl("^--file=", args)]
script_dir <- if (length(fa)) dirname(normalizePath(sub("^--file=", "", fa[1]))) else getwd()
figure_dir <- normalizePath(file.path(script_dir, ".."))
d <- read.csv(file.path(figure_dir, "source_data", "Figure2_roc_source.csv"), stringsAsFactors = FALSE)
model_order <- c("PIV", "Core-7", "Enhanced")
d$model <- factor(d$model, levels = model_order)
ann <- d[!duplicated(d$model), c("model", "auc", "auc_ci_lower", "auc_ci_upper")]
ann$model <- factor(ann$model, levels = model_order)
ann$x <- 0.60
ann$y <- c(PIV = 0.27, `Core-7` = 0.40, Enhanced = 0.53)[as.character(ann$model)]
ann$label <- paste0(as.character(ann$model), "\nAUC ", sprintf("%.3f", ann$auc),
                    "\n95% CI ", sprintf("%.3f", ann$auc_ci_lower), "-", sprintf("%.3f", ann$auc_ci_upper))
cols <- c("PIV" = "#B64B4B", "Core-7" = "#247C9D", "Enhanced" = "#318260")
p <- ggplot(d, aes(x = false_positive_rate, y = true_positive_rate, colour = model)) +
  geom_abline(slope = 1, intercept = 0, linetype = 2, colour = "#9AA5B1", linewidth = 0.35) +
  geom_line(linewidth = 0.8) +
  geom_text(data = ann, aes(x = x, y = y, label = label, colour = model), inherit.aes = FALSE,
            hjust = 0, size = 3.0, lineheight = 1.0, show.legend = FALSE) +
  scale_colour_manual(values = cols) +
  coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
  labs(x = "1 - specificity", y = "Sensitivity", colour = NULL) +
  theme_classic(base_size = 10) +
  theme(legend.position = "bottom", plot.margin = margin(6, 8, 6, 8),
        axis.title = element_text(size = 10), axis.text = element_text(colour = "#263238"))

ggsave(file.path(figure_dir, "Figure2_Revised.pdf"), p, width = 155, height = 145, units = "mm", device = grDevices::pdf, useDingbats = FALSE)
ggsave(file.path(figure_dir, "Figure2_Revised.tiff"), p, width = 155, height = 145, units = "mm", dpi = 600, compression = "lzw")
ggsave(file.path(figure_dir, "Figure2_Revised.png"), p, width = 155, height = 145, units = "mm", dpi = 600)
