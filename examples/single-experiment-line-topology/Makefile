CONFIG_FILE ?= config.py
RESULTS_FILE ?= results.pickle

.PHONY: check_icarus_installed run

check_icarus_installed:
	[ -x "$(shell which icarus)" ] || { echo "Icarus is not installed. Install it first."; exit 1; }

run: check_icarus_installed
	echo "Run experiments"
	icarus run --results $(RESULTS_FILE) $(CONFIG_FILE)

clean:
	rm -rf $(RESULTS_FILE)

all: run
