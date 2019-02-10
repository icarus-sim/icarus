CONFIG_FILE ?= config.py
RESULTS_FILE ?= results.pickle
PLOTS_DIR ?= plots

.PHONY: check_icarus_installed run plot clean

check_icarus_installed:
	[ -x "$(shell which icarus)" ] || { echo "Icarus is not installed. Install it first."; exit 1; }

run: check_icarus_installed
	echo "Run experiments"
	icarus run --results $(RESULTS_FILE) $(CONFIG_FILE)

plot: check_icarus_installed
	echo "Plot results"
	python plotresults.py --results $(RESULTS_FILE) --output $(PLOTS_DIR) $(CONFIG_FILE)

clean:
	rm -rf $(RESULTS_FILE) $(PLOTS_DIR)

all: run plot
