#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
##  tpat2tiff.py
##
##  A utility for making a TIFF from a Test Pattern Descriptor file
##
##  Created by Gino Bollaert on 2023-09-29.
##

import json
from jsonschema import validate
import math
import numpy as np
import os
import pathlib
import sys
import tifffile as tiff

# If 'col' has a length, assume it is already color triplet otherwise treat it as a single
# greyscale color value.
def asColor(col):
    if hasattr(col, "__len__"):
        return col
    return [col, col, col]

# If 'val' has a length, assume it is already an array otherwise treat it as a single value.
def asArray(val):
    if hasattr(val, "__len__"):
        return val
    return [val]

# Blend between two float or integer colors
def blendColors(col1, col2, t, is_float):
    if is_float:
        return [c1 + t * (c2 - c1) for c1, c2 in zip(asColor(col1), asColor(col2))]
    return [int(c1 + t * (c2 - c1) + 0.5) for c1, c2 in zip(asColor(col1), asColor(col2))]

# Square-wave alternation between two colours
def square(col1, col2, phase, is_float):
    return col1 if phase % 2 < 1 else col2

# Sinusoidal alternation between two colours
def sine(col1, col2, phase, is_float):
    return blendColors(col1, col2, (1 - math.sin(phase * math.pi)) / 2, is_float)

# Same as sine but offset by a quarter cycle
def cosine(col1, col2, phase, is_float):
    return blendColors(col1, col2, (1 - math.cos(phase * math.pi)) / 2, is_float)

# Fill with horizontal gradient.
def horizontalRamp(image, col1, col2, is_float):
    for x in range(np.shape(image)[1]):
        image[:, x] = blendColors(col1, col2, x / (np.shape(image)[1] - 1), is_float)

# Fill with vertical gradient.
def verticalRamp(image, col1, col2, is_float):
    for y in range(np.shape(image)[0]):
        image[y, :] = blendColors(col1, col2, y / (np.shape(image)[0] - 1), is_float)

# Fill with horizontal frequency grating.
def horizontalGrating(image, func, half_period, col1, col2, is_float):
    if half_period == 1:
        func = square
    if hasattr(half_period, "__len__"):
        f1 = 1.0 / half_period[0]
        f2 = 1.0 / half_period[1]
    else:
        f1 = 1.0 / half_period
        f2 = 1.0 / half_period
    width = np.shape(image)[1]
    a = (f2 - f1) / (width - 1)
    for x in range(width):
        image[:, x] = func(col1, col2, f1 * x + 0.5 * a * x * x, is_float)

# Fill with horizontal frequency grating.
def verticalGrating(image, func, half_period, col1, col2, is_float):
    if half_period == 1:
        func = square
    if hasattr(half_period, "__len__"):
        f1 = 1.0 / half_period[0]
        f2 = 1.0 / half_period[1]
    else:
        f1 = 1.0 / half_period
        f2 = 1.0 / half_period
    height = np.shape(image)[0]
    a = (f2 - f1) / (height - 1)
    for y in range(height):
        image[y, :] = func(col1, col2, f1 * y + 0.5 * a * y * y, is_float)

# Get the patch's border settings
def borders(tpat):
    hborder = 0
    vborder = 0
    border_color = None
    if 'border' in tpat:
        border = tpat['border']
        if hasattr(border, "__len__"):
            hborder = border[0]
            vborder = border[1]
        else:
            hborder = border
            vborder = border
    if 'bordercolor' in tpat:
        border_color = asColor(tpat['bordercolor'])
    return (hborder, vborder, border_color)

# Get the patch's spacing settings
def spacings(tpat):
    hspacing = 0
    vspacing = 0
    spacing_color = None
    if 'spacing' in tpat:
        spacing = tpat['spacing']
        if hasattr(spacing, "__len__"):
            hspacing = spacing[0]
            vspacing = spacing[1]
        else:
            hspacing = spacing
            vspacing = spacing
    if 'spacingcolor' in tpat:
        spacing_color = asColor(tpat['spacingcolor'])
    return (hspacing, vspacing, spacing_color)

