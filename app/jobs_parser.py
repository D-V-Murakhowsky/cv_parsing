import json
import logging
import pathlib
import re
from collections import defaultdict
from typing import Dict, Union, List

import pandas as pd
import requests
from bs4 import BeautifulSoup

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

    def __init__(self, settings_path: pathlib.Path) -> None:
        self.settings = self._read_settings(settings_path)
        self.logger = logging.getLogger('main_logger')

    def parse(self):
        data_frames: list = [self._parse_page(page_number)
                             for page_number in range(0, self.settings['count_page'], 10)]
        return pd.concat(data_frames)

    @staticmethod
    def _read_settings(settings_path: pathlib.Path) -> Union[Dict, None]:
        if settings_path.is_file():
            with open(settings_path, 'r') as file_object:
                return json.loads(file_object.read())
        else:
            return None

    @staticmethod
    def _get_list_with_re(input_line: str, regex_name: str) -> Union[List, None]:
        if krs := re.findall(REGEXES[regex_name], str(input_line)):
            return krs
        return None

    @classmethod
    def _get_string_with_re(cls, input_line: str, regex_name: str) -> Union[str, None]:
        if res := cls._get_list_with_re(input_line, regex_name):
            return ''.join(res)
        else:
            return None

    def _parse_page(self, page_num: int):
        self.logger.info(f'Start parsing page {page_num}')

        response, soup = self._make_request(page_num)

        if data_re := self._get_list_with_re(response.text, 'get_data'):
            reading_result = defaultdict(list)
            for record in data_re:
                job_id, job_id_param = self._get_job_id(record)

                for key in (PROPERTIES_LIST - {'job_id'}):
                    reading_result[key].append(self._get_string_with_re(record, f'job_{key}'))

                reading_result['long_description'].\
                    append(self._read_long_description(self._get_long_description_by_id(job_id_param),
                                                       reading_result['company_name'][-1]))

            if div_company_desc := soup.findAll('div', class_='job-snippet'):
                reading_result['job_desc'].extend([m.get_text() for m in div_company_desc])

            if div_res_content := soup.findAll('td', class_='resultContent'):
                reading_result['job_salary'].extend(self._get_salaries_list(div_res_content))

            return pd.DataFrame(reading_result)

    def _get_job_id(self, record):
        job_id = self._get_string_with_re(record, 'job_ids')
        job_id_param = ''.join(job_id)
        return job_id, job_id_param

    def _make_request(self, page_num):
        params = (
            ('q', self.settings["job_title"]),
            ('l', self.settings["location"]),
            ('start', str(page_num)),
        )
        response = requests.get(self.settings['url'], params=params)
        soup = BeautifulSoup(response.content, "html.parser")
        return response, soup

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

    def _get_long_description_by_id(self, job_id_param):
        self.logger.info('Try inner request for long job desc:')
        self.logger.info(f'{self.settings["job_details_url"]}={job_id_param}')
        long_desc_res = requests.get(f'{self.settings["job_details_url"]}={job_id_param}')
        long_desc_soup = BeautifulSoup(long_desc_res.content, "html.parser")
        return long_desc_soup.find('div', id='jobDescriptionText')

    @staticmethod
    def _read_long_description(obj_to_parse, company_name) -> str:
        if obj_to_parse:
            return obj_to_parse.get_text()
        else:
            return f'Error reading long description of {company_name}'
