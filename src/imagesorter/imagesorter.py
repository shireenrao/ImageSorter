'''
Created on Jul 07, 2012

@author: shireenrao

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
'''
import os, sys, errno
import shutil
import getopt
import glob
import logging
import time
import datetime, calendar
from PIL import Image
from PIL.ExifTags import TAGS

_version = 0.1
_source = ""
_target = ""

def version():
    """This Prints the version"""
    print "imagesorter.py: Version " + str(_version)

def usage():
    """This prints the usage."""
    print __doc__

def get_create_date(exif_data):
    """Get embedded create date from EXIF data."""
    retval=None

    for (k,v) in exif_data.items():
        key = str(k)
        if "DateTimeOriginal" in key:
            retval = datetime.datetime.strptime(v,'%Y:%m:%d %H:%M:%S')

    return retval

def get_exif_data(fname):
    """Get embedded EXIF data from image file."""
    ret = {}
    try:
        img = Image.open(fname)
        if hasattr( img, '_getexif' ):
            exifinfo = img._getexif()
            if exifinfo != None:
                for tag, value in exifinfo.items():
                    decoded = TAGS.get(tag, tag)
                    ret[decoded] = value
    except IOError:
        log.critical( 'IOERROR ' + fname)
    return ret

def main(argv):
    global log
    formats = ('jpg')
    log = logging.getLogger()
    ch  = logging.StreamHandler()

    localtime   = time.localtime()
    timeString  = time.strftime("%Y%m%d%H%M%S", localtime)
    debug = True
    log_file = os.path.join(os.getcwd(),'imagesorter.log.' + timeString)

    if os.path.exists(os.path.dirname(log_file)):
        fh = logging.FileHandler(log_file)
    else:
        raise "log directory does not exist (" + os.path.dirname(log_file) + ")"
        sys.exit(1)

    log.addHandler(ch)
    log.addHandler(fh)

    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    try:
        opts, args = getopt.getopt(argv, "hvs:t:", ["help", "version", "source=", "target="])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    if not opts:
        version()
        usage()
        exit()

    _source = ""
    _target = ""

    for o, a in opts:
        if o in ("-h", "--help"):
            version()
            usage()
            exit()
        elif o in ("-v", "--version"):
            version()
            exit()
        elif o in ("-s","--source"):
            _source = a
        elif o in ("-t", "--target"):
            _target = a
        else:
            assert False, "unhandled option"


    if not _source:
        _source = os.getcwd()

    if not _target:
        print "No target location provided!, Where will I copy this?"
        usage()
        exit()

    if not os.path.exists(_source):
        print "Source " + _source + " is not a directory!"
        usage()
        exit()

    if not os.path.exists(_target):
        print "Target " + _target + " is not a directory!"
        usage()
        exit()

    log.info("Processing and sorting " + _source + " to target " + _target)


    fileList = []
    for root, dirs, files in os.walk(_source):
        for name in files:
            filename = os.path.join(root,name)
            if filename.lower().endswith(formats):
                fileList.append(filename)

    problems_loc = os.path.join(_target,"exif_problems")
    try:
        os.makedirs(problems_loc)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else: raise
    to_be_processed = len(fileList)
    log.info ("images to be processed -> " + str(to_be_processed))

    processCount = 0
    nocreatedateCount = 0
    copyCount = 0
    skipCount = 0
    exceptionCount = 0
    for file in fileList:
        processCount = processCount + 1
        filename = os.path.basename(file)
        #foldername = os.path.dirname(file)
        exif = {}
        exif = get_exif_data(file)
        create_date = get_create_date(exif)
        if create_date:
            year_str = str(create_date.year)
            month = create_date.month
            month_name = calendar.month_name[month]
            day = create_date.day
            if month < 10:
                month_str = '0'+str(month)
            else:
                month_str= str(month)
            if day < 10:
                day_str = '0'+str(day)
            else:
                day_str=str(day)

            folder_name = year_str + "_" + month_str + "_" + day_str
            path = os.path.join(_target,year_str,month_name,folder_name)
            try:
                os.makedirs(path)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    pass
                else: raise
            dest_file = os.path.join(path,filename)
            try:
                if not os.path.isfile(dest_file):
                    shutil.copy2(file, path)
                    copyCount = copyCount + 1
                    log.info( "(" + str(processCount) + "/" + str(to_be_processed) +") " + filename + " => " + path)
                else:
                    skipCount = skipCount + 1
                    log.error( "(" + str(processCount) + "/" + str(to_be_processed) +") " + file + " not copied as already exists in destination")
            except OSError as exc:
                exceptionCount = exceptionCount + 1
                log.critical( "(" + str(processCount) + "/" + str(to_be_processed) +") " + "Skipped " + file + " due to exception!")
                pass
        else:
            nocreatedateCount = nocreatedateCount + 1
            log.error( "(" + str(processCount) + "/" + str(to_be_processed) +") " + "Skipped " + file + " due to no create date!")
            new_dest_file = os.path.join(problems_loc,filename)
            try:
                if not os.path.isfile(new_dest_file):
                    shutil.copy2(file, problems_loc)
            except:
                pass

    log.info( "Copy Complete")
    log.info( "Files not copied because of no create date exif data: " + str(nocreatedateCount))
    log.info( "Files copied: " + str(copyCount))
    log.info( "Files skipped as they exist in destination: " + str(skipCount))
    log.info( "Exceptions while copying: " + str(exceptionCount))

if __name__ == '__main__':
    main(sys.argv[1:])