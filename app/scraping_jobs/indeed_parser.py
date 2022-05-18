import requests
from bs4 import BeautifulSoup
import os
import sys
import csv
import re
from itertools import zip_longest
import pandas as pd
import pathlib
from typing import Dict, Union
import json

PARSE_URL = 'https://ca.indeed.com/jobs'

class JobParser:

    def __init__(self, url: str, settings_file: str) -> None:
        self.url = url

    @staticmethod
    def _read_settings(file_path: str) -> Union[Dict, None]:
        path = pathlib.Path(__file__).parent.resolve() / file_path
        if path.is_file():
            return json.loads(open(path).read())
        else:
            return None


    @staticmethod
    def parse_string():
        return None

def get_data(str_find):
    krs = re.findall(
        r"""\sjobmap\[\d+\]=\s(.*);""",
        str(str_find))
    if krs:
        return krs
    return None


def job_ids(str_find):
    krs = re.findall(
        r"""jk:'(.*?)'""",
        str(str_find))
    if krs:
        return krs
    return None


def job_title(str_find):
    krs = re.findall(
        r"""title:'(.*?)'""",
        str(str_find))
    if krs:
        return krs
    return None


def job_location(str_find):
    krs = re.findall(
        r"""loc:'(.*?)'""",
        str(str_find))
    if krs:
        return krs
    return None


def job_country(str_find):
    krs = re.findall(
        r"""country:'(.*?)'""",
        str(str_find))
    if krs:
        return krs
    return None


def job_city(str_find):
    krs = re.findall(
        r"""city:'(.*?)'""",
        str(str_find))
    if krs:
        return krs
    return None


def job_company_name(str_find):
    krs = re.findall(
        r"""cmp:'(.*?)'""",
        str(str_find))
    if krs:
        return krs
    return None


if __name__ == '__main__':

    with open(FILE_NAME_CSV, 'a', newline='') as csv_file:
            fieldnames = ['Job_ID', 'Job_Title', 'Company_Name', 'Price', 'Location', 'Job_Description', 'Country', 'City',
                          'Long Job_Description']
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(fieldnames)
            csv_file.close()

    try:
        for i in range(0, count_page, 10):
            print(50 * '=')
            print(f'Parse {i} page')
            params = (
                ('q', jobtitle),
                ('l', location),
                ('start', str(i)),
            )
            response = requests.get(PARSE_URL, params=params)
            soup = BeautifulSoup(response.content, "html.parser")
            # print(response.content)
            data_re = get_data(response.text)
            # print(1111111, data_re)
            if data_re:
                job_salary_lst = []
                job_id_lst = []
                title_lst = []
                c_m_lst = []
                location_lst = []
                country_lst = []
                city_lst = []
                job_desc_lst = []
                long_desc_lst = []
                job_id = None
                title = None
                c_m = None
                location = None
                country = None
                city = None
                long_desc = None
                try:
                    for el in data_re:
                        job_id = job_ids(el)
                        job_id_param = ''.join(job_id)
                        title = job_title(el)
                        c_m = job_company_name(el)
                        location = job_location(el)
                        country = job_country(el)
                        city = job_city(el)

                        job_id_lst.append(''.join(job_id))
                        title_lst.append(''.join(title))
                        c_m_lst.append(''.join(c_m))
                        location_lst.append(''.join(location))
                        country_lst.append(''.join(country))
                        city_lst.append(''.join(city))
                        print(30 * '+')
                        print('Try inner request for long job desc:')
                        print(f'https://ca.indeed.com/viewjob?jk={job_id_param}')
                        long_desc_res = requests.get(f'https://ca.indeed.com/viewjob?jk={job_id_param}')
                        long_desc_soup = BeautifulSoup(long_desc_res.content, "html.parser")
                        # print(666666666, long_desc_soup)
                        div_long_desc = long_desc_soup.find('div', id='jobDescriptionText')
                        if div_long_desc:
                            long_desc = div_long_desc.get_text()
                            long_desc_lst.append(long_desc)
                        else:
                            print(f'No data for job long description {job_id_param}!!!')
                            file = open(FILE_NAME_ERROR, 'a')
                            file.write(f"!!!!!!!!!!! No data for long job description: {i} for {job_id_param}\n")
                            file.close()

                    print("job_id_lst:", job_id_lst)
                    print("title_lst:", title_lst)
                    print("c_m_lst:", c_m_lst)
                    print("location_lst:", location_lst)
                    print("country_lst:", country_lst)
                    print("city_lst:", city_lst)
                    print("long_desc_lst:", long_desc_lst)

                    div_company_desc = soup.findAll('div', class_='job-snippet')
                    if div_company_desc:
                        for m in div_company_desc:
                            job_desc = m.get_text()
                            job_desc_lst.append(job_desc)
                        print("job_desc_lst:", job_desc_lst)
                    else:
                        print('No data for job description !!!')
                        file = open(FILE_NAME_ERROR, 'a')
                        file.write(f"!!!!!!!!!!! No data for job description: {i}\n")
                        file.close()

                    div_res_content = soup.findAll('td', class_='resultContent')
                    if div_res_content:
                        for res_c in div_res_content:
                            job_salary = ''
                            div_company_salary = res_c.findAll('div', class_='metadata salary-snippet-container')

                            if div_company_salary:
                                for t in div_company_salary:
                                    job_salary = t.get_text()
                                    # print(99999, job_salary)
                            job_salary_lst.append(job_salary)
                    print('job_salary_lst:', job_salary_lst)

                    try:
                        with open(FILE_NAME_CSV, 'a', newline='') as csv_file:
                            for el1, el2, el3, el4, el5, el6, el7, el8, el9 in zip_longest(job_id_lst, title_lst, c_m_lst,
                                                                                           job_salary_lst, location_lst,
                                                                                           job_desc_lst, country_lst,
                                                                                           city_lst,
                                                                                           long_desc_lst):

                                all_data = [el1, el2, el3, el4, el5, el6, el7, el8, el9]
                                if len(all_data) != 0:
                                    writer = csv.writer(csv_file, delimiter=',')
                                    writer.writerow(all_data)
                            csv_file.close()

                    except Exception as er:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print(exc_type, fname, exc_tb.tb_lineno)
                        print(f'!!!!!!!!!!! exception block save to csv: {i}:  {er}')
                        file = open(FILE_NAME_ERROR, 'a')
                        file.write(f"!!!!!!!!!!! exception block  -> save to csv: {i}: {er}\n")
                        file.close()

                except Exception as er:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    print(f'!!!!!!!!!!! exception block json loads: {i}:  {er}')
                    file = open(FILE_NAME_ERROR, 'a')
                    file.write(f"!!!!!!!!!!! exception block json loads: {i}: {er}\n")
                    file.close()
            else:
                print('No data')
                file = open(FILE_NAME_ERROR, 'a')
                file.write(f"!!!!!!!!!!! No data: {i}\n")
                file.close()
    except Exception as er:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print(f'!!!!!!!!!!! exception block main:  {er}')
        file = open(FILE_NAME_ERROR, 'a')
        file.write(f"!!!!!!!!!!! exception block  -> main: {er}\n")
        file.close()
