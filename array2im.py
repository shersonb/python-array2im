#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy
from PIL import Image, ImageFile
__version__ = "1.0"

"""Visualization of 2-dimensional numpy arrays."""


def array2im(a, brightness=1, contrast=1):
    P = (a.real * (a.real > 0) * brightness) ** contrast
    N = (-a.real * (a.real < 0) * brightness) ** contrast
    R = numpy.array(
        (256 * (1 - numpy.float64(0.5) ** P)).clip(max=255), dtype=numpy.uint8)[::-1]
    G = numpy.zeros(R.shape, dtype=numpy.uint8)
    B = numpy.array(
        (256 * (1 - numpy.float64(0.5) ** N)).clip(max=255), dtype=numpy.uint8)[::-1]
    return Image.fromarray(numpy.array([R, G, B]).swapaxes(0, 1).swapaxes(1, 2))

if __name__ == "__main__":
    import argparse
    import struct
    import os
    import sys
    import time
    from numpy import dtype, fromfile
    from numpy import save as npsave
    from numpy import load as npload
    import warnings
    warnings.filterwarnings('ignore')

    parser = argparse.ArgumentParser(
        description="Converts a two-dimensional numpy array into an image.")
    parser.add_argument("--in", "-i", dest="input", action="store",
                        help="Input file. Default: <stdin>.", default="-")
    parser.add_argument("--out", "-o", dest="output", action="store",
                        help="Output file. Default: <stdout>.", default="-")
    parser.add_argument("--brightness", "-b", dest="brightness",
                        action="store", help="Adjust brightness. Default: 1.", default=1)
    parser.add_argument("--contrast", "-c", dest="contrast",
                        action="store", help="Adjust contrast. Default: 1.", default=1)
    parser.add_argument("--quality", "-q", dest="quality", action="store",
                        help="JPEG quality, between 1 and 100. Only valid when saving image as a JPEG. Default: 95.", default=95)
    parser.add_argument("--progressive", "-p", dest="progressive", action="store_const",
                        help="Save progressive JPEG. Only valid when saving image as a JPEG.", const=True)
    parser.add_argument("--overwrite", "-y", dest="overwrite",
                        action='store_const', help="Overwrite output file, if it exists.", const=True)
    parser.add_argument("--no-overwrite", "-n", dest="nooverwrite", action='store_const',
                        help="Do not overwrite output file, if it exists.", const=True)
    args = parser.parse_args()

    msgout = sys.stdout if sys.stdout.isatty() else sys.stderr

    if args.overwrite and args.nooverwrite:
        print >>sys.stderr, "Cannot specify both '-y' and '-n'!"
        sys.exit()

    if args.input == "-":
        if sys.stdin.isatty():
            print >>sys.stderr, "Surely you are not typing the raw data into the terminal. Please specify input file, or pipe input from another program.\n"
            parser.print_help(sys.stderr)
            sys.exit()
        infile = sys.stdin
    else:
        infile = open(args.input, "rb")

    if args.output == "-":
        if sys.stdout.isatty():
            print >>sys.stderr, "Cowardly refusing to write binary data to terminal. Please specify output file, or redirect output to a pipe.\n"
            parser.print_help(sys.stderr)
            sys.exit()
        outfile = sys.stdout
        print >>sys.stderr, "Writing data to <stdout>."
    else:
        if os.path.exists(args.output):
            if args.nooverwrite:
                print >>sys.stderr, "Error: Output file '%s' exists. Terminating because '-n' was specified." % args.output
                sys.exit()
            elif args.overwrite:
                print >>msgout, "Warning: Output file '%s' exists. Overwriting because '-y' was specified." % args.output
            elif sys.stdin.isatty() and sys.stdout.isatty():
                overwrite = raw_input(
                    "Warning: Output file '%s' exists. Do you wish to overwrite file? (Y/N) " % args.output)
                while overwrite.upper() not in ("Y", "N", "YES", "NO"):
                    print >>msgout, "Invalid answer: '%s'" % overwrite
                    overwrite = raw_input(
                        "Warning: Output file '%s' exists. Do you wish to overwrite file? (Y/N) " % args.output)

                if overwrite.upper() in ("Y", "YES"):
                    print >>msgout, "Overwriting '%s'." % args.output
                    print >>msgout, ""
                elif overwrite.upper() in ("N", "NO"):
                    print >>msgout, "Operation aborted."
                    sys.exit()
            else:
                print >>sys.stderr, "Operation aborted. Cowardly refusing to overwrite '%s'." % args.output
                sys.exit()

        outfile = args.output

    tag = npload(infile)
    metadata = npload(infile)
    data = npload(infile)
    if infile is not sys.stdin:
        infile.close()

    if len(data.shape) != 2:
        print >>sys.stderr, "Expected a two-dimensional array. Got an array with shape %s instead." % (
            data.shape,)
        sys.exit()

    kind_str = {
        "f": "floating point",
        "i": "integer",
        "u": "unsigned integer",
        "b": "boolean",
        "c": "complex"
    }

    if data.dtype.kind in "iub":
        print >>sys.stderr, "Error: Data type '%s' not supported." % kind_str[
            data.dtype.kind]
        sys.exit()
    elif data.dtype.kind == "c":
        print >>msgout, "Warning: Discarding imaginary part of 'complex' array."

    try:
        args.brightness = float(args.brightness)
    except ValueError:
        print >>sys.stderr, "Bad parameter for brightness. Expected floating point or integer, got '%s' instead." % args.brightness
        sys.exit()

    try:
        args.contrast = float(args.contrast)
    except ValueError:
        print >>sys.stderr, "Bad parameter for contrast. Expected floating point or integer, got '%s' instead." % args.contrast
        sys.exit()

    try:
        args.quality = int(args.quality)
    except ValueError:
        print >>sys.stderr, "Bad parameter for quality. Expected integer between 1 and 100, got '%s' instead." % args.quality
        sys.exit()

    if not (1 <= args.quality <= 100):
        print >>sys.stderr, "Bad parameter for quality. Expected integer between 1 and 100, got '%s' instead." % args.quality
        sys.exit()

    H, W = data.shape

    t0 = time.time()
    print >>msgout, u"Saving %d×%d image to '%s'..." % (W, H, args.output),
    msgout.flush()
    img = array2im(data, brightness=args.brightness, contrast=args.contrast)
    ImageFile.MAXBLOCK = img.size[0] * img.size[1]
    img.save(outfile, progressive=args.progressive, quality=args.quality)
    print >>msgout, "%.2f seconds" % (time.time() - t0)
