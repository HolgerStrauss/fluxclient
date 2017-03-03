
from getpass import getuser
import argparse
import time
import sys
import os

from io import StringIO

PROG_DESCRIPTION = 'Flux fcode/gcode convertor.'
PROG_EPILOG = ''


def gcode_2_fcode(params=None, input=None, output=None):
    parser = argparse.ArgumentParser(description=PROG_DESCRIPTION,
                                     epilog=PROG_EPILOG)
    parser.add_argument('-i', dest='input', type=str,
                        help='Input gcode file')
    parser.add_argument('-t', '--type', dest='head_type', type=str,
                        default='EXTRUDER', choices=['EXTRUDER', 'LASER',
                                                     'N/A'],
                        help='Set toolhead type, default is EXTRUDER')

    parser.add_argument('--cor', dest='correction', type=str,
                        default=None, choices=['A', 'H', 'N'],
                        help='Set correction, A=ALL, H=Do height only, N=No'
                             ' correction')
    parser.add_argument('--hel', dest='head_error_level',
                        type=int, default=None, help='Head error level')
    parser.add_argument('--fmd', dest='filament_detect', type=str,
                        default=None, choices=['Y', 'N'],
                        help='Set filament detect, only for extruder type')

    parser.add_argument(dest='output', type=str, nargs="?",
                        help='Ouput fcode file')

    options = parser.parse_args(params)

    from fluxclient.toolpath import GCodeParser, FCodeV1FileWriter

    title = os.path.splitext(os.path.basename(options.input))[0]
    ext_metadata = {
        "AUTHOR": getuser(),
        "TITLE": title,
        "CREATED_AT": time.strftime('%Y-%m-%dT%H:%M:%SZ',
                                    time.localtime(time.time())),
    }

    if options.head_error_level is not None:
        ext_metadata['HEAD_ERROR_LEVEL'] = str(options.head_error_level)
    if options.correction is not None:
        ext_metadata['CORRECTION'] = str(options.correction)
    if options.filament_detect is not None:
        ext_metadata['FILAMENT_DETECT'] = str(options.filament_detect)
    # ext_metadata['BACKLASH'] = 'Y'

    parser = GCodeParser()
    processor = FCodeV1FileWriter(
        options.output, options.head_type, ext_metadata, ())
    parser.set_processor(processor)
    parser.parse_from_file(options.input)
    processor.terminated()

    errors = processor.errors()
    if errors:
        for err in errors:
            sys.stderr.write(err)
            sys.stderr.write("\n")


def fcode_2_gcode(params=None, input=None, output=sys.stdout):
    parser = argparse.ArgumentParser(description=PROG_DESCRIPTION,
                                     epilog=PROG_EPILOG)
    parser.add_argument('-i', dest='input', type=str,
                        help='Input fcode file')
    # parser.add_argument('-I', dest='--include-preview', action='store_const',
    #                     const=True, default=False,
    #                     help='Output preview images')
    parser.add_argument(dest='output', type=str, nargs="?",
                        help='Output gcode file')

    options = parser.parse_args(params)

    from fluxclient.fcode.f_to_g import FcodeToGcode

    try:
        if options.input:
            input = open(options.input, "rb")

        if options.output:
            output = open(options.output, "w+")
        else:
            output = sys.stdout.buffer

        if not input:
            input = sys.stdin.buffer

        parser = FcodeToGcode()
        res = parser.upload_content(input.read())
        print("Check file:: " + str(res))
        tmp_output = StringIO()
        parser.f_to_g(tmp_output, include_meta=True)
        gcode = tmp_output.getvalue()
        output.write(gcode)
    finally:
        input.close()
        output.close()
