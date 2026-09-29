args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Pass the WP2 output directory")
out <- normalizePath(args[[1]], mustWork = TRUE)
src_dir <- file.path(out, "13_FIGURE_SOURCES")
roc <- read.csv(file.path(src_dir, "ROC_CANONICAL_SOURCE.csv"), stringsAsFactors = FALSE)
perf <- read.csv(file.path(out, "03_PRIMARY_PERFORMANCE", "PRIMARY_MODEL_PERFORMANCE_CANONICAL.csv"), stringsAsFactors = FALSE)
plot_models <- c("PIV", "Core-7", "Enhanced (full cohort)")
label_map <- c("PIV" = "PIV", "Core-7" = "Core-7", "Enhanced (full cohort)" = "Enhanced")
performance_models <- unname(label_map[plot_models])
anno <- perf[perf$model %in% performance_models & perf$cohort_version == "primary_full_1820", , drop = FALSE]
if (!setequal(anno$model, performance_models)) stop("Canonical AUC result rows are incomplete")
anno$curve_model <- names(label_map)[match(anno$model, label_map)]
anno <- anno[match(plot_models, anno$curve_model), , drop = FALSE]
anno$legend <- paste0(unname(label_map[anno$curve_model]), " (AUC = ", sprintf("%.3f", anno$AUC), ")")
roc <- roc[roc$model %in% plot_models, , drop = FALSE]
roc$legend <- anno$legend[match(roc$model, anno$curve_model)]
roc$legend <- factor(roc$legend, levels = anno$legend)
p <- ggplot2::ggplot(roc, ggplot2::aes(false_positive_rate, true_positive_rate, colour = legend)) +
  ggplot2::geom_step(linewidth = 0.9, direction = "hv") +
  ggplot2::geom_abline(slope = 1, intercept = 0, linetype = 2, colour = "grey55") +
  ggplot2::coord_equal(expand = FALSE) +
  ggplot2::scale_x_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.2)) +
  ggplot2::scale_y_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.2)) +
  ggplot2::scale_colour_manual(values = c("#007C91", "#CC5A27", "#4D7C0F")) +
  ggplot2::labs(x = "False-positive rate", y = "True-positive rate", colour = NULL, title = "Canonical 5 × 10 out-of-fold ROC") +
  ggplot2::theme_classic(base_size = 11) +
  ggplot2::theme(legend.position = "bottom", legend.box = "vertical", plot.title = ggplot2::element_text(face = "bold"))
stem <- "Figure_ROC_Canonical_OOF"
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".pdf")), p, width = 6.6, height = 5.8, device = grDevices::pdf)
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".tiff")), p, width = 6.6, height = 5.8, dpi = 600, device = ragg::agg_tiff, compression = "lzw")
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".png")), p, width = 6.6, height = 5.8, dpi = 600, device = ragg::agg_png)
writeLines(trimws(capture.output(utils::sessionInfo()), which = "right"), file.path(out, "14_CODE", "R_sessionInfo.txt"))
