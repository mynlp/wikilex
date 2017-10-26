#!/usr/bin/env bash
virtualenv -p /usr/bin/python3 py3env
source py3env/bin/activate
pip install click
pip install lxml
