save_figure_set <- function(plot, stem, output_dir, width, height) {
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  ggplot2::ggsave(file.path(output_dir, paste0(stem, ".pdf")), plot,
    width = width, height = height, units = "in", device = grDevices::pdf, bg = "white")
  ggplot2::ggsave(file.path(output_dir, paste0(stem, ".tiff")), plot,
    width = width, height = height, units = "in", dpi = 600, compression = "lzw", bg = "white")
  ggplot2::ggsave(file.path(output_dir, paste0(stem, ".png")), plot,
    width = width, height = height, units = "in", dpi = 600, bg = "white")
}

wp3_theme <- function(base_size = 11) {
  ggplot2::theme_classic(base_size = base_size) +
    ggplot2::theme(
      plot.title = ggplot2::element_text(face = "bold", color = "#111111"),
      plot.subtitle = ggplot2::element_text(color = "#333333"),
      axis.title = ggplot2::element_text(color = "#111111"),
      axis.text = ggplot2::element_text(color = "#222222"),
      legend.title = ggplot2::element_blank(),
      legend.position = "bottom",
      panel.grid = ggplot2::element_blank()
    )
}
