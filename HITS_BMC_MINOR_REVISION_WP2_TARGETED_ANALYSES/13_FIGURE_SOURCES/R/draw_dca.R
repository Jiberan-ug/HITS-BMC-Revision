args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Pass the WP2 output directory")
out <- normalizePath(args[[1]], mustWork = TRUE)
src_dir <- file.path(out, "13_FIGURE_SOURCES")
dca <- read.csv(file.path(out, "09_DCA", "DCA_CANONICAL_SOURCE.csv"), stringsAsFactors = FALSE)
model_order <- c("Clinical only", "Clinical + PIV", "Clinical + Core-7", "Clinical + Enhanced", "Treat all", "Treat none")
dca$model <- factor(dca$model, levels = model_order)
p <- ggplot2::ggplot(dca, ggplot2::aes(threshold_probability, net_benefit, colour = model, linetype = model)) +
  ggplot2::geom_line(linewidth = 0.85) +
  ggplot2::scale_colour_manual(values = c("#007C91", "#CC5A27", "#4D7C0F", "#7A5195", "#444444", "#999999")) +
  ggplot2::scale_linetype_manual(values = c(1, 1, 1, 1, 2, 3)) +
  ggplot2::labs(x = "Threshold probability", y = "Net benefit", colour = NULL, linetype = NULL, title = "Exploratory DCA on a common complete-case sample", subtitle = "Retrospective phenotype discrimination; not evidence of clinical utility") +
  ggplot2::theme_classic(base_size = 11) +
  ggplot2::theme(legend.position = "bottom", legend.box = "vertical", plot.title = ggplot2::element_text(face = "bold"))
stem <- "Figure_DCA_Canonical_OOF"
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".pdf")), p, width = 7.2, height = 6.0, device = grDevices::pdf)
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".tiff")), p, width = 7.2, height = 6.0, dpi = 600, device = ragg::agg_tiff, compression = "lzw")
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".png")), p, width = 7.2, height = 6.0, dpi = 600, device = ragg::agg_png)
writeLines(trimws(capture.output(utils::sessionInfo()), which = "right"), file.path(out, "14_CODE", "R_sessionInfo.txt"))
