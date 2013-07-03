#!/usr/bin/env python
'''
Created on Feb 7, 2013

@author: shireenrao
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
'''
import sys
import EXIF
import datetime
import os.path
import time
import os
import errno
import shutil
import getopt
import logging
import calendar
from hachoir_core.error import HachoirError
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_core.tools import makePrintable
from hachoir_metadata import extractMetadata
from hachoir_core.i18n import getTerminalCharset
from PIL import Image #@UnresolvedImport
from PIL.ExifTags import TAGS #@UnresolvedImport


_version = 0.2
_source = ""
_target = ""


def version():
    """This Prints the version"""
    print "sorter.py: Version " + str(_version)


def usage():
    """This prints the usage."""
    print __doc__


def get_hachoir_create_date(fname):
    global log
    retval = None
    filename, realname = unicodeFilename(fname), fname
    parser = createParser(filename, realname)
    if not parser:
        log.critical( 'Unable to parse file ' + fname)
        return retval
    try:
        metadata = extractMetadata(parser)
    except HachoirError, err:
        log.critical( 'Metadata extraction error for ' + fname + ' - '+ unicode(err))
        metadata = None
    if not metadata:
        log.critical( 'Unable to extract metadata for ' + fname )
        return retval

    metaitems = metadata.getItems('creation_date')
    if not metaitems:
        log.critical( 'Unable to extract metaitmes for ' + fname )
        return retval

    date_str = metaitems.values[0].text
    if not date_str:
        log.critical( 'Unable to extract creation date for ' + fname )
    else:
        try:
            retval = datetime.datetime.strptime(str(date_str), '%Y:%m:%d %H:%M:%S')
        except:
            try:
                retval = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except:
                retval = None

    return retval


def get_pil_exif_data(fname):
    """Get embedded EXIF data from image file."""
    global log
    ret = {}
    try:
        img = Image.open(fname)
        if hasattr(img, '_getexif'):
            exifinfo = img._getexif()
            if exifinfo != None:
                for tag, value in exifinfo.items():
                    decoded = TAGS.get(tag, tag)
                    ret[decoded] = value
    except IOError:
        log.critical( 'IOERROR ' + fname)
    except:
        log.critical( 'ERROR ' + fname)
        ret = {}
    return ret


def get_exif_data(fname):
    """Get embedded EXIF data from image file."""
    global log
    tags = {}
    try:
        img = open(fname, 'rb')
        tags = EXIF.process_file(img)
        img.close()
    except IOError:
        log.critical('IOERROR ' + fname)
    except:
        tags = get_pil_exif_data(fname)
    return tags


def get_pil_create_date(exif_data):
    """Get embedded create date from EXIF data."""
    retval = None

    for (k, v) in exif_data.items():
        key = str(k)
        if "DateTimeOriginal" in key:
            retval = v.strip() #datetime.datetime.strptime(v,'%Y:%m:%d %H:%M:%S')

    return retval


def get_create_date(exif_data):
    """Get embedded create date from EXIF data."""
    retval = None
    try:
        date_str = exif_data['EXIF DateTimeOriginal'].values
    except:
        try:
            date_str = get_pil_create_date(exif_data)
        except:
            date_str = None

    if date_str:
        try:
            retval = datetime.datetime.strptime(str(date_str), '%Y:%m:%d %H:%M:%S')
        except:
            try:
                retval = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except:
                retval = None

    return retval


def has_thm_file(filename):
    """For given thm filename, find corresponding avi file. Return true if found """
    retval = (False, '', '')
    dir_name = os.path.dirname(filename)
    file_name = os.path.basename(filename)
    f_name, f_ext = os.path.splitext(file_name)
    thm_file1 = os.path.join(dir_name, f_name + '.THM')
    thm_file2 = os.path.join(dir_name, f_name + '.thm')
    if not os.path.isfile(thm_file1):
        if os.path.isfile(thm_file2):
            retval = (True, f_name+'.thm', thm_file2)
    else:
        retval = (True, f_name+'.THM', thm_file1)
    return retval


