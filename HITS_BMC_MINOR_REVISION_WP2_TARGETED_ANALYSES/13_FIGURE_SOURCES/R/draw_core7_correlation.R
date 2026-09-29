args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Pass the WP2 output directory")
out <- normalizePath(args[[1]], mustWork = TRUE)
src_dir <- file.path(out, "13_FIGURE_SOURCES")
corr <- read.csv(file.path(out, "07_COLLINEARITY", "CORE7_CORRELATION_HEATMAP_SOURCE.csv"), stringsAsFactors = FALSE)
vars <- c("neut", "lymph", "mono", "plt", "mpv", "rdw", "hb")
corr$variable_x <- factor(corr$variable_x, levels = vars)
corr$variable_y <- factor(corr$variable_y, levels = rev(vars))
p <- ggplot2::ggplot(corr, ggplot2::aes(variable_x, variable_y, fill = spearman_rho)) +
  ggplot2::geom_tile(colour = "white", linewidth = 0.4) +
  ggplot2::geom_text(ggplot2::aes(label = sprintf("%.2f", spearman_rho)), size = 3.5) +
  ggplot2::scale_fill_gradient2(low = "#2C7BB6", mid = "white", high = "#D7191C", midpoint = 0, limits = c(-1, 1), name = "Spearman\nrho") +
  ggplot2::labs(x = NULL, y = NULL, title = "Core-7 predictor correlation") +
  ggplot2::theme_minimal(base_size = 11) +
  ggplot2::theme(panel.grid = ggplot2::element_blank(), axis.text.x = ggplot2::element_text(angle = 45, hjust = 1), plot.title = ggplot2::element_text(face = "bold"))
stem <- "Figure_Core7_Spearman_Correlation"
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".pdf")), p, width = 6.4, height = 5.8, device = grDevices::pdf)
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".tiff")), p, width = 6.4, height = 5.8, dpi = 600, device = ragg::agg_tiff, compression = "lzw")
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".png")), p, width = 6.4, height = 5.8, dpi = 600, device = ragg::agg_png)
writeLines(trimws(capture.output(utils::sessionInfo()), which = "right"), file.path(out, "14_CODE", "R_sessionInfo.txt"))
