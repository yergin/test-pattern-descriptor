#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A python utility for rendering a Test Pattern Descriptor file to Blackmagic Decklink output.

Requires https://github.com/nick-shaw/blackmagic-decklink-output

Usage: python tpat_bmd.py <tpat_file> -d <display_mode> [-p <pixel_format>] [-r <range>] [-m <matrix>] [-e <eotf>]
"""

__version__ = "2.0"
__license__ = "BSD 3-Clause License"
__maintainer__ = "Nick Shaw"
__email__ = "nick@orion-convert.com"


import argparse
import numpy as np
from tpat import render_tpat
import blackmagic_output as bmo
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat


if __name__ == "__main__":
    modes = {
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
    
    displaymode_options = list(modes.keys())
    pixelformat_options = ['YUV10', 'RGB10', 'RGB12']
    range_options = ['full', 'narrow']
    matrix_options = ['Rec709', 'Rec2020']
    eotf_options = ['SDR', 'HLG', 'PQ']
    
    parser = argparse.ArgumentParser()
    parser.add_argument('tpat_in', help="input T-PAT file")
    parser.add_argument('-d',
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
                        default='narrow',
                        help="range (optional) Default: narrow. Overriden if full/narrow in TPAT name"
    )
    parser.add_argument('-m',
                        choices=matrix_options,
                        default='Rec709',
                        help="matrix (optional) Default: Rec709"
    )
    parser.add_argument('-e',
                        choices=eotf_options,
                        default='SDR',
                        help="eotf (optional) Default: SDR"
    )
    args = parser.parse_args()

    try:
        (image, bits, name) = render_tpat(args.tpat_in)
        if bits < 32:
            image = image.astype(np.uint16) << (16 - bits)
        with BlackmagicOutput() as output:
            output.initialize()

            display_mode = modes[args.d]

            pixel_format_str = str(args.p).lower()
            if pixel_format_str == 'rgb10':
                pixel_format = PixelFormat.RGB10
            elif pixel_format_str == 'rgb12':
                pixel_format = PixelFormat.RGB12
            else:
                pixel_format = PixelFormat.YUV10

            narrow_range = (str(args.r).lower() == 'narrow' or 'narrow' in name.lower()) and not 'full' in name.lower()

            if str(args.m).lower() == 'rec2020':
                matrix = bmo.Matrix.Rec2020
            else:
                matrix = bmo.Matrix.Rec709

            eotf_str = str(args.e).lower()
            if eotf_str == 'hlg':
                eotf = {'eotf': bmo.Eotf.HLG}
            elif eotf_str == 'pq':
                eotf = {'eotf': bmo.Eotf.PQ}
            else:
                eotf = {'eotf': bmo.Eotf.SDR}

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
        exit(1)
