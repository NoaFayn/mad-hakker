# largelog_extractor
This Python script can be used to parse a large log file (like syslog) containing lines ordered by date, and extract a specific interval.

## Features
* Works with log files of any size
* Supports any log format that write one log per line and has a date

## Requirements
- Python 3.9
- Pip

## Installation
1. Create the python virtual environment
```bash
python3.9 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies
```bash
python -m pip install -r requirements.txt
```

3. Ensure that you have the madhac lib accessible in your PYTHONPATH

Running the following command from the `Python_LargeLogExtractor` folder:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/../lib
```

If you want to make the path to the lib persistent to your venv, you can create a `.pth` file in the `site-packages` directory of your venv:
```bash
echo $(pwd)/../lib > $(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")/madhac.pth
```

## Usage
```text
usage: largelog_extractor.py [-h] [--prop PROPERTY VALUE] [-v] [-q] [--raw] [--log-year LOG_YEAR]
                             input output start_datetime end_datetime

This script parses a large log file (like syslog) that has some kind of line order (like dates), and extracts specific lines.
Mad Hakker

positional arguments:
  input                 Large log file
  output                Output file
  start_datetime        Starting datetime to extract
  end_datetime          Ending datetime

optional arguments:
  -h, --help            show this help message and exit
  --prop PROPERTY VALUE
                        Set a property manually (this overrides the properties.json file)
  -v, --verbose         verbosity level (-v for verbose, -vv for debug)
  -q, --quiet           Show no information at all
  --raw                 Print without formatting the output
  --log-year LOG_YEAR   Year for the dates found in the log file. By default, the current year

available properties:
   log_line_regex   The regex for a log line                                   
   regex_group_nb   The capturing group of the regex that is the date to parse 
   log_date_format  The time format captured in the regex group number         
```

## Basic examples
Retrieve logs for the 18 Nov 2022 in the `out/out.log` file:
```bash
python largelog_extractor.py /var/log/syslog out/out.log 18/11/2022 18/11/2022
```
