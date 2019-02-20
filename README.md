# 🍅 pytest-tomato 

pytest plugin for [tomato-bot](https://tomato-bot/)

## Installation
`pip install pytest-tomato`

## Usage
Nada, after installing pytest will publish test results to the tomato-bot 🍅

## Setting junit-xml path
In order to parse test results the tomato bot read junit xml files created by pytest junit plugin.
By default pytest doesn't generates this file so `pytest-tomato` enables junit xml generation.
If you want control the path of the xml pass `--junit-xml=<location>.xml` flag to pytest.