def convert_bits(image, from_bits, to_bits):
    if from_bits == to_bits:
        return image
    if to_bits == 32:
        return image.astype(np.float32) / (2**from_bits - 1)
    if from_bits == 32:
        return (image * (2**to_bits - 1) + 0.5).astype(np.int32)
    return convert_bits(convert_bits(image, from_bits, 32), 32, to_bits)

def composite_image(image, tpat, bits, directory):
    if not 'image' in tpat:
        return
    path = tpat['image']
    path = path if os.path.isabs(path) else os.path.join(directory, path)
    comp = tiff.imread(path)
    [comp_hgt, comp_wid, comp_ch] = comp.shape
    if comp.dtype == np.float32 or comp.dtype == np.float64:
        from_bits = 32
    else:
        from_bits = 8 if comp.dtype == np.uint8 else 16
    [hgt, wid] = image.shape[:2]
    if comp_wid > wid or comp_hgt > hgt:
        print("Image size is larger than its subpatch")
        return
    x = (wid - comp_wid) // 2
    y = (hgt - comp_hgt) // 2
    rect = image[y:y + comp_hgt, x:x + comp_wid]
    if comp_ch == 3:
        rect[:] = convert_bits(comp, from_bits, bits)
        return
    comp = convert_bits(comp, from_bits, 32)
    dest = convert_bits(rect, bits, 32)

    r, g, b, a = np.dsplit(comp, 4)
    rgb = np.dstack((r, g, b))
    rect[:] = convert_bits(dest * (1 - a) + rgb, 32, bits)

# A recursive function for drawing patches.
def drawPatch(image, tpat, bits, directory):
    is_float = bits == 32
    [height, width] = image.shape[:2]
    (hborder, vborder, border_color) = borders(tpat)
    (hspacing, vspacing, spacing_color) = spacings(tpat)

    # Draw borders if a color was specified
    if not border_color is None:
        image[:, :hborder] = border_color
        image[:, width - hborder:] = border_color
        image[:vborder, :] = border_color
        image[height - vborder:, :] = border_color

    # Crop out borders for solid color, ramp or gratings
    rect = image[vborder:height - vborder, hborder:width - hborder]

    if 'color' in tpat:
        rect[:] = asColor(tpat['color']) # patch background color
    elif 'hramp' in tpat:
        horizontalRamp(rect[:], tpat['hramp'][0], tpat['hramp'][1], is_float)
    elif 'vramp' in tpat:
        verticalRamp(rect[:], tpat['vramp'][0], tpat['vramp'][1], is_float)
    elif 'hsine' in tpat:
        horizontalGrating(rect[:], sine, tpat['hsine'][0], tpat['hsine'][1], tpat['hsine'][2], is_float)
    elif 'vsine' in tpat:
        verticalGrating(rect[:], sine, tpat['vsine'][0], tpat['vsine'][1], tpat['vsine'][2], is_float)
    elif 'hcosine' in tpat:
        horizontalGrating(rect[:], cosine, tpat['hcosine'][0], tpat['hcosine'][1], tpat['hcosine'][2], is_float)
    elif 'vcosine' in tpat:
        verticalGrating(rect[:], cosine, tpat['vcosine'][0], tpat['vcosine'][1], tpat['vcosine'][2], is_float)
    elif 'hsquare' in tpat:
        horizontalGrating(rect[:], square, tpat['hsquare'][0], tpat['hsquare'][1], tpat['hsquare'][2], is_float)
    elif 'vsquare' in tpat:
        verticalGrating(rect[:], square, tpat['vsquare'][0], tpat['vsquare'][1], tpat['vsquare'][2], is_float)

    if not 'width' in tpat and not 'height' in tpat:
        composite_image(rect, tpat, bits, directory)
        return # no subpatch grid has been defined

    widths = asArray(tpat['width']) if 'width' in tpat else [width - 2 * hborder]
    heights = asArray(tpat['height']) if 'height' in tpat else [height - 2 * vborder]

    # Interleave the grid widths with the border and spacings
    x = [b for a in widths for b in [a, hspacing]]
    y = [b for a in heights for b in [a, vspacing]]
    x = np.cumsum([0] + x[:-1]) # calculate the grid of x offsets
    y = np.cumsum([0] + y[:-1]) # calculate the grid of y offsets

    # Draw spacings if a color was specified
    if not spacing_color is None:
        for i in range(2, len(x), 2):
            rect[:, x[i - 1]:x[i]] = spacing_color
        for i in range(2, len(y), 2):
            rect[y[i - 1]:y[i], :] = spacing_color

    if not 'subpatches' in tpat:
        composite_image(rect, tpat, bits, directory)
        return # there are no sub-patches so we return here

    # Default rect, in grid cells not pixels, of the first sub-patch.
    left = 0
    top = 0
    wid = 1
    hgt = 1

    # Iterate through each sub-patch.
    for p in asArray(tpat['subpatches']):
        if isinstance(p, dict):
            if 'left' in p:
                left = p['left']
            if 'top' in p:
                top = p['top']
            if 'right' in p:
                wid = p['right'] - left
            if 'bottom' in p:
                hgt = p['bottom'] - top

        # The patch's rect in pixels.
        subpatch = rect[y[top * 2]:y[(top + hgt) * 2 - 1], x[left * 2]:x[(left + wid) * 2 - 1]]

        if isinstance(p, dict):
            drawPatch(subpatch, p, bits, directory) # the sub-patch is defined as a dict, therefore recurse
        else:
            subpatch[:] = asColor(p) # the sub-patch is defined as a color value

        # Offset the next patch by 'wid' cells to the right by default.
        left += wid

        # If the next patch's position surpasses the right edge of the grid, move it to the start of
        # the next row, assuming rows are 'hgt' cells high.
        if left + wid > len(x) / 2:
            left = 0
            top += hgt

    # Composite images on top of subpatches.
    composite_image(rect, tpat, bits, directory)

