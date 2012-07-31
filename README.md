NAME
    imagesorter - This is a utility to sort images into directories based on
              year/month and date taken from the exif data of the image

SYNOPSIS
    imagesorter [hvs:t:]

Usage:
    % imagesorter -s /path/to/source -t /path/to/target

    where /path/to/source is where all the images are stored
    and /path/to/target is where images will be sorted

    The source tag is optional. If not provided, it will take the
    current directory.

    The options are as follows:

    -h --help              Prints this
    -v --version           Prints version
    -s --source            Directory to process. If not set will process current directory
    -t --target            Expression to remove from file name

    A log file is created in the same location as the one would run the script.