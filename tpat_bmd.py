#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A python utility for rendering a Test Pattern Descriptor file to Blackmagic Decklink output.

Requires https://github.com/nick-shaw/blackmagic-decklink-output

Usage: python tpat_bmd.py <tpat_file> <display_mode> [-p <pixel_format>] [-r <range>] [-m <matrix>] [-e <eotf>]
"""

__version__ = "2.0"
__license__ = "BSD 3-Clause License"
__maintainer__ = "Nick Shaw"
__email__ = "nick@orion-convert.com"


import argparse
import json
import sys
import numpy as np
from tpat import render_tpat
import blackmagic_output as bmo
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat


DISPLAY_MODES = {
    '1080p25': DisplayMode.HD1080p25,
    '1080p2997': DisplayMode.HD1080p2997,
    '1080p30': DisplayMode.HD1080p30,
    '1080p50': DisplayMode.HD1080p50,
    '1080p5994': DisplayMode.HD1080p5994,
    '1080p60': DisplayMode.HD1080p60,
    '1080i50': DisplayMode.HD1080i50,
    '1080i5994': DisplayMode.HD1080i5994,
    '1080i60': DisplayMode.HD1080i60,
    '2160p25': DisplayMode.Mode4K2160p25,
    '2160p2997': DisplayMode.Mode4K2160p2997,
    '2160p30': DisplayMode.Mode4K2160p30,
    '2160p50': DisplayMode.Mode4K2160p50,
    '2160p5994': DisplayMode.Mode4K2160p5994,
    '2160p60': DisplayMode.Mode4K2160p60,
}

PIXEL_FORMATS = {
    'yuv10': PixelFormat.YUV10,
    'rgb10': PixelFormat.RGB10,
    'rgb12': PixelFormat.RGB12,
}

MATRICES = {
    'rec709': bmo.Matrix.Rec709,
    'rec2020': bmo.Matrix.Rec2020,
}

EOTFS = {
    'sdr': bmo.Eotf.SDR,
    'hlg': bmo.Eotf.HLG,
    'pq': bmo.Eotf.PQ,
}


def main():
    """Main function for the tpat_bmd utility."""
    displaymode_options = list(DISPLAY_MODES.keys())
    pixelformat_options = ['YUV10', 'RGB10', 'RGB12']
    range_options = ['full', 'narrow']
    matrix_options = ['Rec709', 'Rec2020']
    eotf_options = ['SDR', 'HLG', 'PQ']

    parser = argparse.ArgumentParser()
    parser.add_argument('tpat_in', help="input T-PAT file")
    parser.add_argument('display_mode',
                        choices=displaymode_options,
                        help="display mode"
                        )
    parser.add_argument('-p',
                        choices=pixelformat_options,
                        default='YUV10',
                        help="pixel format (optional) Default: YUV10"
    )
    parser.add_argument('-r',
                        choices=range_options,
                        default=None,
                        help="range (optional) Overrides TPAT file range tag if specified"
    )
    parser.add_argument('-m',
                        choices=matrix_options,
                        default=None,
                        help="matrix (optional) Overrides TPAT file matrix tag if specified"
    )
    parser.add_argument('-e',
                        choices=eotf_options,
                        default=None,
                        help="eotf (optional) Overrides TPAT file eotf tag if specified"
    )
    args = parser.parse_args()

    try:
        with open(args.tpat_in) as f:
            tpat_data = json.load(f)

        (image, bits, name) = render_tpat(args.tpat_in)
        if bits < 32:
            image = image.astype(np.uint16) << (16 - bits)
        with BlackmagicOutput() as output:
            output.initialize()

            display_mode = DISPLAY_MODES[args.display_mode]

            pixel_format = PIXEL_FORMATS.get(
                str(args.p).lower(),
                PixelFormat.YUV10
            )

            # Determine narrow_range: -r flag overrides TPAT file's range tag
            if args.r is not None:
                narrow_range = str(args.r).lower() == 'narrow'
            elif 'range' in tpat_data:
                narrow_range = str(tpat_data['range']).lower() == 'narrow'
            else:
                narrow_range = True

            # Determine matrix: -m flag overrides TPAT file's matrix tag
            if args.m is not None:
                matrix_str = str(args.m).lower()
            elif 'matrix' in tpat_data:
                matrix_str = str(tpat_data['matrix']).lower()
            else:
                matrix_str = 'rec709'

            matrix = MATRICES.get(matrix_str, bmo.Matrix.Rec709)

            # Determine eotf: -e flag overrides TPAT file's eotf tag
            if args.e is not None:
                eotf_str = str(args.e).lower()
            elif 'eotf' in tpat_data:
                eotf_str = str(tpat_data['eotf']).lower()
            else:
                eotf_str = 'sdr'

            eotf_value = EOTFS.get(eotf_str, bmo.Eotf.SDR)
            eotf = {'eotf': eotf_value}

            output.display_static_frame(
                image,
                display_mode,
                pixel_format,
                matrix=matrix,
                hdr_metadata=eotf,
                narrow_range=narrow_range
            )

            input("Press Enter to stop...")

            output.display_solid_color((0.0, 0.0, 0.0), display_mode)

    except Exception as error:
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
