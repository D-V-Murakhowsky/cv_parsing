#!/usr/bin/env python3
import os
import pathlib

import click
import pandas as pd

from app.companies_parser import CompaniesParser
from app.jobs_parser import JobParser


def make_pathlib_path(path_string: str) -> pathlib.Path:
    if os.path.isabs(path_string):
        return pathlib.Path(path_string)
    else:
        return pathlib.Path(__file__).parent.resolve() / path_string


@click.group(help="Indeed parser CLI.")
def cli():
    """Application CLI group.
    """
    pass


@cli.command("parse_jobs", help="Start jobs parsing")
@click.option("-s", "--settings", default="", help="Path to settings file")
@click.option("-o", "--output", default="", help="Output file")
def parse_jobs(settings: str = 'assets/settings.json'):
    """Runs jobs parsing."""
    if (pathlib_path := pathlib.Path(settings)).is_file():
        pass
    elif (pathlib_path := pathlib.Path(__file__).parent.resolve() / settings).is_file():
        pass
    else:
        print('Path not exists.\nProgram terminated.')
    parsed_data = JobParser(pathlib_path).parse()
    pd.to_csv(parsed_data)


@cli.command("parse_companies", help="Start companies parsing")
@click.option("-o", "--output", default="", help="Output file")
def parse_jobs(output_file):
    """Runs companies parsing."""
    comp_infos = CompaniesParser.company_info_results()
    CompaniesParser.dump_to_file(comp_infos, make_pathlib_path(output_file))


if __name__ == "__main__":
    cli()