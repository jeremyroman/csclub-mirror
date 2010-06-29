#!/usr/bin/env python
"""make-index.py

Generates an nice index of the directories from a
template.

Original Author: Jeremy Roman <jbroman@csclub.uwaterloo.ca>

So if you don't like how I did something,
I'm the person you get to complain to.
Please be gentle.
"""

import os, sys, time
from subprocess import Popen, PIPE
from optparse import OptionParser
import yaml, mako.exceptions, webhelpers.html.tags
from mako.template import Template

def reformat_size(size):
    """Reformats '124M' to '124 MB', et cetera."""
    if size[-1].isalpha():
        return size[:-1] + " " + size[-1] + "B"
    else:
        return size

def atomic_write(filename, body):
    """Atomically write to a file by writing a
    temporary file and then moving it to replace
    the desired output file.
    
    This ensures that partial files are never seen
    by clients."""
    
    # generate an appropriate temporary filename
    # in the same directory
    tmp_filename = "%s.%d.tmp" % (filename, os.getpid())
    
    # open the directory so that we can fsync it
    dir = os.open(os.path.realpath(os.path.dirname(filename)), \
                      os.O_DIRECTORY | os.O_RDONLY)
    
    # write to the temporary file
    tmp = open(tmp_filename, 'w')
    print >>tmp, body
    tmp.flush()
    os.fsync(tmp.fileno())
    tmp.close()
    
    # atomically replace the actual file
    os.rename(tmp_filename, filename)
    os.fsync(dir)
    os.close(dir)

def main():
    # accept command-line arguments
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config", default="config.yaml",
                      help="configuration file to be used", metavar="FILE")
    parser.add_option("-D", "--docroot", dest="docroot",
                      help="directory to be scanned", metavar="DIR")
    parser.add_option("-F", "--duflags", dest="duflags",
                      help="flags to be passed to du, replaces any in config")
    parser.add_option("-o", "--output", dest="output", metavar="FILE",
                      help="file to which index page will be written. "
                      "Use /dev/stdout to send to standard out.")
    parser.add_option("-t", "--template", dest="template",
                      help="Mako template to render", metavar="FILE")
    parser.add_option("--nonatomic", dest="nonatomic", action="store_true",
                      default=False, help="write the output to the path "
                      "given without creating a temporary file in between. "
                      "This is automatically set if the output appears "
                      "to be a character device, not a file.")
    (options, args) = parser.parse_args()
    
    # load config file
    try:
        config = yaml.load(file(options.config,'r'))
    except:
        config = None
    
    if not config or type(config) != dict:
        print >>sys.stderr, "Unable to load configuration '%s'." % options.config
        sys.exit(-1)
    
    # determine important variables based on an appropriate order of
    # precedence (command-line flags first, then the config file,
    # then built-in fallbacks)
    #
    # fallback value for nonatomic is used so that character devices
    # (e.g. /dev/stdout, /dev/null) are written to in the regular way
    docroot   = options.docroot   or config.get('docroot')
    duflags   = options.duflags   or config.get('duflags')   or "-h --max-depth=1"
    output    = options.output    or config.get('output')
    template  = options.template  or config.get("template")  or "index.mako"
    nonatomic = options.nonatomic or config.get("nonatomic") or \
        (os.path.exists(output) and not os.path.isfile(output))
    
    # sanity checks
    if not docroot:
        print >>sys.stderr, "docroot not specified."
        print >>sys.stderr, "Define it in the config file or pass -D on the command line."
        sys.exit(-1)
    elif not output:
        print >>sys.stderr, "output not specified."
        print >>sys.stderr, "Define it in the config file or pass -o on the command line."
    elif not config.get('directories'):
        print >>sys.stderr, "directories not specified."
        print >>sys.stderr, "Define it in the config file."
        sys.exit(-1)
    elif not os.path.isdir(docroot):
        print >>sys.stderr, "docroot '%s' not found or not a directory." % docroot
        sys.exit(-1)
    elif not os.path.exists(template) or os.path.isdir(template):
        print >>sys.stderr, "template '%s' not found or is a directory." % template
        sys.exit(-1)
    
    # Call du to compute size
    du = Popen(
        "/usr/bin/du %s %s | /usr/bin/sort -fk2" % (docroot, duflags),
        shell=True, stdout=PIPE, stderr=PIPE).communicate()
    
    # Check that du executed successfully
    # If there's anything on stderr, send it
    # out our own stderr and terminate.
    if len(du[1].strip()) > 0:
        sys.stderr.write(du[1])
        print >>sys.stderr, "du terminated unsuccessfully. Not generating index."
        sys.exit(-1)
    
    # first one should be total, grab its size and format
    du = du[0].splitlines() # we only care about stdout now
    total_size = reformat_size(du[0].split(None,2)[0])
    
    # the rest are the sizes we want
    directories = []
    for line in du[1:]:
        (size, dir) = line.split(None, 2)
        dir = os.path.basename(dir)
        info = {'dir':dir, 'size':reformat_size(size)}
        
        # use info from config.yaml, if found
        # otherwise, skip this directory
        if dir in config['directories']:
            info.update(config['directories'][dir])
        else:
            continue
        
        directories.append(info)
    
    # render the template to a string
    body = Template(filename=template).render(
        total_size=total_size,
        directories=directories,
        config=config,
        h=webhelpers.html.tags)
    
    # write the rendered output
    if nonatomic:
        print >>file(output,'w'), body
    else:
        atomic_write(output, body)


if __name__ == "__main__":
    main()
