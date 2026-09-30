#!/usr/bin/env Rscript
suppressPackageStartupMessages({library(ggplot2); library(patchwork)})

args <- commandArgs(trailingOnly = FALSE)
fa <- args[grepl("^--file=", args)]
script_dir <- if (length(fa)) dirname(normalizePath(sub("^--file=", "", fa[1]))) else getwd()
figure_dir <- normalizePath(file.path(script_dir, ".."))
flow <- read.csv(file.path(figure_dir, "source_data", "Figure4_DateAxisFlow_Revised_source.csv"), stringsAsFactors = FALSE)
d <- read.csv(file.path(figure_dir, "source_data", "Figure4_Revised_auc_source.csv"), stringsAsFactors = FALSE)
d$analysis <- factor(d$analysis, levels = rev(unique(d$analysis)))
d$model <- factor(d$model, levels = c("PIV", "Core-7", "Enhanced"))
cols <- c("PIV" = "#2F80B7", "Core-7" = "#F28E2B", "Enhanced" = "#2CA02C")
flow$label <- paste0(flow$stage, "\nN = ", format(flow$N, big.mark = ","),
                     "; AMI = ", format(flow$AMI_n, big.mark = ","))
flow$y <- c(2.6, 1.55, 0.5)
edges <- data.frame(x = 0.5, xend = 0.5, y = c(2.22, 1.17), yend = c(1.92, 0.87))
scheme <- ggplot() +
  geom_segment(data = edges, aes(x = x, xend = xend, y = y, yend = yend),
               linewidth = 0.6, colour = "#666666",
               arrow = grid::arrow(length = grid::unit(2.2, "mm"), type = "closed")) +
  geom_label(data = flow, aes(x = 0.5, y = y, label = label),
             fill = "#F3F4F6", colour = "#333333", linewidth = 0.45,
             size = 2.8, lineheight = 0.98, label.padding = grid::unit(0.34, "lines"),
             label.r = grid::unit(0.08, "lines")) +
  annotate("text", x = 0.03, y = 3.25, label = "A", fontface = "bold", hjust = 0, size = 4.2) +
  coord_cartesian(xlim = c(0, 1), ylim = c(0.0, 3.45), expand = FALSE, clip = "off") +
  theme_void() + theme(plot.margin = margin(6, 6, 6, 6))
forest <- ggplot(d, aes(x = auc, y = analysis, colour = model, group = model)) +
  geom_errorbar(aes(xmin = ci_lower, xmax = ci_upper),
                position = position_dodge(width = 0.48), width = 0.22, linewidth = 0.55) +
  geom_point(position = position_dodge(width = 0.48), size = 2) +
  scale_colour_manual(values = cols) +
  scale_x_continuous(limits = c(0.55, 0.86), breaks = seq(0.55, 0.85, 0.05), expand = c(0.01, 0.01)) +
  labs(x = "AUC (95% CI)", y = NULL, colour = NULL) +
  theme_classic(base_size = 9.5) +
  theme(legend.position = "bottom", plot.margin = margin(6, 8, 6, 8),
        axis.text = element_text(colour = "#263238")) +
  annotate("text", x = 0.55, y = Inf, label = "B", hjust = 0, vjust = 1.8,
           fontface = "bold", size = 4.2, colour = "#263238")
p <- scheme + forest + plot_layout(widths = c(0.40, 1.60), guides = "collect") & theme(legend.position = "bottom")

ggsave(file.path(figure_dir, "Figure4_Revised.pdf"), p, width = 210, height = 120, units = "mm", device = grDevices::pdf, useDingbats = FALSE)
ggsave(file.path(figure_dir, "Figure4_Revised.tiff"), p, width = 210, height = 120, units = "mm", dpi = 600, compression = "lzw")
ggsave(file.path(figure_dir, "Figure4_Revised.png"), p, width = 210, height = 120, units = "mm", dpi = 600)
