NAME
    imagesorter - This is a utility to sort images and videos into directories
    based on year/month and date taken from the exif data of the image

SYNOPSIS
    imagesorter [hvs:t:f:]

Usage:
    % imagesorter -s /path/to/source -t /path/to/target [-f format]

    where /path/to/source is where all the images are stored
    and /path/to/target is where images will be sorted
    and optional argument for format for target directory structure

    The source tag is optional. If not provided, it will take the
    current directory.

    The options are as follows:

    -h --help              Prints this
    -v --version           Prints version
    -s --source            Directory to process. If not set will process
                           current directory
    -t --target            Expression to remove from file name
    -f --format            Optional format for target directory structure.
                           Default structure created under target directory
                           is yyyy/mmmm/yyyy_mm_dd
                           e.g. 2013/January/2013_01_13
                           The format is supplied as "yyyy/yyyy_mm_dd".
                           This will create a directory structure of the format
                           "2013/2013_01_13" under your target directory.
                           Where 2013 is a sub-directory under the target
                           directory and 2013_01_13 is a sub-directory under
                           2013


                           Here are the possible format types -
                           d    day as a number without leading zero (1-31)
                           dd   day as a number with leading zero (01-31)
                           ddd  day as an abreviation (Sun-Sat)
                           dddd day as a full name (Sunday-Saturday)
                           m    month as a number without leading zero (1-12)
                           mm   month as a number with leading zero (01-12)
                           mmm  month as an abreviation (Jan-Dec)
                           mmmm month as a full name (January-December)
                           yy   year as a two-digit number (00-99)
                           yyyy year as a four digit number

    A log file is created in the same location where you would run the script.
