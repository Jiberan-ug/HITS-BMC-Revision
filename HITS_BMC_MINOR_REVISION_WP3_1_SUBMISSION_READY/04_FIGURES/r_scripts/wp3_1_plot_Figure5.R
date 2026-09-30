#!/usr/bin/env Rscript
suppressPackageStartupMessages(library(ggplot2))

args <- commandArgs(trailingOnly = FALSE)
fa <- args[grepl("^--file=", args)]
script_dir <- if (length(fa)) dirname(normalizePath(sub("^--file=", "", fa[1]))) else getwd()
figure_dir <- normalizePath(file.path(script_dir, ".."))
d <- read.csv(file.path(figure_dir, "source_data", "Figure5_Revised_source.csv"), stringsAsFactors = FALSE)
d$analysis <- factor(d$analysis, levels = rev(unique(d$analysis)))
d$model <- factor(d$model, levels = c("PIV", "Core-7", "Enhanced"))
cols <- c("PIV" = "#2F80B7", "Core-7" = "#F28E2B", "Enhanced" = "#2CA02C")
p <- ggplot(d, aes(x = auc, y = analysis, colour = model, group = model)) +
  geom_errorbar(aes(xmin = ci_lower, xmax = ci_upper),
                position = position_dodge(width = 0.48), width = 0.22, linewidth = 0.65) +
  geom_point(position = position_dodge(width = 0.48), size = 2.1) +
  scale_colour_manual(values = cols) +
  scale_x_continuous(limits = c(0.55, 0.86), breaks = seq(0.55, 0.85, 0.05), expand = c(0.01, 0.01)) +
  labs(x = "AUC (95% CI)", y = NULL, colour = NULL) +
  theme_classic(base_size = 10) +
  theme(legend.position = "bottom", plot.margin = margin(6, 8, 6, 8),
        axis.text = element_text(colour = "#263238"))

ggsave(file.path(figure_dir, "Figure5_Revised.pdf"), p, width = 175, height = 130, units = "mm", device = grDevices::pdf, useDingbats = FALSE)
ggsave(file.path(figure_dir, "Figure5_Revised.tiff"), p, width = 175, height = 130, units = "mm", dpi = 600, compression = "lzw")
ggsave(file.path(figure_dir, "Figure5_Revised.png"), p, width = 175, height = 130, units = "mm", dpi = 600)
