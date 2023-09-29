#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
##  tpat2tiff.py
##
##  A utility for making a TIFF from a Test Pattern Descriptor file
##
##  Created by Gino Bollaert on 2023-09-29.
##

import sys
import numpy as np
import colour
import json

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

# Blend between two float or integer colours
def blendColors(col1, col2, t):
    if isinstance(asColor(col1)[0], int):
        return [int(c1 + t * (c2 - c1) + 0.5) for c1, c2 in zip(asColor(col1), asColor(col2))]
    return [c1 + t * (c2 - c1) for c1, c2 in zip(asColor(col1), asColor(col2))]

# Fill with horizontal gradient.
def horizontalRamp(image, col1, col2):
    for x in range(np.shape(image)[1]):
        image[:, x] = blendColors(col1, col2, x / (np.shape(image)[1] - 1))
    
# Fill with vertical gradient.
def verticalRamp(image, col1, col2):
    for y in range(np.shape(image)[0]):
        image[y, :] = blendColors(col1, col2, y / (np.shape(image)[0] - 1))

# A recursive function for drawing patches.
def drawPatch(image, tpat):
    if 'color' in tpat:
        image[:] = asColor(tpat['color']) # patch background color
    elif 'hramp' in tpat:
        horizontalRamp(image[:], tpat['hramp'][0], tpat['hramp'][1])
    elif 'vramp' in tpat:
        verticalRamp(image[:], tpat['vramp'][0], tpat['vramp'][1])

    if not 'patch' in tpat:
        return # there are no sub-patches so we return here
    
    x = np.cumsum([0] + asArray(tpat['width'])) # calculate the grid of x offsets
    y = np.cumsum([0] + asArray(tpat['height'])) # calculate the grid of y offsets
    
    # Default rect, in grid cells not pixels, of the first sub-patch.
    left = 0
    top = 0
    wid = 1
    hgt = 1
    
    # Iterate through each sub-patch.
    for p in asArray(tpat['patch']):
        if isinstance(p, dict):
            if 'left' in p:
                left = p['left']
            if 'top' in p:
                top = p['top']
            if 'right' in p:
                wid = p['right'] - left
            if 'bottom' in p:
                hgt = p['bottom'] - top
        
        #print(f"Patch pos: ({left},{top})  size: {wid}x{hgt}")
        
        # The patch's rect in pixels.
        rect = image[y[top]:y[top + hgt], x[left]:x[left + wid]]
        
        if isinstance(p, dict):
            drawPatch(rect, p) # the sub-patch defined as a dict therefore recurse
        else:
            rect[:] = asColor(p) # the sub-patch is defined as color value
            
        # Offset the next patch by 'wid' cells to the right by default.
        left += wid
        
        # If the next patch's position surpasses the right edge of the grid, move it to the next
        # row, assuming rows are 'hgt' cells high.
        if left + wid >= len(x):
            left = 0
            top += hgt

# Draw and save a TIFF file from a TPAT file.
def tpat2tiff(tpat_in, tiff_out):
    f = open(tpat_in)
    tpat = json.load(f)
    f.close()
    
    # If the TIFF's file name is not defined, use the TPAT's 'name' field, otherwise use the name
    # of the TPAT file itself.
    if tiff_out is None:
        tiff_out = (tpat['name'].replace(' ', '_') if 'name' in tpat else tpat_in) + '.tif'
        
    # Sum the cell widths and heights to get the total image size.
    width = sum(tpat['width']) if hasattr(tpat['width'], "__len__") else tpat['width']
    height = sum(tpat['height']) if hasattr(tpat['height'], "__len__") else tpat['height']
    
    # Produce integer image data if the bit depth is 16 or less, other produce float image data.
    bits = tpat['depth']
    image = np.zeros((height, width, 3), np.int32 if bits <= 16 else np.float32)
    drawPatch(image, tpat)
    
    if bits == 8:
        bit_depth = "uint8"
        scaleUp = 1
        scaleDown = 0
    elif bits <= 16:
        bit_depth = "uint16"
        scaleUp = 2**(16 - bits) # shift up to MSBs
        scaleDown = 2**(2 * bits - 16) # fill LSBs with MSBs for full 16-bit scaling
    elif bits == 32:
        bit_depth = "float32"
        scaleUp = 1
        scaleDown = 0
    image = (image * scaleUp) + (image / scaleDown)
    
    colour.io.write_image(image.astype(bit_depth), tiff_out, bit_depth)
    
def main():
    if len(sys.argv) < 2:
        print(f"Usage:  python {sys.argv[0]} <TPAT_file_in> [<TIFF_file_out>]")
        exit(1)
    tpat2tiff(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

if __name__ == "__main__":
    main()