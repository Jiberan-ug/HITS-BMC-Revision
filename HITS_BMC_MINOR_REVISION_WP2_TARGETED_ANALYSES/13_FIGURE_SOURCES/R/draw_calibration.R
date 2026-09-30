args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Pass the WP2 output directory")
out <- normalizePath(args[[1]], mustWork = TRUE)
src_dir <- file.path(out, "13_FIGURE_SOURCES")
cal <- read.csv(file.path(out, "08_CALIBRATION", "CALIBRATION_CANONICAL_SOURCE.csv"), stringsAsFactors = FALSE)
keep <- c("PIV", "Core-7", "Enhanced (full cohort)", "Enhanced (complete case)")
cal <- cal[cal$model %in% keep, , drop = FALSE]
cal$model <- factor(cal$model, levels = keep)
p <- ggplot2::ggplot(cal, ggplot2::aes(mean_predicted, observed_rate, colour = model, group = model)) +
  ggplot2::geom_abline(slope = 1, intercept = 0, linetype = 2, colour = "grey55") +
  ggplot2::geom_line(linewidth = 0.85) +
  ggplot2::geom_point(ggplot2::aes(size = N), alpha = 0.9) +
  ggplot2::scale_colour_manual(values = c("#007C91", "#CC5A27", "#4D7C0F", "#7A5195")) +
  ggplot2::scale_size_continuous(range = c(1.8, 3.4), guide = "none") +
  ggplot2::coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
  ggplot2::labs(x = "Mean predicted probability", y = "Observed AMI proportion", colour = NULL, title = "Calibration from canonical patient-mean OOF predictions") +
  ggplot2::theme_classic(base_size = 11) +
  ggplot2::theme(legend.position = "bottom", plot.title = ggplot2::element_text(face = "bold"))
stem <- "Figure_Calibration_Canonical_OOF"
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".pdf")), p, width = 7.0, height = 5.8, device = grDevices::pdf)
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".tiff")), p, width = 7.0, height = 5.8, dpi = 600, device = ragg::agg_tiff, compression = "lzw")
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".png")), p, width = 7.0, height = 5.8, dpi = 600, device = ragg::agg_png)
writeLines(trimws(capture.output(utils::sessionInfo()), which = "right"), file.path(out, "14_CODE", "R_sessionInfo.txt"))
