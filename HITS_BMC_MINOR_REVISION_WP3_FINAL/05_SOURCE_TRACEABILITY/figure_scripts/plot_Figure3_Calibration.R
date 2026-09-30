args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) args[[1]] else stop("Pass the WP3 package directory.")
source(file.path(root, "05_SOURCE_TRACEABILITY", "figure_scripts", "figure_helpers.R"))
suppressPackageStartupMessages(library(ggplot2))
d <- read.csv(file.path(root, "05_SOURCE_TRACEABILITY", "source_data", "Figure3_calibration_source.csv"))
d <- subset(d, model %in% c("Core-7", "Enhanced (full cohort)"))
d$model <- factor(d$model, levels = c("Core-7", "Enhanced (full cohort)"),
  labels = c("Core-7", "Enhanced"))
p <- ggplot(d, aes(mean_predicted, observed_rate, color = model, group = model)) +
  geom_abline(slope = 1, intercept = 0, linetype = 2, color = "#9CA8AE", linewidth = .45) +
  geom_line(linewidth = .8) + geom_point(aes(size = N), alpha = .9) +
  scale_color_manual(values = c("Core-7" = "#176D8A", "Enhanced" = "#267A5A")) +
  scale_size_continuous(range = c(1.8, 3.3), guide = "none") +
  scale_x_continuous(limits = c(0, .7), breaks = seq(0, .7, .1), expand = c(0, 0)) +
  scale_y_continuous(limits = c(0, .7), breaks = seq(0, .7, .1), expand = c(0, 0)) +
  coord_equal() +
  labs(title = "Calibration from mean 5-fold by 10-repeat held-out predictions",
    x = "Mean predicted probability", y = "Observed AMI proportion") +
  wp3_theme() + theme(plot.margin = margin(8, 10, 8, 8))
save_figure_set(p, "Figure3_Revised", file.path(root, "04_FIGURES"), 7.2, 6.2)
