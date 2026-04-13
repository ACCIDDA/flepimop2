library(yaml)
library(data.table)
library(ggplot2)

.args <- commandArgs(trailingOnly = TRUE)

config <- read_yaml(.args[1])
results_dir <- .args[2]
output_file <- tail(.args, 1)