def main(argv):
    global log
    formats = ('jpg', 'avi', 'cr2', 'mov', 'mp4')
    log = logging.getLogger()
    ch = logging.StreamHandler()

    localtime = time.localtime()
    timeString = time.strftime("%Y%m%d%H%M%S", localtime)
    debug = True
    log_file = os.path.join(os.getcwd(), 'imagesorter.log.' + timeString)

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
        elif o in ("-s", "--source"):
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
            filename = os.path.join(root, name)
            if filename.lower().endswith(formats):
                fileList.append(filename)

    problems_loc = os.path.join(_target, "exif_problems")
    try:
        os.makedirs(problems_loc)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise
    to_be_processed = len(fileList)
    log.info("images to be processed -> " + str(to_be_processed))

    processCount = 0
    nocreatedateCount = 0
    copyCount = 0
    skipCount = 0
    exceptionCount = 0
    avionlycount = 0
    avithmcount = 0
    has_avi = False
    for file in fileList:
        processCount = processCount + 1
        filename = os.path.basename(file)
        orig_path = os.path.dirname(file)
        has_thm = False
        is_video_file = False
        if filename.lower().endswith('avi'):
            is_video_file = True
            has_thm, thm_filename, thm_fullpath = has_thm_file(file)
        if filename.lower().endswith(('mov', 'mp4')):
            is_video_file = True

        create_date = None
        if not is_video_file:
            exif = get_exif_data(file)
            create_date = get_create_date(exif)
        else:
            if is_video_file and has_thm:
                avithmcount = avithmcount + 1
                exif = get_exif_data(thm_fullpath)
                create_date = get_create_date(exif)
            else:
                avionlycount = avionlycount + 1
                create_date = get_hachoir_create_date(file)

        if create_date:
            year_str = str(create_date.year)
            month = create_date.month
            month_name = calendar.month_name[month]
            day = create_date.day
            if month < 10:
                month_str = '0'+str(month)
            else:
                month_str = str(month)
            if day < 10:
                day_str = '0'+str(day)
            else:
                day_str = str(day)

            folder_name = year_str + "_" + month_str + "_" + day_str
            destpath = os.path.join(_target, year_str, month_name, folder_name)
            try:
                os.makedirs(destpath)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    pass
                else:
                    raise
            dest_file = os.path.join(destpath, filename)
            try:
                if not os.path.isfile(dest_file):
                    shutil.copy2(file, destpath)
                    copyCount = copyCount + 1
                    log.info("(" + str(processCount) + "/" + str(to_be_processed) + ") " + filename + " => " + destpath)
                else:
                    skipCount = skipCount + 1
                    log.error("(" + str(processCount) + "/" + str(to_be_processed) + ") " + file + " not copied as already exists in destination")
            except OSError as exc:
                exceptionCount = exceptionCount + 1
                log.critical("(" + str(processCount) + "/" + str(to_be_processed) + ") " + "Skipped " + file + " due to exception!")
                pass
            if has_thm:
                dest_thmfile = os.path.join(destpath, thm_filename)
                try:
                    if not os.path.isfile(dest_thmfile):
                        shutil.copy2(thm_fullpath, destpath)
                        #copyCount = copyCount + 1
                        log.info("(" + str(processCount) + "/" + str(to_be_processed) + ") " + thm_filename + " => " + destpath)
                    else:
                        #skipCount = skipCount + 1
                        orig_thm_file = os.path.join(orig_path, thm_filename)
                        log.error("(" + str(processCount) + "/" + str(to_be_processed) + ") " + orig_thm_file + " not copied as already exists in destination")
                except OSError as exc:
                    #exceptionCount = exceptionCount + 1
                    log.critical("(" + str(processCount) + "/" + str(to_be_processed) + ") " + "Skipped " + file + " due to exception!")
                    pass

        else:
            nocreatedateCount = nocreatedateCount + 1
            log.error("(" + str(processCount) + "/" + str(to_be_processed) + ") " + "Skipped " + file + " due to no create date!")
            new_error_dest = os.path.join(problems_loc, orig_path[1:])
            try:
                os.makedirs(new_error_dest)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    pass
                else:
                    raise
            new_dest_file = os.path.join(new_error_dest, filename)
            try:
                if not os.path.isfile(new_dest_file):
                    shutil.copy2(file, new_error_dest)
            except:
                pass

    log.info("Copy Complete")
    log.info("Files not sorted because of no create date exif data: " + str(nocreatedateCount))
    log.info("Files copied: " + str(copyCount))
    log.info("Files skipped as they exist in destination: " + str(skipCount))
    log.info("Exceptions while copying: " + str(exceptionCount))


if __name__ == '__main__':
    main(sys.argv[1:])
