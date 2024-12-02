"T-PAT": Test Pattern Descriptor Specification V2
=================================================

*Updated: 2024-12-01*

The purpose of T-PAT (**T**est **PAT**tern) files is to concisely describe the positioning and colors of rectangular color patches in a test pattern image. They can serve as specifications from which test pattern images can be generated. T-PAT files are JSON files with a `.tpat` extension.

Each T-PAT file represents a test pattern image of a specified size and bit-depth. It contains hierarchical data describing the layout and color of each color patch within its 'container' patch. At the top of the hierarchy is the top-level patch representing the entire image. Patches can be split into a grid of "cells" which serve to locate "sub-patches".

The `version` field must be included to enable certain features like specifying borders, spacings, image overlays and descriptions. In the following tables, the superscript next to the field indicates the version in which support for the field was added. The fields with no superscripts were introduced in version 1.

General top-level fields
------------------------

| Field | Type | Required | Description |
| - | - | - | - |
| **version** | integer | no | The T-PAT version number (defaults to 1 if omitted). |
| **name** | string | no | A name describing the test pattern. |
| **depth** | integer | yes | The bit depth of the color data - either 8, 10, 12, 16 or 32(float). |
| **columns**<sup>2</sup><br>**width** | integer or array of integers | yes | The widths in pixels of each column of the image's grid. |
| **rows**<sup>2</sup><br>**height** | integer or array of integers | yes | The heights in pixels of each row of the image's grid. |
| **border**<sup>2</sup> | integer or array of 2 integers | no | The vertical and horizontal border sizes, respectively, in pixels. The same value is used for both if specified as a single integer. |
| **spacing**<sup>2</sup> | integer or array of 2 integers | no | The spacing between grid rows and columns, respectively, in pixels. The same value is used for both if specified as a single integer. |

(2) Introduced in version 2.

Image size
----------

The image size is determined by the fields `width` or `columns`, `height` or `rows`, `border` and `spacing`. If `width` or `columns` is defined as a single integer, the image width will be equal to `width + 2 * border` to account for the borders at either side. If `width` or `columns` is an array describing the column widths in the top-level grid, the image width will be equal to the borders plus the sum of the individual column widths plus the spacings between each column. The same applies to `height` when determining the final image height.

If both `width` and `columns` are specified, `width` must be a single integer and equal to the image's width which has been calculated from `columns`, `border` and `spacing` as described above. Similarly, if both `height` and `rows` are specified, `height` must be a single integer and equal to the image's height which has been calculated from `rows`, `border` and `spacing`.

Grids
-----

Rather than specifying the positions and sizes of each color patch individually, a T-PAT file will define a grid in terms of row heights and column widths. Color patches are then listed from left to right, top to bottom, filling each cell in the grid. The `cell` field of a patch will cause the position of the patch to skip to a particular row and column in the grid, and can also describe a patch as spanning more than one row or column. Cells are counted starting at row 1, column 1.

Patches may themselves contain a grid and sub-patches. This makes it possible to divide the test pattern up into rectangular areas and define patches within a given area consecutively.

Grids start and end within the container patch's borders and rows and columns will be separated by uniform spacings according to the `spacing` field, if specified.

Patches spanning multiple rows or columns may opt to inherit the containing patch's grid and spacing so as to define an area in a grid without needing to redefine the grid sizes and spacing. The special string value `parent` indicated this.

Grid-related fields
-------------------

| Field | Type | Required | Description |
| - | - | - | - |
| **columns**<sup>2</sup><br>**width** | integer or array of integers or `"parent"` | no* | The widths in pixels of each column of the patch's grid. If set to "parent", the containing patch's horizontal grid and spacing will be used. |
| **rows**<sup>2</sup><br>**height** | integer or array of integers or `"parent"` | no* | The heights in pixels of each row of the patch's grid. If set to "parent", the containing patch's vertical grid and spacing will be used. |
| **border**<sup>2</sup> | integer or array of 2 integers | no | The vertical and horizontal border sizes, respectively, in pixels. The same value is used for both if specified as a single integer. |
| **spacing**<sup>2</sup> | integer or array of 2 integers | no | The spacing between grid rows and columns, respectively, in pixels. The same value is used for both if specified as a single integer. |
| **cell**<sup>2</sup> | array of 2 or 4 integers | no | Positions the patch at a particular row and column, respectively, within the containing patches grid rather than at the next cell position according to the left-to-right, top-to-bottom order. If 2 integers are specified, the patch will fill a single cell. If 4 integers are specified, the patch will span multiple cells where the 1st and 2nd integers specify the top-left cell's row and column and the 3rd and 4th integer specify the bottom-right cell's row and column for the range of cells being spanned.** |
| **top**<br>**left**<br>**bottom**<br>**right** | integer | no | these are deprecated in version 2 in favour of the `cell` field and otherwise correspond to the top-left cell, except starting at row 0, column 0, and the bottom-right cell in the cell range, incremented by one. |

