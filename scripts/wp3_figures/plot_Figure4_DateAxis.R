args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) args[[1]] else stop("Pass the WP3 package directory.")
source(file.path(root, "05_SOURCE_TRACEABILITY", "figure_scripts", "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
d <- read.csv(file.path(root, "05_SOURCE_TRACEABILITY", "source_data", "Figure4_date_axis_flow_source.csv"))
d$stage <- factor(d$stage, levels = c("Development", "Buffer", "Later"))
d$non_AMI_n <- d$N - d$AMI_n
long <- rbind(
  data.frame(stage = d$stage, status = "AMI phenotype", n = d$AMI_n),
  data.frame(stage = d$stage, status = "Non-AMI CAD", n = d$non_AMI_n)
)
long$status <- factor(long$status, levels = c("AMI phenotype", "Non-AMI CAD"))
p <- ggplot(long, aes(stage, n, fill = status)) +
  geom_col(width = .58, color = "white", linewidth = .35) +
  geom_text(data = d, aes(x = stage, y = N, label = paste0("N=", N, "; AMI=", AMI_n)),
    inherit.aes = FALSE, vjust = -0.55, size = 3.4, color = "#17242D") +
  scale_fill_manual(values = c("AMI phenotype" = "#B34747", "Non-AMI CAD" = "#176D8A")) +
  scale_y_continuous(expand = expansion(mult = c(0, .16))) +
  labs(title = "Exploratory deidentified date-axis sensitivity allocation",
    subtitle = "Not formal temporal validation; dates were not uniformly linked to the index angiography hospitalization",
    x = "Prespecified date-axis group", y = "Patients") +
  wp3_theme() + theme(plot.subtitle = element_text(color = "#333333", size = 9),
    plot.margin = margin(8, 10, 8, 8))
save_figure_set(p, "Figure4_Revised", file.path(root, "04_FIGURES"), 7.6, 5.0)
