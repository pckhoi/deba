#!/usr/bin/env bash

coverage run --source=dirk -m unittest dirk/**/*_test.py
coverage lcov