(*) Only required at the top level. Will default to a single row or column taking up all the available space if not specified.

(**) If `cell` is not specified, the cell will span the same number of rows and columns as the previous cell.

Color patches
-------------

Each patch's background may be filled with either:
- a solid color (`color`)
- a horizontal ramp (`hramp`)
- a vertical ramp (`vramp`)
- a horizontal frequency grating (`hsquare`, `hsine` or `hcosine`)
- a vertical frequency grating (`vsquare`, `vsine` or `vcosine`)

If `border` has been specified, the border will drawn as part of the background and filled with the color `bordercolor`, if `bordercolor` has been specified, otherwise it is left as transparent.

If the patch contains sub-patches, first the spacings will be filled using the color `bordercolor`, if `bordercolor` has been specified. Each sub-patch will then be drawn on top of the background.

Lastly, if an `image` field is present, the specified image file will be overlaid onto the patch.

Drawing and patch-related fields
--------------------------------

| Field | Type | Required | Description |
| - | - | - | - |
| **bordercolor**<sup>2</sup> | color (see [Specifying colors](#specifying-colors) below) | no | The border and spacing color. The borders and spacings will be transparent if not specified (black if it is the top-level border). |
| **color** | color (see [Specifying colors](#specifying-colors) below) | no | The patch's solid background color. |
| **hramp** | gradient (see [Specifying gradients](#specifying-gradients) below) | no | The patch's background horizontal gradient. |
| **vramp** | gradient (see [Specifying gradients](#specifying-gradients) below) | no | The patch's background vertical gradient. |
| **hsquare**<sup>2</sup> | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) below) | no | The patch's background horizontal square frequency grating. |
| **vsquare**<sup>2</sup>| frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) below) | no | The patch's background vertical square frequency grating. |
| **hsine**<sup>2</sup><br>**hcosine**<sup>2</sup> | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) below) | no | The patch's background horizontal sinusoidal frequency grating. |
| **vsine**<sup>2</sup><br>**vcosine**<sup>2</sup> | frequency grating (see [Specifying frequency gratings](#specifying-frequency-gratings) below) | no | The patch's background vertical sinusoidal frequency grating. |
| **image**<sup>2</sup> | string | no | A TIFF file to be composited onto the patch after sub-patches have been drawn. The path may be specified relative to T-PAT file. |
| **premul**<sup>2</sup> | boolean | no | Whether the composited image is premultiplied by its alpha channel. |
| **description**<sup>2</sup> | string | no | A description of the current patch. This overrides the containing patch's corresponding "descriptions" entry for this patch.* |
| **descriptions**<sup>2</sup> | array of string | no | A description of the sub-patches. This must be the same length as the sub-patch array and "..." means "refer to another description for the patch with the same color value."* |
| **patches**<sup>2</sup><br>**subpatches** | array of sub-patches (see [Sub-patches](#Sub-patches) below) | no | The patch's sub-patches. `subpatches` is deprecated in version 2 in favour of `patches`. |

(*) Although description do not affect how test patterns are rendered, they may be used by future tools to automatically generate PDF or HTML specifications for the test pattern.

Only one of `color`, `hramp`, `vramp`, `hsquare`, `vsquare`, `hsine`, `vsine`, `hcosine` or `vcosine` may be defined. If no background is specified, the patch's background color will be black.

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

Frequency gratings, whether horizontal or vertical, sinusoidal or square, are defined as a 3 or 4-element array. 3 elements specify a constant frequency followed by the 2 alternating colours whereas 4 elements specify the beginning and ending frequencies for a linear frequency sweep followed by the 2 alternating colours.

Frequencies are integers or floats specifying the half-period of the gratings repetition in pixels, a half-period of 1 pixel representing the nyquist frequency. 

The last two elements specify the two colors the grating alternates between, the first one being the left-most or top-most color.

`hcosine` and `vcosine` are equivalent to `hsine` and `vsine` with the only difference being the phase at which they start.
 No spatial filtering is used with `hsquare` and `vsquare`, it is therefore recommended to employ sinusoidal rather than square frequency sweeps.

T-PAT file example
==================

Below are the contents of the file `3_squares.tpat` included in this repository. The pattern is for a 32-bit image with three grey squares on top of a horizontal grey-scale gradient. The 3 squares are positioned in a 7x3 grid in cells located at: (1, 1), (3, 1) and (5, 1).

```
{
  "version": 2,
  "name": "3 squares",
  "depth": 32,
  "width": 1920,
  "height": 1080,
  "rows": [360, 360, 360],
  "columns": [210, 360, 210, 360, 210, 360, 210],
  "description": "Full screen horizontal ramp background",
  "hramp": [0, 1],
  "descriptions": ["50% grey", "...", "..."],
  "patches": [
    {
      "cell": [2, 2],
      "color": 0.5
    },
    {
      "cell": [2, 4],
      "color": 0.5
    },
    {
      "cell": [2, 6],
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