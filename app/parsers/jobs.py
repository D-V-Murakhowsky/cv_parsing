import requests
from bs4 import BeautifulSoup
import os
import sys
import csv
import re
from itertools import zip_longest
import logging
import pandas as pd
import pathlib
from typing import Dict, Union, List
import json
from collections import defaultdict

FIELD_NAMES = ['Job_ID', 'Job_Title', 'Company_Name', 'Price', 'Location', 'Job_Description', 'Country', 'City',
               'Long Job_Description']
REGEXES = {'get_data': r'\sjobmap\[\d+\]=\s(.*);',
           'job_ids': r"""jk:'(.*?)'""",
           'job_title': r"""title:'(.*?)'""",
           'job_location': r"""loc:'(.*?)'""",
           'job_country': r"""country:'(.*?)'""",
           'job_city': r"""city:'(.*?)'""",
           'job_company_name': r"""cmp:'(.*?)'"""}
PROPERTIES_LIST = {'job_id', 'title', 'company_name', 'location', 'country', 'city'}


class JobParser:

    def __init__(self, settings_file: str) -> None:
        self.settings = self._read_settings(settings_file)
        self.logger = logging.getLogger('main_logger')

    @staticmethod
    def _read_settings(file_path: str) -> Union[Dict, None]:
        path = pathlib.Path(__file__).parents[2].resolve() / f'assets/{file_path}'
        if path.is_file():
            with open(path, 'r') as file_object:
                return json.loads(file_object.read())
        else:
            return None

    def parse(self):
        data_frames: list = []
        for page_number in range(0, self.settings['count_page'], 10):
            data_frames.append(self._parse_page(page_number))
        return pd.concat(data_frames)

    @staticmethod
    def _get_string_with_re(input_line: str, regex_name: str) -> Union[List, None]:
        if krs := re.findall(REGEXES[regex_name], str(input_line)):
            return krs
        return None

    def _parse_page(self, page_num: int):
        self.logger.info(f'Start parsing page {page_num}')
        params = (
            ('q', self.settings["job_title"]),
            ('l', self.settings["location"]),
            ('start', str(page_num)),
        )
        response = requests.get(self.settings['url'], params=params)
        soup = BeautifulSoup(response.content, "html.parser")
        data_re = self._get_string_with_re(response.text, 'get_data')
        if data_re:
            reading_result = defaultdict(list)
            for record in data_re:
                job_id = self._get_string_with_re(record, 'job_ids')
                job_id_param = ''.join(job_id)
                reading_result['job_id'].append(job_id)

                for key in (PROPERTIES_LIST - {'job_id'}):
                    reading_result[key].append(self._get_string_with_re(record, f'job_{key}'))

                print(30 * '+')
                print('Try inner request for long job desc:')
                print(f'https://ca.indeed.com/viewjob?jk={job_id_param}')

                reading_result['long_description'].\
                    append(self._read_long_description(self._get_long_description_by_id(job_id_param),
                                                       reading_result['company_name'][-1]))

            if div_company_desc := soup.findAll('div', class_='job-snippet'):
                reading_result['job_desc'].extend([m.get_text() for m in div_company_desc])

            if div_res_content := soup.findAll('td', class_='resultContent'):
                reading_result['job_salary'].extend(self._get_salaries_list(div_res_content))

            return pd.DataFrame(reading_result)

    @classmethod
    def _get_salaries_list(cls, salaries_soup):
        result = []
        for res_c in salaries_soup:
            if div_company_salary := res_c.findAll('div', class_='metadata salary-snippet-container'):
                for t in div_company_salary:
                    result.append(t.get_text())
            else:
                result.append('')
        return result

    @staticmethod
    def _get_long_description_by_id(job_id_param):
        long_desc_res = requests.get(f'https://ca.indeed.com/viewjob?jk={job_id_param}')
        long_desc_soup = BeautifulSoup(long_desc_res.content, "html.parser")
        return long_desc_soup.find('div', id='jobDescriptionText')

    @staticmethod
    def _read_long_description(obj_to_parse, company_name) -> str:
        if obj_to_parse:
            return obj_to_parse.get_text()
        else:
            return f'Error reading long description of {company_name}'
