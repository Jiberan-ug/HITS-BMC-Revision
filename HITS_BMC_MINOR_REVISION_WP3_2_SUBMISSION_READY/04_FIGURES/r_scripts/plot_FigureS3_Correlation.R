args <- commandArgs(trailingOnly = FALSE)
fa <- args[grepl("^--file=", args)]
script_dir <- if (length(fa)) dirname(normalizePath(sub("^--file=", "", fa[1]))) else getwd()
source_root <- normalizePath(file.path(script_dir, ".."))
output_dir <- if (basename(source_root) == "05_SOURCE_TRACEABILITY") {
  normalizePath(file.path(source_root, "..", "04_FIGURES"))
} else source_root
source(file.path(script_dir, "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
d <- read.csv(file.path(source_root, "source_data", "FigureS3_correlation_source.csv"), check.names = FALSE)
d$variable <- factor(d$variable, levels = unique(d$variable))
d$variable2 <- factor(d$variable2, levels = rev(unique(d$variable2)))
p <- ggplot(d, aes(variable, variable2, fill = rho)) +
  geom_tile(color = "white", linewidth = .45) +
  geom_text(aes(label = sprintf("%.2f", rho)), size = 3, color = "#17242D") +
  scale_fill_gradient2(low = "#B34747", mid = "#F7F8F8", high = "#176D8A",
    midpoint = 0, limits = c(-1, 1), name = "Spearman rho") +
  coord_equal() +
  labs(title = "Core-7 pairwise Spearman correlations", x = NULL, y = NULL) +
  wp3_theme() + theme(axis.text.x = element_text(angle = 35, hjust = 1),
    legend.position = "right", plot.margin = margin(8, 8, 8, 8))
save_figure_set(p, "FigureS3_Core7Correlation", output_dir, 7.0, 6.3)
