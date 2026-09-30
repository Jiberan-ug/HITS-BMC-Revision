args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Pass the WP2 output directory")
out <- normalizePath(args[[1]], mustWork = TRUE)
src_dir <- file.path(out, "13_FIGURE_SOURCES")
flow <- read.csv(file.path(out, "10_HIGH_SPECIFICITY", "HIGH_SPECIFICITY_FLOW_FINAL.csv"), stringsAsFactors = FALSE)
get_n <- function(stage) {
  z <- flow$N[flow$stage == stage]
  if (length(z) != 1) stop(paste("Missing flow stage", stage))
  z
}
nodes <- data.frame(
  x = c(0.5, 1.8, 1.8, 1.8, 3.2, 3.2, 1.8, 3.2, 3.2, 4.7),
  y = c(0.82, 0.98, 0.76, 0.54, 0.67, 0.43, 0.14, 0.22, 0.02, 0.54),
  label = c(
    sprintf("Primary definite AMI\nN = %d", get_n("primary_AMI")),
    sprintf("Early allocation\nN = %d", get_n("date_axis_early")),
    sprintf("Buffer allocation\nN = %d", get_n("date_axis_buffer")),
    sprintf("Later AMI\nN = %d", get_n("date_axis_later")),
    sprintf("High-specificity text rule met\nN = %d", get_n("later_high_specificity_AMI")),
    sprintf("Strict text rule not met\nN = %d", get_n("later_AMI_not_meeting_strict_text_rule")),
    sprintf("Broad late controls\nN = %d", get_n("later_broad_CAD_angina_controls")),
    sprintf("Strict controls retained\nN = %d", get_n("later_strict_CAD_angina_controls")),
    sprintf("Broad controls excluded\nN = %d", get_n("later_broad_controls_excluded")),
    sprintf("Final late comparison\nAMI = %d; controls = %d; N = %d", get_n("later_high_specificity_AMI"), get_n("later_strict_CAD_angina_controls"), get_n("later_high_specificity_comparison"))
  ),
  group = c("primary", rep("allocation", 3), "retained", "excluded", "allocation", "retained", "excluded", "final"),
  stringsAsFactors = FALSE
)
edges <- data.frame(
  x = c(0.88, 0.88, 0.88, 2.10, 2.35, 2.35, 2.10, 2.35, 2.35, 3.62, 3.62),
  y = c(0.82, 0.82, 0.82, 0.54, 0.54, 0.54, 0.14, 0.14, 0.14, 0.67, 0.22),
  xend = c(1.42, 1.42, 1.42, 2.35, 2.82, 2.82, 2.35, 2.82, 2.82, 4.28, 4.28),
  yend = c(0.98, 0.76, 0.54, 0.54, 0.67, 0.43, 0.14, 0.22, 0.02, 0.54, 0.54)
)
p <- ggplot2::ggplot() +
  ggplot2::geom_segment(data = edges, ggplot2::aes(x = x, y = y, xend = xend, yend = yend), arrow = grid::arrow(length = grid::unit(2.0, "mm")), colour = "grey45", linewidth = 0.6) +
  ggplot2::geom_label(data = nodes, ggplot2::aes(x, y, label = label, fill = group), linewidth = 0.35, label.r = grid::unit(0.04, "in"), size = 3.2, lineheight = 1.0, colour = "#222222") +
  ggplot2::scale_fill_manual(values = c(primary = "#DCEEF2", allocation = "#F3F1E8", retained = "#E3F0DD", excluded = "#F6E1D9", final = "#DCE8F5")) +
  ggplot2::coord_cartesian(xlim = c(0, 5.6), ylim = c(-0.1, 1.12), expand = FALSE, clip = "off") +
  ggplot2::labs(title = "High-specificity late-sample flow", subtitle = "Discharge-diagnosis text rule; not independent clinical adjudication", fill = NULL) +
  ggplot2::theme_void(base_size = 11) +
  ggplot2::theme(legend.position = "none", plot.title = ggplot2::element_text(face = "bold", hjust = 0.5), plot.subtitle = ggplot2::element_text(hjust = 0.5), plot.background = ggplot2::element_rect(fill = "white", colour = NA), panel.background = ggplot2::element_rect(fill = "white", colour = NA), plot.margin = ggplot2::margin(12, 12, 12, 12))
stem <- "Figure_HighSpecificity_Flow"
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".pdf")), p, width = 11.5, height = 6.0, device = grDevices::pdf)
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".tiff")), p, width = 11.5, height = 6.0, dpi = 600, device = ragg::agg_tiff, compression = "lzw")
ggplot2::ggsave(file.path(src_dir, paste0(stem, ".png")), p, width = 11.5, height = 6.0, dpi = 600, device = ragg::agg_png)
writeLines(trimws(capture.output(utils::sessionInfo()), which = "right"), file.path(out, "14_CODE", "R_sessionInfo.txt"))
