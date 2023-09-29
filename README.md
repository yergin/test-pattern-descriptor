JSON Test Pattern Descriptor
============================

Color
-----

Examples:
- `"col": 0.1` - normalised grey scale (0.1, 0.1, 0.1)
- `"col": [0.1, 0.5, 0.9]` - Normalised 0-to-1
- `"col10": [651, 286, 705]` - 10-bit
- `"col12": [2604, 1144, 2820]` - 12-bit

Top-level fields
----------------

Name and background color (black):
```
{
  "name": "BT2111 HLG Narrow",
  "depth": 10
  "color": 0
}
```

The default background color is black.

Grid
----

Two cells stacked on top of each other (1920x810 and 1920x270):
```
{
  "width": 1920,
  "height": [810,270]
}
```

A grid of 15x4 (60) cells in an area the size of 1920x810:
```
{
  "width": [240,206,103,103,103,103,102,102,103,103,103,103,103,103,240],
  "height": [90,540,90,90]
}
```

Patches
-------

A gray patch 2 cells tall in the last column, first 2 rows:
```
{
  "width": [240,206,103,103,103,103,102,102,103,103,103,103,103,103,240],
  "height": [90,540,90,90]
  "patch": {
    "left": 14, "bottom": 2,
    "color": 414
  }
}
```

By default, the first patch begins at "top": 0, "left": 0 and its width and height is 1 cell.

Rows of patches, each patch inheriting the width, height and color representation of the previous patch:
```
{
  "width": [240,206,103,103,103,103,102,102,103,103,103,103,103,103,240],
  "height": [90,540,90,90]
  "patch": [
    {
      "bottom": 2, 
      "col10": 414
    },
    {
      "bottom": 1,
      "col10": 940
    },
    [940,940,64],[64,940,940],[64,940,64],[940,64,940],[940,64,64],[64,64,940],
    {
      "bottom": 2,
      "col10": 414
    },
    {
      "top": 1, "bottom": 2, "left": 1,
      "col10": 721
    },
    [721,721,64],[64,721,721],[64,721,64],[721,64,721],[721,64,64],[64,64,721]
  ]
}
```

The above example shows that patches can be defined as an array of color values but they may even be defined as a simple number representing the greyscale color.

Ramps:
```
{
  "left": {
    "grid": 2,
    "col10": 4
  },
  "right": { "col10": 1019 }
}
```

Nested cells
------------

```
{
  "name": "BT2111 HLG 10bit Narrow",
  "col10": 0,
  "width": 1920,
  "height": [810,270],
  "patch": [
    {
      "width": [240,206,103,103,103,103,102,102,103,103,103,103,103,103,240],
      "height": [90,540,90,90]
      "patch": [
        {
          "bottom": 2,
          "col10": 414
        },
        {
          "bottom": 1,
          "col10": 940
        },
        [940,940,64],[64,940,940],[64,940,64],[940,64,940],[940,64,64],[64,64,940],
        {
          "bottom": 2,
          "col10": 414
        }
      ]
    },
    {
      "top": 1
    }
  ]
}
```
