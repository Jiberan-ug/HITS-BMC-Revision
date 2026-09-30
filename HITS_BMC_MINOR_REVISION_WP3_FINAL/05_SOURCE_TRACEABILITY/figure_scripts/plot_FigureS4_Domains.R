args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) args[[1]] else stop("Pass the WP3 package directory.")
source(file.path(root, "05_SOURCE_TRACEABILITY", "figure_scripts", "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
d <- read.csv(file.path(root, "05_SOURCE_TRACEABILITY", "source_data", "FigureS4_domain_schema.csv"))
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
save_figure_set(p, "FigureS4_Domains", file.path(root, "04_FIGURES"), 8.1, 4.8)
