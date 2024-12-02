#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A python utility for rendering a Test Pattern Descriptor file to an image file.

Usage: python tpat2tiff.py <tpat_file>
"""

__version__ = "2.0"
__license__ = "BSD 3-Clause License"
__maintainer__ = "Gino Bollaert"
__email__ = "gino@orion-convert.com"


import json
import math
import numpy as np
import numpy.typing as npt
import os
import pathlib
import sys
import tifffile as tiff
from jsonschema import validate
from PIL import Image
from typing import List, Dict, Tuple


def as_color(col: float | List[float]) -> List[float]:
    """If the color is defines as a single greyscale number, convert it to an RGB triplet.

    Args:
        col (float | List[float]): The color as a single greyscale number or RGB triplet.

    Returns:
        List[float]: An RGB color triplet.
    """
    if hasattr(col, "__len__"):
        return col
    return [col, col, col]


def as_array(val: any) -> List[any]:
    """Convert the argument to a one element array if it isn't an array already.

    Args:
        val (any): Any value.

    Returns:
        List[any]: The value as an array.
    """
    if hasattr(val, "__len__"):
        return val
    return [val]


def blend_colors(col1, col2, t: float, is_float: bool) -> List[float]:
    """LERP between two colors.

    Args:
        col1 (float | List[float]): The first color.
        col2 (float | List[float]): The second color.
        t (float): The blend parameter from 0 to 1.
        is_float (bool): Whether the color channels are stored as floating point.

    Returns:
        List[float]: The color result of the interpolation.
    """
    if is_float:
        return [c1 + t * (c2 - c1) for c1, c2 in zip(as_color(col1), as_color(col2))]
    return [int(c1 + t * (c2 - c1) + 0.5) for c1, c2 in zip(as_color(col1), as_color(col2))]


def horizontal_ramp(image: npt.NDArray, col1, col2, is_float: bool) -> None:
    """Fill an image with a horizontal linear gradient.

    Args:
        image (npt.NDArray): The image to be filled.
        col1 (float | List[float]): The leftmost color.
        col2 (float | List[float]): The rightmost color.
        is_float (bool): Whether the color channels are stored as floating point.
    """
    for x in range(np.shape(image)[1]):
        image[:, x] = blend_colors(
            col1, col2, x / (np.shape(image)[1] - 1), is_float)


def vertical_ramp(image: npt.NDArray, col1, col2, is_float: bool) -> None:
    """Fill an image with a vertical linear gradient.

    Args:
        image (npt.NDArray): The image to be filled.
        col1 (float | List[float]): The topmost color.
        col2 (float | List[float]): The bottommost color.
        is_float (bool): Whether the color channels are stored as floating point.
    """
    for y in range(np.shape(image)[0]):
        image[y, :] = blend_colors(
            col1, col2, y / (np.shape(image)[0] - 1), is_float)


def square_wave(col1, col2, phase: float, is_float: bool) -> List[float]:
    """Square-wave alternation between two colors.

    Args:
        col1 (float | List[float]): The first color.
        col2 (float | List[float]): The second color.
        phase (float): The phase in half-cycles (repeats at 2.0).
        is_float (bool): Whether the color channels are stored as floating point.

    Returns:
        List[float]: The resulting color.
    """
    return as_color(col1) if phase % 2 < 1 else as_color(col2)


def sine_wave(col1, col2, phase: float, is_float: bool) -> List[float]:
    """Sinusoidal alternation between two colors.

    Args:
        col1 (float | List[float]): The first color.
        col2 (float | List[float]): The second color.
        phase (float): The phase in half-cycles (repeats at 2.0).
        is_float (bool): Whether the color channels are stored as floating point.

    Returns:
        List[float]: The resulting color.
    """
    return blend_colors(col1, col2, (1 - math.sin(phase * math.pi)) / 2, is_float)


def cosine_wave(col1, col2, phase: float, is_float: bool) -> List[float]:
    """Same as sine_wave but offset by a quarter cycle.

    Args:
        col1 (float | List[float]): The first color.
        col2 (float | List[float]): The second color.
        phase (float): The phase in half-cycles (repeats at 2.0).
        is_float (bool): Whether the color channels are stored as floating point.

    Returns:
        List[float]: The resulting color.
    """
    return blend_colors(col1, col2, (1 - math.cos(phase * math.pi)) / 2, is_float)


def horizontal_grating(image: npt.NDArray, func, tpat: List, is_float: bool) -> None:
    """Fill an image with a horizontal frequency grating.

    Args:
        image (npt.NDArray): The image to be filled.
        func (_type_): A waveform function which accepts two colors and a phase.
        tpat (List): A 3 or 4-element array specifying the oscillating half-periods and the two
        colors which the grating oscillates between. If the array has 4 elements the first 2 numbers
        will be the starting and ending half-periods for a linear frequency sweep.
        is_float (bool): _description_
    """
    if len(tpat) == 3:
        if tpat[0] == 1:
            func = square_wave
        f1 = 1.0 / tpat[0]
        f2 = 1.0 / tpat[0]
    else:
        f1 = 1.0 / tpat[0]
        f2 = 1.0 / tpat[1]
    col1 = tpat[-2]
    col2 = tpat[-1]
    width = np.shape(image)[1]
    a = (f2 - f1) / (width - 1)  # the phase acceleration
    for x in range(width):
        image[:, x] = func(col1, col2, f1 * x + 0.5 * a * x * x, is_float)


def vertical_grating(image: npt.NDArray, func, tpat: List, is_float: bool) -> None:
    """Fill an image with a vertical frequency grating.

    Args:
        image (npt.NDArray): The image to be filled.
        func (_type_): A waveform function which accepts two colors and a phase.
        tpat (List): A 3 or 4-element array specifying the oscillating half-periods and the two
        colors which the grating oscillates between. If the array has 4 elements the first 2 numbers
        will be the starting and ending half-periods for a linear frequency sweep.
        is_float (bool): _description_
    """
    if len(tpat) == 3:
        if tpat[0] == 1:
            func = square_wave
        f1 = 1.0 / tpat[0]
        f2 = 1.0 / tpat[0]
    else:
        f1 = 1.0 / tpat[0]
        f2 = 1.0 / tpat[1]
    col1 = tpat[-2]
    col2 = tpat[-1]
    height = np.shape(image)[0]
    a = (f2 - f1) / (height - 1)  # the phase acceleration
    for y in range(height):
        image[y, :] = func(col1, col2, f1 * y + 0.5 * a * y * y, is_float)


def border_settings(tpat: Dict) -> Tuple:
    """Get the patch's border settings.

    Args:
        tpat (Dict): The patch's loaded dictionary.

    Returns:
        Tuple: The horizontal and vertical border sizes and border color.
    """
    hborder = 0
    vborder = 0
    border_color = None
    if 'border' in tpat:
        border = tpat['border']
        if hasattr(border, "__len__"):
            hborder = border[1]
            vborder = border[0]
        else:
            hborder = border
            vborder = border
    if 'bordercolor' in tpat:
        border_color = as_color(tpat['bordercolor'])
    return (hborder, vborder, border_color)


def spacing_settings(tpat: Dict,
                     default_hspacing: int | None,
                     default_vspacing: int | None) -> Tuple:
    """Get the patch's spacing settings.

    Args:
        tpat (Dict): The patch's loaded dictionary.
        default_hspacing (int | None): The default horizontal spacing.
        default_vspacing (int | None): The default vertical spacing.

    Returns:
        Tuple: The horizontal and vertical spacings.
    """
    hspacing = 0 if default_hspacing is None else default_hspacing
    vspacing = 0 if default_vspacing is None else default_vspacing
    if 'spacing' in tpat:
        spacing = tpat['spacing']
        if hasattr(spacing, "__len__"):
            hspacing = spacing[1]
            vspacing = spacing[0]
        else:
            hspacing = spacing
            vspacing = spacing
    return (hspacing, vspacing)


def convert_bits(image: npt.NDArray, from_bits: int, to_bits: int) -> npt.NDArray:
    """Convert an image from one bit depth to another.

    Args:
        image (npt.NDArray): The source image.
        from_bits (int): The input bit depth (8, 10, 12, 16 or 32).
        to_bits (int): The output bit depth (8, 10, 12, 16 or 32).

    Returns:
        npt.NDArray: The converted image.
    """
    if from_bits == to_bits:
        return image
    if to_bits == 32:
        return image.astype(np.float32) / (2**from_bits - 1)
    if from_bits == 32:
        return (image * (2**to_bits - 1) + 0.5).astype(np.int32)
    return convert_bits(convert_bits(image, from_bits, 32), 32, to_bits)


def overlay_image(image: npt.NDArray, tpat: Dict, bits: int, directory: str) -> None:
    """Composite an image file onto a source image.

    Args:
        image (npt.NDArray): The image onto which the other image will be composited.
        tpat (Dict): The patch's loaded dictionary.
        bits (int): The resulting image's bit depth.
        directory (str): The base directory for resolving relative paths.
    """
    if not 'image' in tpat:
        return  # no image to overlay.

    path = tpat['image']
    # alpha premultiplication
    premul = tpat['premul'] if 'premul' in tpat else False

    # Load the image to be overlaid and determine its size and bit depth.
    path = path if os.path.isabs(path) else os.path.join(directory, path)
    with Image.open(path) as im:
        comp = np.array(im, dtype=np.uint8)
    [comp_hgt, comp_wid, comp_ch] = comp.shape
    if comp.dtype == np.float32 or comp.dtype == np.float64:
        from_bits = 32
    else:
        from_bits = 8 if comp.dtype == np.uint8 else 16
    [hgt, wid] = image.shape[:2]
    if comp_wid > wid or comp_hgt > hgt:
        raise ValueError("The image size is larger than the patch size")

    # Calculate the offsets for centering the overlay.
    x = (wid - comp_wid) // 2
    y = (hgt - comp_hgt) // 2

    # Obtain the destination image area for the overlay.
    rect = image[y:y + comp_hgt, x:x + comp_wid]

    # If the overlay has no alpha channel, replace the image area with the overlay.
    if comp_ch == 3:
        rect[:] = convert_bits(comp, from_bits, bits)
        return

    # Convert the image area and overlay to floating point.
    comp = convert_bits(comp, from_bits, 32)
    dest = convert_bits(rect, bits, 32)

    # Split the alpha from the RGB channels
    r, g, b, a = np.dsplit(comp, 4)
    rgb = np.dstack((r, g, b))

    # Blend the images and replace the image area with the result convert to the original bit depth.
    rgb = dest * (1 - a) + (rgb if premul else a * rgb)
    rect[:] = convert_bits(rgb, 32, bits)


def draw_patch(image: npt.NDArray,
               bits: int,
               tpat: Dict,
               directory: str,
               parent_columns: List[int] = None,
               parent_rows: List[int] = None,
               parent_hspacing: int = None,
               parent_vspacing: int = None) -> None:
    """A recursive function for drawing patches.

    Args:
        image (npt.NDArray): The destination image.
        bits (int): The bit depth of the destination image.
        tpat (Dict): The patch's loaded dictionary.
        directory (str): The base directory for resolving relative paths.
        parent_columns (List[int]): The parent columns spanned by the patch.
        parent_rows (List[int]):  The parent rows spanned by the patch.
        parent_hspacing (int): The parent's horizontal grid spacing.
        parent_vspacing (int): The parent's vertical grid spacing.
    """
    is_float = bits == 32
    [height, width] = image.shape[:2]
    (hborder, vborder, border_color) = border_settings(tpat)

    # Draw borders if a color was specified.
    if not border_color is None:
        image[:, :hborder] = border_color
        image[:, width - hborder:] = border_color
        image[:vborder, :] = border_color
        image[height - vborder:, :] = border_color

    # Crop out borders for solid color, ramp or grating.
    rect = image[vborder:height - vborder, hborder:width - hborder]

    # Draw solid color, ramp or grating.
    if 'color' in tpat:
        rect[:] = as_color(tpat['color'])  # patch background color
    elif 'hramp' in tpat:
        horizontal_ramp(rect[:], tpat['hramp'][0], tpat['hramp'][1], is_float)
    elif 'vramp' in tpat:
        vertical_ramp(rect[:], tpat['vramp'][0], tpat['vramp'][1], is_float)
    elif 'hsine' in tpat:
        horizontal_grating(rect[:], sine_wave, tpat['hsine'], is_float)
    elif 'vsine' in tpat:
        vertical_grating(rect[:], sine_wave, tpat['vsine'], is_float)
    elif 'hcosine' in tpat:
        horizontal_grating(rect[:], cosine_wave, tpat['hcosine'], is_float)
    elif 'vcosine' in tpat:
        vertical_grating(rect[:], cosine_wave, tpat['vcosine'], is_float)
    elif 'hsquare' in tpat:
        horizontal_grating(rect[:], square_wave, tpat['hsquare'], is_float)
    elif 'vsquare' in tpat:
        vertical_grating(rect[:], square_wave, tpat['vsquare'], is_float)

    if not any(x in tpat for x in ['columns', 'rows', 'width', 'height']):
        overlay_image(rect, tpat, bits, directory)
        return  # no subpatch grid has been defined

    # Calculate default grid size.
    widths = [width - 2 * hborder]
    heights = [height - 2 * vborder]
    default_hspacing = None
    default_vspacing = None

    # Columns widths may be defined using the "columns" or "width" tags.
    if 'columns' in tpat:
        if tpat['columns'] == 'parent':
            widths = parent_columns
            default_hspacing = parent_hspacing
        else:
            widths = as_array(tpat['columns'])
    elif 'width' in tpat:
        if tpat['width'] == 'parent':
            widths = parent_columns
            default_hspacing = parent_hspacing
        else:
            widths = as_array(tpat['width'])

    # Row heights may be defined using the "rows" or "height" tags.
    if 'rows' in tpat:
        if tpat['rows'] == 'parent':
            heights = parent_rows
            default_vspacing = parent_vspacing
        else:
            heights = as_array(tpat['rows'])
    elif 'height' in tpat:
        if tpat['height'] == 'parent':
            heights = parent_rows
            default_vspacing = parent_vspacing
        else:
            heights = as_array(tpat['height'])

    # Obtain the spacing settings.
    (hspacing, vspacing) = spacing_settings(
        tpat, default_hspacing, default_vspacing)

    # Interleave the grid widths and heights with the spacings.
    x = [b for a in widths for b in [a, hspacing]]
    y = [b for a in heights for b in [a, vspacing]]
    x = np.cumsum([0] + x[:-1])  # calculate the grid of x offsets
    y = np.cumsum([0] + y[:-1])  # calculate the grid of y offsets

    # Draw spacings if a border color was specified.
    if not border_color is None:
        for i in range(2, len(x), 2):
            rect[:, x[i - 1]:x[i]] = border_color
        for i in range(2, len(y), 2):
            rect[y[i - 1]:y[i], :] = border_color

    if not 'patches' in tpat and not 'subpatches' in tpat:
        overlay_image(rect, tpat, bits, directory)
        return  # there are no sub-patches so we return here

    # Default rect, in grid cells not pixels, of the first sub-patch.
    left = 0
    top = 0
    wid = 1
    hgt = 1

    # Iterate through each sub-patch.
    for p in as_array(tpat['patches'] if 'patches' in tpat else tpat['subpatches']):
        if isinstance(p, dict):
            if 'left' in p:
                left = p['left']
            if 'top' in p:
                top = p['top']
            if 'right' in p:
                wid = p['right'] - left
            if 'bottom' in p:
                hgt = p['bottom'] - top
            if 'cell' in p:
                cell = p['cell']
                top = cell[0] - 1
                left = cell[1] - 1
                if len(cell) == 4:
                    hgt = cell[2] - top
                    wid = cell[3] - left
                else:
                    wid = 1
                    hgt = 1

        # The patch's rect in pixels.
        subpatch = rect[y[top * 2]:y[(top + hgt) * 2 - 1],
                        x[left * 2]:x[(left + wid) * 2 - 1]]

        if isinstance(p, dict):
            # The sub-patch is defined as a dict, therefore recurse
            draw_patch(subpatch, bits, p, directory, widths[left:left + wid],
                       heights[top:top + hgt], hspacing, vspacing)
        else:
            # the sub-patch is defined as a color value
            subpatch[:] = as_color(p)

        # Offset the next patch by 'wid' cells to the right by default.
        left += wid

        # If the next patch's position surpasses the right edge of the grid, move it to the start of
        # the next row, assuming rows are 'hgt' cells high.
        if left + wid > len(widths):
            left = 0
            top += hgt

    # Composite an image on the patch, if specified.
    overlay_image(rect, tpat, bits, directory)


def save_tiff(image: npt.NDArray, bits: int, file_path: str, max_16bit_scaling: bool) -> None:
    """Save the image as an 8, 16 or 32-bit tiff.

    Args:
        image (npt.NDArray): The image to be saved.
        bits (int): The original bit depth.
        file_path (str): The output file path.
        max_16bit_scaling (bool): Whether to scale to the maximum 16-bit value.
    """
    if bits == 8:
        bit_depth = "uint8"
        scaleUp = 1
        scaleDown = 0
    elif bits <= 16:
        bit_depth = "uint16"
        scaleUp = 2**(16 - bits)  # shift right to fill MSBs
        # fill LSBs with MSBs for full 16-bit scaling
        scaleDown = 2**(2 * bits - 16) if max_16bit_scaling else 0
    elif bits == 32:
        bit_depth = "float32"
        scaleUp = 1
        scaleDown = 0
    image = (image * scaleUp) + (image / scaleDown if scaleDown > 0 else 0)

    tiff.imwrite(file_path, image.astype(bit_depth))


def save_8bit(image: npt.NDArray, bits: int, file_path: str) -> None:
    """Save an 8-bit preview of the image.

    Args:
        image (npt.NDArray): The image to be saved.
        bits (int): The original bit depth.
        file_path (str): The output file path.
    """
    if bits == 32:
        image = (image * 255 + 0.5).astype(np.uint8)
    elif bits > 8:
        image = (image * 255 / (2**bits - 1)).astype(np.uint8)
    Image.fromarray(image).save(file_path)


def render_tpat(tpat_in: str) -> Tuple:
    """Render a T-PAT file to an image.

    Args:
        tpat_in (str): The path to the T-PAT file.

    Returns:
        Tuple: The image, bit depth and name of the test pattern.
    """
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
        validate(instance=tpat, schema=schema)

    # Check the T-PAT version number.
    if 'version' in tpat:
        if tpat['version'] > 2:
            raise ValueError(f"This tool supports version 1 and 2 T-PAT files only")

    # Sum the cell widths and heights to get the total image size.
    (hborder, vborder, _) = border_settings(tpat)
    (hspacing, vspacing) = spacing_settings(tpat, None, None)
    widths = as_array(tpat['columns'] if 'columns' in tpat else tpat['width'])
    heights = as_array(tpat['rows'] if 'rows' in tpat else tpat['height'])
    width = sum(widths) + 2 * hborder + (len(widths) - 1) * hspacing
    height = sum(heights) + 2 * vborder + (len(heights) - 1) * vspacing

    # Cross check the width and height if possible
    if 'width' in tpat and 'columns' in tpat:
        if tpat['width'] != width:
            raise ValueError(f"The calulated width ({
                  width}) does not match the specified width ({tpat['width']})")
    if 'height' in tpat and 'rows' in tpat:
        if tpat['height'] != height:
            raise ValueError(f"The calulated height ({
                  height}) does not match the specified height ({tpat['height']})")

    # Produce integer image data if the bit depth is 16 or less, other produce float image data.
    bits = tpat['depth']
    image = np.zeros((height, width, 3),
                     np.int32 if bits <= 16 else np.float32)
    draw_patch(image, bits, tpat, pathlib.Path(tpat_in).parent.resolve())

    return (image, bits, tpat['name'] if 'name' in tpat else None)


def main():
    if len(sys.argv) < 2:
        print(f"Usage:  python {sys.argv[0]} <TPAT_file_in> [<TIFF_file_out>]")
        exit(1)

    tpat_in = sys.argv[1]

    try:
        (image, bits, name) = render_tpat(tpat_in)

        # If the TIFF's file name is not defined, use the T-PAT's 'name' field, otherwise use the
        # name of the T-PAT file itself.
        base_file_name = name.replace(' ', '_') if not name is None else tpat_in[:-5]
        tiff_out = sys.argv[2] if len(sys.argv) > 2 else base_file_name + '.tif'

        save_tiff(image, bits, tiff_out, True)
        save_8bit(image, bits, base_file_name + '.png')
    except Exception as error:
        print(error)
        exit(1)


if __name__ == "__main__":
    main()
