# Kepler/K2 Quality Control

***Automated quality control of Kepler/K2 data products.***

This tool allows the [Guest Observer Office of NASA's Kepler/K2 Missions](https://keplerscience.arc.nasa.gov)
to perform a quick sanity check of its public data sets.

In particular, this tool verifies that Target Pixel Files
are wel-formatted and contain sensible data.
It does not replace the pipeline's existing suite of unit tests,
it merely provides an independent sanity check on the final data products
that the pipeline creates.
It is intended to be run prior to each data release and catch obvious errors
such as corrupt files or nonsensical data.


## Installation

```
git clone https://github.com/KeplerGO/k2-quality-control.git
cd k2-quality-control
python setup.py install
```


## Usage

Once installed, the package adds the `k2qc` command-line tool
which can be used to verify a directory of TPF files. For example:

```
$ k2qc /path/to/tpf-files/
Found 0 issues (234 files checked).
```

Type `--help` for more info:
```
$ k2qc --help
Usage: k2qc [OPTIONS] PATH

  Check Kepler/K2 data for errors.

  PATH must be the location of a Kepler/K2 Target Pixel File, or a directory
  containing such Target Pixel Files.

Options:
  --help  Show this message and exit.

```

One can also redirect the standard output to a text file, e.g.:

```
$ k2qc /path/to/tpf-files > foo.txt
```

The package also installs the following auxillary tools
to help inspect the contents of target pixel files:

```
$ k2qc-flags --help
Usage: k2qc-flags [OPTIONS] PATH

  Show a summary of the QUALITY flags.

Options:
  --plot
  --help  Show this message and exit.
```

```
$ k2qc-flux --help
Usage: k2qc-flux [OPTIONS] PATH

  Plots the FLUX, FLUX_BKG, and RAW_CNTS time series given a Target Pixel
  File.

Options:
  --help  Show this message and exit.
```

## Authors

Created by Geert Barentsen for the NASA Kepler/K2 Guest Observer Office.
