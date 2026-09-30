args <- commandArgs(trailingOnly = FALSE)
fa <- args[grepl("^--file=", args)]
script_dir <- if (length(fa)) dirname(normalizePath(sub("^--file=", "", fa[1]))) else getwd()
source_root <- normalizePath(file.path(script_dir, ".."))
output_dir <- if (basename(source_root) == "05_SOURCE_TRACEABILITY") {
  normalizePath(file.path(source_root, "..", "04_FIGURES"))
} else source_root
source(file.path(script_dir, "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
d <- read.csv(file.path(source_root, "source_data", "FigureS4_domain_schema.csv"))
d$domain <- factor(d$domain, levels = rev(unique(d$domain)))
d$group <- factor(d$group, levels = c("core", "enhanced"))
p <- ggplot(d, aes(x = x, y = domain, fill = group)) +
  geom_tile(width = .84, height = .72, color = "#64717A", linewidth = .45) +
  geom_text(aes(label = content), color = "#17242D", size = 3.7, lineheight = 1.05) +
  scale_fill_manual(values = c(core = "#DDEBF0", enhanced = "#F2E9D5")) +
  scale_x_continuous(breaks = c(1, 2), labels = c("Core-7", "Enhanced model"),
    limits = c(.45, 2.55), expand = c(0, 0)) +
  labs(title = "Analytical grouping of routine hematologic features",
    subtitle = "Domains organize variables for interpretation; they are not independent causal pathways",
    x = NULL, y = NULL, fill = NULL) +
  wp3_theme() +
  theme(axis.text.y = element_text(face = "bold"), panel.grid = element_blank(),
    legend.position = "none", plot.subtitle = element_text(size = 9),
    plot.margin = margin(8, 10, 8, 8))
save_figure_set(p, "FigureS4_Domains", output_dir, 8.1, 4.8)
