#!/usr/bin/env Rscript
suppressPackageStartupMessages(library(ggplot2))

args <- commandArgs(trailingOnly = FALSE)
fa <- args[grepl("^--file=", args)]
script_dir <- if (length(fa)) dirname(normalizePath(sub("^--file=", "", fa[1]))) else getwd()
figure_dir <- normalizePath(file.path(script_dir, ".."))
nodes <- read.csv(file.path(figure_dir, "source_data", "Figure1_Revised_source.csv"), stringsAsFactors = FALSE)
edges <- read.csv(file.path(figure_dir, "source_data", "Figure1_Revised_edges.csv"), stringsAsFactors = FALSE)
edges <- merge(edges, nodes[, c("node_id", "x", "y")], by.x = "from_id", by.y = "node_id", all.x = TRUE)
edges <- merge(edges, nodes[, c("node_id", "x", "y")], by.x = "to_id", by.y = "node_id", suffixes = c("_from", "_to"), all.x = TRUE)

fills <- c(source = "#EAF1F5", phenotype = "#F7F9FB", review = "#F3F4F6", exclusion = "#F3F4F6", analysis = "#E7F0EA", sensitivity = "#F8EFE5")
p <- ggplot() +
  geom_segment(data = edges, aes(x = x_from, y = y_from, xend = x_to, yend = y_to),
               linewidth = 0.45, colour = "#65727E",
               arrow = grid::arrow(length = grid::unit(2.2, "mm"), type = "closed")) +
  geom_label(data = nodes, aes(x = x, y = y, label = label, fill = role),
             colour = "#263238", linewidth = 0.3, size = 2.85, lineheight = 0.94,
             label.padding = grid::unit(0.30, "lines"), label.r = grid::unit(0.08, "lines")) +
  scale_fill_manual(values = fills, drop = FALSE) +
  coord_cartesian(xlim = c(-1.0, 6.25), ylim = c(1.0, 11.3), expand = FALSE, clip = "off") +
  theme_void() +
  theme(legend.position = "none", plot.margin = margin(8, 12, 8, 12),
        plot.background = element_rect(fill = "white", colour = NA),
        panel.background = element_rect(fill = "white", colour = NA))

ggsave(file.path(figure_dir, "Figure1_Revised_OriginalStyle.pdf"), p,
       width = 180, height = 205, units = "mm", device = grDevices::pdf, useDingbats = FALSE, bg = "white")
ggsave(file.path(figure_dir, "Figure1_Revised_OriginalStyle.tiff"), p,
       width = 180, height = 205, units = "mm", dpi = 600, compression = "lzw", bg = "white")
ggsave(file.path(figure_dir, "Figure1_Revised_OriginalStyle.png"), p,
       width = 180, height = 205, units = "mm", dpi = 600, bg = "white")
