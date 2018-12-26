#!/usr/bin/env python
"""Run the Icarus simulator.

This script automatically adds Icarus source folder to the PYTHONPATH and then
executes the simulator according to the settings specified in the provided
configuration file.

Usage:

  icarus run -r RESULTS [-c CONFIG_OVERRIDE] [-v] config
  icarus results print [--json] RESULTS
  icarus results merge -o OUTPUT INPUT_1 ... INPUT_N

"""
import click

import icarus


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


read = icarus.registry.RESULTS_READER['PICKLE']
write = icarus.registry.RESULTS_WRITER['PICKLE']


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(icarus.__version__)
def main():
    pass


@main.command(context_settings=CONTEXT_SETTINGS)
@click.option('--results', '-r', required=True,
              help='The file on which results will be saved')
@click.option('--config-override', '-c', multiple=True,
              help='Override specific key=value parameter of configuration file')
@click.argument('config', nargs=1, required=True)
def run(results, config_override, config):
    """Run a set of simulations."""
    config_override = dict(c.split("=") for c in config_override) or None
    icarus.run(config, results, config_override)


@main.group(context_settings=CONTEXT_SETTINGS)
def results():
    """Process results from a previous simulation"""
    pass


@results.command('merge', context_settings=CONTEXT_SETTINGS)
@click.option('--output', '-o', nargs=1, required=True, help='The output file')
@click.argument('inputs', nargs=-1, required=True)
def merge_results(output, inputs):
    """Merge multiple results files into one."""
    write(sum((read(i) for i in inputs[1:]), read(inputs[0])), output)


@results.command('print', context_settings=CONTEXT_SETTINGS)
@click.option('--json', '-j', is_flag=True, help='Print results in JSON format')
@click.argument('path')
def print_results(json, path):
    """Print content of a results file."""
    rs = read(path)
    if json:
        print(rs.json(indent=4))
    else:
        print(rs.prettyprint())
