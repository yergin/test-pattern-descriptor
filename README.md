"T-PAT": Test Pattern Descriptor Specification V2
=================================================

*Updated: 2024-11-28*

The purpose of T-PAT (**T**est **PAT**tern) files is to concisely describe the positioning and colors of rectangular color patches in a test pattern image. They can serve as specifications from which test pattern images can be generated. T-PAT files are JSON files with a `.tpat` extension.

Each T-PAT file represents a test pattern image of a specified size and bit-depth. It contains hierarchical data describing the layout and color of each color patch within its 'container' patch. At the top of the hierarchy is the top-level patch representing the entire image. Patches can be split into a grid of "cells" which serve to locate "sub-patches".

Top-level patch fields
----------------------

| Field | Type | Version | Required | Description |
| - | - | - | - | - |
| **version** | integer | 1 | no | The T-PAT version number (defaults to 1 if omitted) |
| **name** | string | 1 | no | A name describing the test pattern. |
| **description** | string | 2 | no | A full description of the test pattern.** |
| **depth** | integer | 1 | yes | The bit depth of the color data - either 8, 10, 12, 16 or 32(float). |
| **width** | integer or array of integers | 1 | yes | The widths in pixels of each column of the image's grid.* |
| **height** | integer or array of integers | 1 | yes | The heights in pixels of each row of the image's grid.* |
| **border** | integer or array of 2 integers | 2 | no | The horizontal and vertical border size in pixels. The same value is used for both if specified as a single integer.* |
| **bordercolor** | color (see [Specifying colors](#specifying-colors) below) | 2 | no | The border color. The border will be black if not specified. |
| **spacing** | integer or array of 2 integers | 2 | no | The spacing between grid columns and rows in pixels. The same value is used for both if specified as a single integer.* |
| **spacingcolor** | color (see [Specifying colors](#specifying-colors) below) | 2 | no | The grid spacing color. Nothing will be draw in the spacings if not specified. |
| **color** | color (see [Specifying colors](#specifying-colors) below) | 1 | no | The image's solid background color. |
| **hramp** | gradient (see [Specifying gradients](#specifying-gradients) below) | 1 | no | The image's background horizontal gradient. |
| **vramp** | gradient (see [Specifying gradients](#specifying-gradients) below) | 1 | no | The image's background vertical gradient. |
| **hsquare** | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) below) | 2 | no | The image's background horizontal square frequency grating. |
| **vsquare** | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) below) | 2 | no | The image's background vertical square frequency grating. |
| **hsine**<br>**hcosine** | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) below) | 2 | no | The image's background horizontal sinusoidal frequency grating. |
| **vsine**<br>**vcosine** | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) below) | 2 | no | The image's background vertical sinusoidal frequency grating. |
| **image** | string | 2 | no | A TIFF file to be composited onto the image after subpatches have been drawn. If the file has an alpha channel, alpha premultiplication will be assumed. The path may be specified relative to T-PAT file. |
| **subpatches** | array of sub-patches (see [Sub-patches](#Sub-patches) below) | 1 | no | The image's top-level sub-patches |
| **descriptions** | array of string | 2 | no | A description of the sub-patches. This must be the same length as the sub-patch array and "..." means "refer to another description for the patch with the same color value."** |

(*) If width or height are defined as arrays, their sum will determine the total width and height of the image, respectively. The image size will also include any borders and spacings specified.

(**) These fields may be used to automatically generates a PDF specification for the test pattern.

Only one of **color**, **hramp** or **vramp** may be defined. If no background is specified, the image's background color will be black.

Specifying colors
-----------------

Colors can be specified as either a single value, representing the color's greyscale value, or a number array (triplet) representing the color's individual RGB components. If **depth** is either of 8, 10, 12 or 16, greyscale or component values are interpreted as integers whereas if **depth** is 32, greyscale or component values are interpreted as floats.

10-bit integer examples: `940`, `[940, 940, 64]`

32-bit float examples: `0.5`, `[0.5, 0.5, 0]`

Specifying gradients
--------------------

Linear gradients, whether horizontal or vertical, are defined as an array of two color values, the first corresponding to the color at the left-most or top-most pixel within the patch and the second corresponding to the right-most or bottom-most pixel within the patch.

10-bit integer examples: `[0, 940]`, `[[0, 940, 940], [940, 0, 0]]`, `[0, [940, 0, 0]]`

32-bit float examples: `[0, 1]`, `[[0, 1, 0.5], [1, 0, 0.5]]`, `[0, [1, 0, 0]]`

Specifying frequency gratings
-----------------------------

Frequency gratings, whether horizontal or vertical, sinusoidal or square, are defined as a three-element array. The first element may either be an integer, float or a pair of integers or floats in an array. If the first element is a single value, it specifies the half-period of the gratings repetition in pixels, a half-period of 1 pixel representing the nyquist frequency. If the first element is a pair of values, these specify the starting and ending half-periods in a linear frequency sweep. The two subsequent elements specify the two colors the grating alternates between, the first one being the left-most or top-most color. `hcosine` and `vcosine` are equivalent to `hsine` and `vsine` with the only difference being the phase at which they start.

Sub-patches
-----------

Each sub-patch may be defined as a simple color value (see [Specifying colors](#specifying-colors) above) or as a JSON object containing the fields described below. Sub-patches are always defined inside arrays and the first sub-patch defaults to filling the top-left cell in the containing patch's grid, while subsequent patches fill the grid in a left-to-right then top-to-bottom order. This allows Sub-patches to be simply listed as colors without the need to define each sub-patch's position explicitly.

| Field | Type | Version | Required | Description |
| - | - | - | - | - |
| **width** | integer or array of integers | 1 | no | The widths in pixels of each column of the sub-patches inner grid. |
| **height** | integer or array of integers | 1 | no | The heights in pixels of each row of the sub-patches inner grid. |
| **border** | integer or array of 2 integers | 2 | no | The horizontal and vertical border size in pixels. The same value is used for both if specified as a single integer. |
| **bordercolor** | color (see [Specifying colors](#specifying-colors) below) | 2 | no | The border color. Nothing will be draw in the borders if not specified. |
| **spacing** | integer or array of 2 integers | 2 | no | The spacing between grid columns and rows in pixels. The same value is used for both if specified as a single integer. |
| **spacingcolor** | color (see [Specifying colors](#specifying-colors) below) | 2 | no | The grid spacing color. Nothing will be draw in the spacings if not specified. |
| **color** | color (see [Specifying colors](#specifying-colors) above) | 1 | no | The sub-patch's solid background color. |
| **hramp** | gradient (see [Specifying gradients](#specifying-gradients) above) | 1 | no | The sub-patch's background horizontal gradient. |
| **vramp** | gradient (see [Specifying gradients](#specifying-gradients) above) | 1 | no | The sub-patch's background vertical gradient. |
| **hsquare** | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) above) | 2 | no | The sub-patch's background horizontal square frequency grating. |
| **vsquare** | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) above) | 2 | no | The sub-patch's background vertical square frequency grating. |
| **hsine**<br>**hcosine** | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) above) | 2 | no | The sub-patch's background horizontal sinusoidal frequency grating. |
| **vsine**<br>**vcosine** | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) above) | 2 | no | The sub-patch's background vertical sinusoidal frequency grating. |
| **image** | string | 2 | no | A TIFF file to be composited onto the subpatch after child subpatches have been drawn. If the file has an alpha channel, alpha premultiplication will be assumed. The path may be specified relative to T-PAT file. |
| **description** | string | 2 | no | A description of the current sub-patch. This overrides the parents corresponding "descriptions" entry for this sub-patch.* |
| **left** | integer | 1 | no | The sub-patch's left position in its containing patch's grid starting at 0. |
| **right** | integer | 1 | no | The sub-patch's right position in its containing patch's grid starting at 0. |
| **top** | integer | 1 | no | The sub-patch's top position in its containing patch's grid starting at 0. |
| **bottom** | integer | 1 | no | The sub-patch's bottom position in its containing patch's grid starting at 0. |
| **subpatches** | array of sub-patches | 1 | no | The sub-patch's own sub-patches |
| **descriptions** | array of string | 2 | no | A description of the sub-patches. This must be the same length as the sub-patch array and "..." means "refer to another description for the patch with the same color value."* |

(*) These fields may be used to automatically generates a PDF specification for the test pattern.

**left**, **top**, **right** and **bottom** are always expressed in cells of the containing patch. Specifying **left** or **top** overrides the sub-patch's default left or top positioning, respectively, which is always the next position along in the containing patch's grid, from left to right then from top to bottom. **right** and **bottom** override the sub-patch's default width and height which is otherwise inherited from the previous sub-patch. The width and height also determine the X and Y increment for the sub-patch's default location.

As an example, if a sub-patch is located at row 1, column 2 and is 2 columns wide (`"top": 1, "left": 2, "right": 4`), the next sub-patch will be located, by default, at row 1, column 4 and will also be 2 columns wide. If the grid were only 5 columns wide, in order for it to not surpass the right edge of the grid, by default, the sub-patch would be re-positioned at the start of the next row: column 0, row 2.

T-PAT file example
==================

Below are the contents of the file `3_squares.tpat` included in this repository. The pattern is for a 32-bit image with three grey squares on top of a horizontal grey-scale gradient. The 3 squares are positioned in a 7x3 grid in cells located at: (1, 1), (3, 1) and (5, 1).

```
{
  "name": "3 squares",
  "depth": 32,
  "width": [210, 360, 210, 360, 210, 360, 210],
  "height": [360, 360, 360],
  "description": "Full screen horizontal ramp background",
  "hramp": [0, 1],
  "descriptions": ["50% grey", "...", "..."],
  "subpatches": [
    {
      "left": 1,
      "top": 1,
      "color": 0.5
    },
    {
      "left": 3,
      "color": 0.5
    },
    {
      "left": 5,
      "color": 0.5
    }
  ]
}
```

See the file `BT2111_HLG_10bit_narrow.tpat` for a more complete example.

Generating test pattern TIFF images
===================================

The python script `tpat2tiff.py` included in this repository generates a TIFF image file from a T-PAT file. Run the following command to generate a BT.2111 HLG 10-bit narrow-range test pattern image:

```
python3 tpat2tiff.py BT2111_HLG_10bit_narrow.tpat
```