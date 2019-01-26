scanbro
=======

This project grew out of the desire to provide an efficient method for
scanning one or more documents into a searchable, space-efficient PDF.
The name stems from the detail that I currently use it with a Brother
scanner. In principle however, any printer supported by SANE can be
used.

The script is distributed under the [MIT License](LICENSE).

### Installation

There is no installation necessary, just make sure you have
[Python 3](www.python.org) installed.

Currently the scripts make use of SANE, Tesseract, and Ghostscript, so these are
also dependencies. ImageMagick can also be useful if you want to extend the
script with your own filters.

You may install the binary to a directory of your choosing with a name of
your choosing.

### Usage

I prefer to define aliases of the quality settings I want to have for scanning.
A set of examples can be found in the `aliases.sh` file.
In whichever directory I am in, I can then scan from the flatbed:

```
$ scan-xs -s flatbed 2019-01_My_Filename
:: Scan from Brother MFC-J5730DW
-> scanimage --device-name brother4:net1;dev0 --format tiff -x 210 -y 297 --mode Black & White --resolution 300
:: Read file 2019-01_My_Filename.tiff
:: Transform [2019-01_My_Filename.tiff ...] => [2019-01_My_Filename.tesserac
-> tesseract 2019-01_My_Filename.tiff 2019-01_My_Filename.tesseract -l eng+d
:: Transform [2019-01_My_Filename.tesseract.pdf ...] => 2019-01_My_Filename.
-> gs -dNOPAUSE -dSAFER -dQUIET -dBATCH -sDEVICE=pdfwrite -dCompatibil
OLD_BW.tesseract.gs.pdf -dPDFSETTINGS=/ebook -dEmbedAllFonts=false -dC
ageResolution=100 -dGrayImageResolution=100 -dMonoImageResolution=100
orConversionStrategyForImages=Gray 2019-01_My_Filename.tesseract.pdf
-> rm 2019-01_My_Filename.tesseract.pdf
-> mv 2019-01_My_Filename.tesseract.gs.pdf 2019-01_My_Filename.pdf
-> rm 2019-01_My_Filename.tiff
```

Here, `scan-xs` is an alias to `scanbro -m bw -ccavg low`. The output of the
above command will be `2019-01_My_Filename.pdf`, provided no error occurred. We
didn't have to specify `-s flatbed`, but it keeps the filename simpler for
demonstration purposes, as we don't need to do batch scanning.

For other usage examples, have a look at the help. For evaluating the quality
settings you would like to use, the `--gs-benchmark` option is quite useful.
Note that it is highly recommended to scan with a resolution of at least 300
DPI. This not only provides the best OCR results from Tesseract, but
Ghostscript's downsampling is much more effective the higher the DPI of the
input file.

Enjoy!

### Known Issues

- Dryrun mode does not always work reliably.
- When specifiying the output name initially, should prompt before
  overwriting.
- When `--clean` is specified 3 times, existing files are overwritten, not
  deleted. This means that it is possible for more files to be in the
  output that were actually scanned.
