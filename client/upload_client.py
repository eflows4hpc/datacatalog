#!/usr/bin/env python3

import argparse
import getpass
import json
from urllib.parse import urljoin
import sys

import requests

def login(server, user, password):
    r = requests.post(urljoin(server, 'token'),
                      data={'username': user, 'password': password})

    if r.status_code!=200:
        print("Unable to authenticate. Breaking")
        sys.exit(-1)

    token = r.json()['access_token']
    return {'Authorization': f"Bearer {token}"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Uploads data to apiserver')
    parser.add_argument('-s', '--server', help='server url',
                        default='http://localhost:8000/')
    parser.add_argument('-u', '--user', help='user name', required=True)
    parser.add_argument('-f', '--dataset',
                        help='json file with dataset', required=True)
    args = parser.parse_args()

    password = getpass.getpass(prompt='Password required')
    auth_headers = login(args.server, args.user, password)

    lst = requests.get(urljoin(args.server, 'dataset')).json()
    datasets = {a[0]: a[1] for a in lst}

    with open(args.dataset, 'r') as f:
        ds = json.load(f)

    for el in ds:
        if el['name'] in datasets:
            print(f"{el['name']} is already on sever (id={datasets[el['name']]}). Updating...")
            r = requests.put(url=urljoin(args.server, f"dataset/{datasets[el['name']]}"),
                json=el, headers=auth_headers)
        else:
            r = requests.post(urljoin(args.server, 'dataset'),
                            json=el, headers=auth_headers)
        if r.status_code==200:
            print(f"Sent {el['name']} -> {r.json()[0]}")
        else:
            print(r.url, r.status_code, r.text)

    print('Data sets on the server:')
    r = requests.get(urljoin(args.server, 'dataset'))
    for el in r.json():
        print(el)
