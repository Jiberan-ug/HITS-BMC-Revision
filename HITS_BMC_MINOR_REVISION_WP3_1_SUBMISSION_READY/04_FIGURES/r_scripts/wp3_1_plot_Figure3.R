#!/usr/bin/env Rscript
suppressPackageStartupMessages(library(ggplot2))

args <- commandArgs(trailingOnly = FALSE)
fa <- args[grepl("^--file=", args)]
script_dir <- if (length(fa)) dirname(normalizePath(sub("^--file=", "", fa[1]))) else getwd()
figure_dir <- normalizePath(file.path(script_dir, ".."))
d <- read.csv(file.path(figure_dir, "source_data", "Figure3_calibration_source.csv"), stringsAsFactors = FALSE)
d$model <- factor(d$model, levels = c("Core-7", "Enhanced (full cohort)"),
                  labels = c("Core-7", "Enhanced"))
cols <- c("Core-7" = "#247C9D", "Enhanced" = "#318260")
p <- ggplot(d, aes(x = mean_predicted, y = observed_rate, colour = model, group = model)) +
  geom_abline(slope = 1, intercept = 0, linetype = 2, colour = "#9AA5B1", linewidth = 0.35) +
  geom_line(linewidth = 0.75) +
  geom_point(size = 1.8) +
  scale_colour_manual(values = cols) +
  coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
  labs(x = "Mean predicted probability", y = "Observed AMI proportion", colour = NULL) +
  theme_classic(base_size = 10) +
  theme(legend.position = "bottom", plot.margin = margin(6, 8, 6, 8),
        axis.title = element_text(size = 10), axis.text = element_text(colour = "#263238"))

ggsave(file.path(figure_dir, "Figure3_Revised.pdf"), p, width = 150, height = 140, units = "mm", device = grDevices::pdf, useDingbats = FALSE)
ggsave(file.path(figure_dir, "Figure3_Revised.tiff"), p, width = 150, height = 140, units = "mm", dpi = 600, compression = "lzw")
ggsave(file.path(figure_dir, "Figure3_Revised.png"), p, width = 150, height = 140, units = "mm", dpi = 600)
