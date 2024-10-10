#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @created: 18 Nov 2022

import madhac.app as mapp
import os
import datetime
import io
import locale
import re

# The regex for a log line
PROP_LOG_LINE_REGEX = 'log_line_regex'
DEFAULT_LOG_LINE_REGEX = r'^(.+?[ \t]+\d+)[ \t]+(\d+:\d+:\d+)[ \t]+(.*)$'
# The capturing group of the regex that is the date to parse
PROP_REGEX_GROUP_NB = 'regex_group_nb'
DEFAULT_REGEX_GROUP_NB = 1
# The time format captured in the regex group number
PROP_LOG_DATE_FORMAT = 'log_date_format'
DEFAULT_LOG_DATE_FORMAT = '%b %d'


class UnknownLogformat(Exception):
    def __init__(self, line: str, *args: object) -> None:
        super().__init__(*args)
        self.line = line


class DateNotFound(Exception):
    pass


class ParseLogApp(mapp.App):
    def line_at_offset(self, fin: io.TextIOWrapper, offset: int):
        """Given an offset, returns the corresponding line.
        The offset must start at the begining of the line.
        """
        fin.seek(offset)
        return fin.readline()

    def previous_line_offset(self, fin: io.TextIOWrapper, line_offset: int):
        """Given a line offset, returns the previous line offset.
        ```text
        line(i)     O=-=-=-=-=-=-=
        line(i+1)   I=-=-=-=-=-=-=
        line(i+2)   -=-=-=-=-=-=-=
        ```
        """
        return self.line_offset(line_offset - 2, fin)

    def line_offset(self, offset: int, fin: io.TextIOWrapper):
        """Given any offset, returns the start of the line offset.
        """
        # TODO(noa): OPTIMISE THIS!!!
        offset -= 1
        if offset < 0:
            # Offset is start of the file
            return 0
        fin.seek(offset)
        try:
            b = fin.read(1)
        except UnicodeDecodeError:
            # Ignored: we don't care about anything but line breaks
            b = '?'
        while b != '\n':
            offset -= 1
            if offset < 0:
                # Offset is start of the file
                return 0
            fin.seek(offset)
            try:
                b = fin.read(1)
            except UnicodeDecodeError:
                # Ignored: we don't care about anything but line breaks
                pass
        offset += 1
        return offset

    def get_datetime(self, line: str):  # type: ignore
        """Given a syslog line, returns the datetime object corresponding to this line.
        The provided line must not be empty.
        """
        # Clean string
        line = line.strip('\x00')
        m = re.match(self.log_line_regex, line)
        if not m:
            raise UnknownLogformat(line)
        parsed_date = datetime.datetime.strptime(m[1], self.log_date_format)
        parsed_date = parsed_date.replace(year=self.options.log_year)
        return parsed_date

    def get_known_datetime(self, fin: io.TextIOWrapper, line_offset: int, direction='backward'):
        """Given a valid starting syslog line, finds the first log line which format is valid and return the corresponding datetime object for this line.
        The direction controls whether to find the next log line forward or backward. The default is backward search.

        Returns a tuple with the date and offset at which the date was found.
        """
        date = None
        while not date:
            line = self.line_at_offset(fin, line_offset)
            try:
                date = self.get_datetime(line)
            except UnknownLogformat:
                date = None
                if direction == 'forward':
                    # TODO(noa): If we have the last line of the syslog and we can't parse it, then we cannot complete the operation
                    if line_offset == self.max_size:
                        raise Exception('The log format of the last line is unknown. Cannot proceed.')
                    line_offset = fin.tell()
                else:
                    # If we have the first line of the syslog and we can't parse it, then we cannot complete the operation
                    if line_offset == 0:
                        raise Exception('The log format of the first line is unknown. Cannot proceed.')
                    line_offset = self.line_offset(line_offset - 2, fin)
        return (date, line_offset)

    def find_line_around_date(self, fin: io.TextIOWrapper, start_offset: int, end_offset: int, find_date: datetime.datetime):
        """Given a date, returns the line offset of a log line that matches this date.
        The line offset is not necessarily the first log line at this date.
        The search is performed by dichotomy.
        """
        while True:
            # Perform dichotomy search of an offset to start search
            offset = int(start_offset + (end_offset - start_offset) / 2)

            # Find the closest line at this offset
            offset = self.line_offset(offset, fin)

            # Find a log line with a valid date
            date, line_offset = self.get_known_datetime(fin, offset)
            # Here, we are at the start of a line, so read it
            line = self.line_at_offset(fin, line_offset)
            # If the line offset is before the start offset, then take the first line after the start offset and use this one
            if line_offset < start_offset:
                self.logger.warning(f'Found a log line but could not determine its date: {line}')

            # Check the date found, and update the offset accordingly
            if date > find_date:
                end_offset = offset
            elif date < find_date:
                # If we already have this offset, then the date to find is not in the range searched
                if start_offset == offset:
                    self.logger.warning(f'No logs for searched date: {find_date}')
                    # return offset
                    raise DateNotFound(f'Date ({find_date}) not found')
                start_offset = offset
            else:
                # We have an approximation of the starting offset
                return offset
            if start_offset >= end_offset:
                raise DateNotFound(f'Date ({find_date.isoformat()}) not found')

    def extract_between_offsets(self, f_in: str, f_out: str, start_offset: int, end_offset: int):
        """Given a starting and ending offset, extracts the portion of the input file and writes the output file.
        """
        # Create output file folders
        os.makedirs(os.path.dirname(f_out), exist_ok=True)
        # We use binary mode because of UTF-8
        with open(f_in, 'rb') as fin, open(f_out, 'wb') as fout:
            fin.seek(start_offset)
            fout.write(fin.read(end_offset - start_offset))

    def find_previous_date(self, fin: io.TextIOWrapper, offset: int, current_date: datetime.datetime):
        """Given a current line offset, finds a previous log line with older date.
        Returns the offset of the log line with older date, and the offset of the next log line (with current_date).
        """
        previous_line_offset = offset
        # Read line date
        date, line_offset = self.get_known_datetime(fin, previous_line_offset)
        # Check if date is older
        while date >= current_date:
            # false: find a previous date
            previous_offset = self.previous_line_offset(fin, line_offset)
            # If previous_offset is SOF, then we consider the first line as the line to return
            if previous_offset == 0:
                self.logger.warning(f'Reached SOF while searching for previous date of {current_date}')
                return (0, 0)

            previous_line_offset = line_offset
            date, line_offset = self.get_known_datetime(fin, previous_offset)

        # true: return it
        return (line_offset, previous_line_offset)

    def find_next_date(self, fin: io.TextIOWrapper, offset: int, current_date: datetime.datetime):
        """Given a current line offset, finds the next log line with newer date.
        Returns the offset of the log line with newer date, and the offset of the previous log line (with current_date).
        """
        previous_line_offset = offset
        # Read line date
        date, line_offset = self.get_known_datetime(fin, offset, 'forward')
        # Check if date is newer
        while date <= current_date:
            # false: find a next date
            next_offset = fin.tell()
            # If next_offset is EOF, then we consider the last line as the one to return
            if next_offset == self.max_size:
                self.logger.warning(f'Reached EOF while searching for next date of {current_date}')
                return (line_offset, line_offset)

            previous_line_offset = line_offset
            date, line_offset = self.get_known_datetime(fin, next_offset, 'forward')

        # true: return it
        return (line_offset, previous_line_offset)

    def main(self):
        # Parse properties to speed things up
        # log line regex
        self.log_line_regex = re.compile(mapp.properties.get(PROP_LOG_LINE_REGEX, DEFAULT_LOG_LINE_REGEX))
        # log date format
        self.log_date_format = mapp.properties.get(PROP_LOG_DATE_FORMAT, DEFAULT_LOG_DATE_FORMAT)

        # Print locale (because of date parsing, might be useful to know)
        self.logger.info(f'Locale used: {locale.getlocale()}')

        # Open input file and stats about it
        fin = open(self.options.input, 'r')
        self.max_size = os.path.getsize(self.options.input)
        self.logger.info(f'File is {self.max_size} bytes')
        self.logger.info('Starting dichotomy search')

        # TODO(noa): Make it more generic than just dates
        # Parse requested dates
        start_date = datetime.datetime.strptime(self.options.start_datetime, '%d/%m/%Y')
        end_date = datetime.datetime.strptime(self.options.end_datetime, '%d/%m/%Y')
        if end_date < start_date:
            self.logger.error('End date is before start date')
            return
        self.logger.info(f'Extracting logs between {start_date} and {end_date}')

        # Search starting date
        min_offset = 0
        max_offset = self.max_size
        self.logger.info('Searching for a line around starting date...')
        try:
            start_offset = self.find_line_around_date(fin, min_offset, max_offset, start_date)
            self.logger.success('Found log line around starting date')

            self.logger.info('Searching for the first log line (this can take some time)...')
            # Go back until the first log line is found for this date
            _, start_offset = self.find_previous_date(fin, start_offset, start_date)
            self.logger.success(f'First log line found at offset ({start_offset})!')
        except DateNotFound:
            # If date not found, then use first line of file
            start_offset = 0
            self.logger.error('Starting date not found, using start of file')

        # Now search for the ending date
        self.logger.info('Searching for a line around the ending date...')
        min_offset = start_offset
        max_offset = self.max_size
        try:
            end_offset = self.find_line_around_date(fin, min_offset, max_offset, end_date)
            self.logger.success('Found log line around ending date')

            self.logger.info('Searching for the last log line (this can take some time)...')
            # Go forward until the last log is found for this date
            last_offset, _ = self.find_next_date(fin, start_offset, end_date)
            end_offset = last_offset - 1
            self.logger.success(f'Last log line found at offset ({end_offset})!')
        except DateNotFound:
            # If no ending date, use the EOF
            # TODO(noa): might not be the right solution for all cases
            self.logger.info('No ending date found, using EOF as last line to extract')
            end_offset = self.max_size

        self.logger.success(f'Start offset: {start_offset}')
        self.logger.success(f'End offset: {end_offset}')

        # Close input file
        fin.close()

        # Extract file between offsets
        self.extract_between_offsets(self.options.input, self.options.output, start_offset, end_offset)


if __name__ == "__main__":
    app = ParseLogApp(app_description='This script parses a large log file (like syslog) that has some kind of line order (like dates), and extracts specific lines.')

    app.register_property(PROP_LOG_LINE_REGEX, 'The regex for a log line')
    app.register_property(PROP_REGEX_GROUP_NB, 'The capturing group of the regex that is the date to parse')
    app.register_property(PROP_LOG_DATE_FORMAT, 'The time format captured in the regex group number')

    parser = app.get_parser()
    parser.add_argument(
        'input',
        help='Large log file',
    )
    parser.add_argument(
        'output',
        help='Output file',
    )
    parser.add_argument(
        'start_datetime',
        help='Starting datetime to extract',
    )
    parser.add_argument(
        'end_datetime',
        help='Ending datetime',
    )

    parser.add_argument(
        '--log-year',
        type=int,
        default=datetime.datetime.now().year,
        help='Year for the dates found in the log file. By default, the current year',
    )

    app.init(app.main)
