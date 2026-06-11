library(data.table)
library(ggplot2)
library(yaml)

.args <- if (interactive()) {
  c("configs/config.yml", "model_output/SIR_plot.png")
} else {
  commandArgs(trailingOnly = TRUE)
}

# read in config file
config <- yaml::read_yaml(.args[1])
if (is.null(names(config$backend))) {
  config$backend <- list(default = config$backend[[1]])
}
if (is.null(config$simulate[[1]]$backend)) {
  config$simulate[[1]]$backend <- "default"
}
# get the backend info - which did simulate use, and what is its root path
backend <- config$backend[[config$simulate[[1]]$backend]]

# for csv results, the results path is either the backend root, or "model_output" by default
results_path <- if (!is.null(backend$root)) {
  backend$root
} else {
  "model_output"
}

# resolve state names from the first system's spec
state_names <- unlist(config$system[[1]]$spec$state)
if (is.null(state_names) || length(state_names) == 0) {
  stop("system spec must define a non-empty 'state' list")
}
col_names <- c("time", state_names)

# get the most recently recorded result
results_dt <- tail(
  list.files(results_path, pattern = backend$module, full.names = TRUE),
  1
) |>
  fread() |>
  setnames(col_names) |>
  melt(id.vars = "time", variable.name = "compartment")

p <- ggplot(results_dt) +
  aes(time, value, color = compartment) +
  geom_line(linewidth = 1.2) +
  theme_minimal()

output_file <- tail(.args, 1)

ggsave(output_file, plot = p, width = 6, height = 4, bg = "white")
