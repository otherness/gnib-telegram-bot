#!/usr/local/bin/python3

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

params = {
    'readform': '',
    'cat': 'Work',
    'sbcat': 'All',
    'typ': 'New',
}

url = 'https://burghquayregistrationoffice.inis.gov.ie/Website/AMSREG/AMSRegWeb.nsf/(getAppsNear)'


def query_data():
    # Get nearest appointments from INIS site
    response = requests.get(url, params, verify=False)

    if response.status_code == 200:
        resp_dict = response.json()
        print('SUCCESS', resp_dict)
        return resp_dict

    print(response)
    return None


if __name__ == '__main__':
    query_data()
