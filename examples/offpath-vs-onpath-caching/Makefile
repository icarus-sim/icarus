CONFIG_FILE ?= config.py
RESULTS_FILE ?= results.pickle
PLOTS_DIR ?= plots

.PHONY: check_installed run plot clean

all: run plot

check_installed:
	@[ -x "$(shell which icarus)" ] || { echo "Icarus is not installed. Install it first."; exit 1; }

run: check_installed
	@echo "Run experiments..."
	icarus run --results $(RESULTS_FILE) $(CONFIG_FILE)

plot: check_installed
	@echo "Plot results..."
	python plotresults.py --results $(RESULTS_FILE) --output $(PLOTS_DIR) $(CONFIG_FILE)

clean:
	rm -rf $(RESULTS_FILE) $(PLOTS_DIR)
