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
import numpy as np
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

# Fill with horizontal gradient.
def horizontalRamp(image, col1, col2, is_float):
    for x in range(np.shape(image)[1]):
        image[:, x] = blendColors(col1, col2, x / (np.shape(image)[1] - 1), is_float)

# Fill with vertical gradient.
def verticalRamp(image, col1, col2, is_float):
    for y in range(np.shape(image)[0]):
        image[y, :] = blendColors(col1, col2, y / (np.shape(image)[0] - 1), is_float)

# A recursive function for drawing patches.
def drawPatch(image, tpat, is_float):
    hborder = 0
    vborder = 0
    hspacing = 0
    vspacing = 0
    if 'border' in tpat:
        border = tpat['border']
        if hasattr(border, "__len__"):
            hborder = border[0]
            vborder = border[1]
        else:
            hborder = border
            vborder = border
    rect = image[vborder:, hborder:]
    if 'spacing' in tpat:
        spacing = tpat['spacing']
        if hasattr(spacing, "__len__"):
            hspacing = spacing[0]
            vspacing = spacing[1]
        else:
            hspacing = spacing
            vspacing = spacing
    if 'color' in tpat:
        rect[:] = asColor(tpat['color']) # patch background color
    elif 'hramp' in tpat:
        horizontalRamp(rect[:], tpat['hramp'][0], tpat['hramp'][1], is_float)
    elif 'vramp' in tpat:
        verticalRamp(rect[:], tpat['vramp'][0], tpat['vramp'][1], is_float)

    if not 'subpatches' in tpat:
        return # there are no sub-patches so we return here

    # Interleave the grid widths with the border and spacings
    x = [0, hborder] + [b for a in asArray(tpat['width']) for b in [a, hspacing]]
    y = [0, vborder] + [b for a in asArray(tpat['height']) for b in [a, vspacing]]
    x = np.cumsum(x) # calculate the grid of x offsets
    y = np.cumsum(y) # calculate the grid of y offsets

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
        rect = image[y[top * 2 + 1]:y[(top + hgt) * 2], x[left * 2 + 1]:x[(left + wid) * 2]]

        if isinstance(p, dict):
            drawPatch(rect, p, is_float) # the sub-patch is defined as a dict, therefore recurse
        else:
            rect[:] = asColor(p) # the sub-patch is defined as a color value

        # Offset the next patch by 'wid' cells to the right by default.
        left += wid

        # If the next patch's position surpasses the right edge of the grid, move it to the start of
        # the next row, assuming rows are 'hgt' cells high.
        if left + wid >= len(x) / 2:
            left = 0
            top += hgt

# Draw and save a TIFF file from a T-PAT file.
def tpat2tiff(tpat_in, tiff_out):
    f = open(tpat_in)
    tpat = json.load(f)
    f.close()

    # Check the T-PAT version number
    if 'version' in tpat:
        if tpat['version'] != 1:
            print(f"This tool supports V1 T-PAT files only")
            exit(1)

    # If the TIFF's file name is not defined, use the T-PAT's 'name' field, otherwise use the name
    # of the T-PAT file itself.
    if tiff_out is None:
        tiff_out = (tpat['name'].replace(' ', '_') if 'name' in tpat else tpat_in) + '.tif'

    # Sum the cell widths and heights to get the total image size.
    width = sum(asArray(tpat['width']))
    height = sum(asArray(tpat['height']))

    # Produce integer image data if the bit depth is 16 or less, other produce float image data.
    bits = tpat['depth']
    image = np.zeros((height, width, 3), np.int32 if bits <= 16 else np.float32)
    drawPatch(image, tpat, bits == 32)

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