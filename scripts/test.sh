#!/usr/bin/env bash
set -e

coverage run --source=dirk -m unittest dirk/*_test.py dirk/**/*_test.py
coverage lcov
coverage report