# Draw and save a TIFF file from a T-PAT file.
def tpat2tiff(tpat_in, tiff_out):
    f = open(tpat_in)
    tpat = json.load(f)
    f.close()

    # Check the T-PAT file against the schema.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    schema_file = os.path.join(script_dir, "tpat.schema.json")
    if os.path.isfile(schema_file):
        f = open(schema_file)
        schema = json.load(f)
        f.close()
        try:
            validate(instance=tpat, schema=schema)
        except Exception as error:
            print(str(error).splitlines()[0])
            exit(1)

    # Check the T-PAT version number.
    if 'version' in tpat:
        if tpat['version'] > 2:
            print(f"This tool supports version 1 and 2 T-PAT files only")
            exit(1)

    # If the TIFF's file name is not defined, use the T-PAT's 'name' field, otherwise use the name
    # of the T-PAT file itself.
    if tiff_out is None:
        tiff_out = (tpat['name'].replace(' ', '_') if 'name' in tpat else tpat_in) + '.tif'

    # Sum the cell widths and heights to get the total image size.
    (hborder, vborder, _) = borders(tpat)
    (hspacing, vspacing, _) = spacings(tpat)
    widths = asArray(tpat['width'])
    heights = asArray(tpat['height'])
    width = sum(widths) + 2 * hborder + (len(widths) - 1) * hspacing
    height = sum(heights) + 2 * vborder + (len(heights) - 1) * vspacing

    # Produce integer image data if the bit depth is 16 or less, other produce float image data.
    bits = tpat['depth']
    image = np.zeros((height, width, 3), np.int32 if bits <= 16 else np.float32)
    drawPatch(image, tpat, bits, pathlib.Path(tpat_in).parent.resolve())

    if bits == 8:
        bit_depth = "uint8"
        scaleUp = 1
        scaleDown = 0
    elif bits <= 16:
        bit_depth = "uint16"
        scaleUp = 2**(16 - bits) # shift right to fill MSBs
        scaleDown = 2**(2 * bits - 16) # fill LSBs with MSBs for full 16-bit scaling
    elif bits == 32:
        bit_depth = "float32"
        scaleUp = 1
        scaleDown = 0
    image = (image * scaleUp) + (image / scaleDown if scaleDown > 0 else 0)

    tiff.imwrite(tiff_out, image.astype(bit_depth))

def main():
    if len(sys.argv) < 2:
        print(f"Usage:  python {sys.argv[0]} <TPAT_file_in> [<TIFF_file_out>]")
        exit(1)
    tpat2tiff(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

if __name__ == "__main__":
    main()