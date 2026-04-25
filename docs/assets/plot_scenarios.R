library(yaml)
library(data.table)
library(ggplot2)

.args <- if (interactive()) {
  c("configs/scenarios_config.yaml", "model_output", "output.png")
} else {
  commandArgs(trailingOnly = TRUE)
}

config <- read_yaml(.args[1])
results_dir <- .args[2]
results_dt <- list.files(results_dir, full.names = TRUE) |>
  lapply(fread) |>
  rbindlist(idcol = TRUE) |>
  setnames(c("scenario", "time", "S", "I", "R")) |>
  melt.data.table(id.vars = c("scenario", "time"), variable.name = "compartment", value.name = "count")

# r expand grid expansion is the opposite of the one in python:
# expands first item fully
# so we need to reverse the order of the parameters
scenarios <- as.data.table(expand.grid(rev(config$scenarios[[1]]$parameters)))[, scenario := seq_len(.N)]

p <- ggplot(results_dt[scenarios, on = .(scenario)]) + aes(x = time, y = count, color = compartment) +
    facet_grid(beta ~ gamma) +
    geom_line() +
    theme_bw()

output_file <- tail(.args, 1)

ggsave(output_file, p, width = 10, height = 8)
