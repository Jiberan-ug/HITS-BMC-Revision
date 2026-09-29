args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) args[[1]] else normalizePath(file.path(dirname(sub("--file=", "", commandArgs()[grep("--file=", commandArgs())][1])), "..", ".."))
source(file.path(root, "05_SOURCE_TRACEABILITY", "figure_scripts", "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
nodes <- read.csv(file.path(root, "05_SOURCE_TRACEABILITY", "source_data", "Figure1_flow_nodes.csv"), check.names = FALSE)
edge_input <- read.csv(file.path(root, "05_SOURCE_TRACEABILITY", "source_data", "Figure1_flow_edges.csv"), check.names = FALSE)
edges <- merge(edge_input, nodes[c("id", "x", "y", "w")], by.x = "from_id", by.y = "id")
names(edges)[names(edges) %in% c("x", "y", "w")] <- c("from_x", "from_y", "from_w")
edges <- merge(edges, nodes[c("id", "x", "y", "w")], by.x = "to_id", by.y = "id")
names(edges)[names(edges) %in% c("x", "y", "w")] <- c("to_x", "to_y", "to_w")
p <- ggplot(nodes) +
  geom_segment(data = edges,
    aes(x = from_x + from_w / 2, y = from_y, xend = to_x - to_w / 2, yend = to_y),
    linewidth = 0.45, color = "#596B78", arrow = grid::arrow(length = grid::unit(2.2, "mm"), type = "closed")) +
  geom_rect(aes(xmin = x - w / 2, xmax = x + w / 2, ymin = y - h / 2, ymax = y + h / 2, fill = group),
    color = "#49606F", linewidth = 0.45, show.legend = FALSE) +
  geom_text(aes(x = x, y = y, label = label), size = 3.4, lineheight = 1.05, color = "#17242D") +
  scale_fill_manual(values = c(primary = "#E3F1EC", source = "#EAF0F3", phenotype = "#F5F1E7", exclusion = "#F7E9E7")) +
  coord_cartesian(xlim = c(-0.5, 12.0), ylim = c(-2.55, 2.8), expand = FALSE, clip = "off") +
  labs(title = "Study population flow",
    subtitle = "Patient-level record selection was completeness-based; index-admission timing was not verified",
    x = NULL, y = NULL) +
  theme_void(base_size = 11) +
  theme(plot.title = element_text(face = "bold", hjust = 0.5, color = "#111111", margin = margin(b = 8)),
    plot.subtitle = element_text(hjust = 0.5, color = "#333333", size = 9, margin = margin(b = 8)),
    plot.margin = margin(8, 12, 8, 12))
save_figure_set(p, "Figure1_Revised", file.path(root, "04_FIGURES"), 11.2, 6.4)
