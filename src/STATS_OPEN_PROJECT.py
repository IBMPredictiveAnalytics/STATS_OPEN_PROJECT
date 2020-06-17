#/***********************************************************************
# * Licensed Materials - Property of IBM 
# *
# * IBM SPSS Products: Statistics Common
# *
# * (C) Copyright IBM Corp. 2014-2020
# *
# * US Government Users Restricted Rights - Use, duplication or disclosure
# * restricted by GSA ADP Schedule Contract with IBM Corp. 
# ************************************************************************/



import os.path, random, re, os, codecs
import spss, spssaux, SpssClient
from extension import Template, Syntax, processcmd

"""STATS OPEN PROJECT extension command"""

__author__ =  'IBM SPSS, JKP'
__version__=  '1.0.1'

# history
# 17-feb-2014 Original version

helptext = """STATS OPEN PROJECT FILE="filespec" PASSWORD="password"
    STARTUP = ASIS or SET or DELETE

FILE is the name of a project file to open.  A Project file is a plain text
file with the following format.

[RUN]
syntax commands in interactive format
[OPEN]
list of data (.sav), syntax (.sps), and output (.spv) files to open
[PROJECT]
list of other project files to be opened

Sections may appear in any order and may be repeated.
Files listed in a PROJECT section must follow this same format.
If you have a standard utility library and various working projects,
it may be convenient to reference a standard project file first and then
make working project specifications.

File handles defined in executed RUN sections or before this command can
be used in file listings.

Lines starting with a semicolon are comments and are echoed to the Viewer.

Optionally a single password, encrypted or in plain text can be
specified to be applied to files listed in OPEN sections if your version
of Statistics supports this.  The password must be enclosed in quotes.

STARTUP specifies what happens in future sessions.  
If STARTUP = SET, future sessions will open this project automatically
If STARTUP = DELETE, future sessions will not open this project.
If STARTUP = ASIS, future sessions will operate the same as the current
session.  By default, the project is not set as default.

Note: SET creates a script that is automatically executed when
Statistics starts.  If there is an existing startup script, it
is replaced if it appears to have been created by this command.  
STARTUP=DELETE erases the startup script if it appears to have
been created with this command.

If you want to combine automatic project opening with other scripted
activities at startup, you can add the startup code to your
existing script.  This portion of the script would look like this.
import SpssClient
SpssClient.StartClient()
SpssClient.RunSyntax(r'''STATS OPEN PROJECT FILE="project filename".''')
SpssClient.StopClient()

/HELP displays this help and does nothing else.
"""

def doproj(projfile, password=None, startup="asis"):
    """Execute a project file
    
    projfile is the name of the project file
    password is an optional password"""
    # debugging
        # makes debug apply only to the current thread
    #try:
        #import wingdbstub
        #if wingdbstub.debugger != None:
            #import time
            #wingdbstub.debugger.StopDebug()
            #time.sleep(1)
            #wingdbstub.debugger.StartDebug()
        #import thread
        #wingdbstub.debugger.SetDebugThreads({thread.get_ident(): 1}, default_policy=0)
        ## for V19 use
        ###    ###SpssClient._heartBeat(False)
    #except:
        #pass    
    fh = FileHandles()
    projfile = fh.resolve(projfile)
    setstartup(projfile, startup, password)
    print("**** Opening project %s" % projfile)
    state = None
    lines = []
    ###with open(projfile) as f:
    with codecs.open(projfile, encoding="utf_8_sig") as f:
        for line in f.readlines():
            line = line.rstrip()  # strip newline
            # lines starting with "<whitespace>;" are comments and are just printed
            if line.lstrip().startswith(";"):
                print(line)
                continue
            # if section header, process previous section; otherwise accumulate lines
            if line in list(dispatch.keys()):
                if state == "[PROJECT]":
                    for item in lines:
                        doproj(item, password)  # Will never set child as startup script
                else:
                    dispatch[state](lines, password)
                lines = []
                state = line
            else:
                lines.append(line)
            
    # on end of file
    if state == "[PROJECT]":
        for item in lines:
            doproj(item, password)
    else:
        dispatch[state](lines, password)    
        
def donothing(lines, password):
    """No-op"""
    
    pass
    
def dorun(lines, password):
    """Execute stacked commands, if any"""
    
    if lines:
        spss.Submit(lines)

def doopen(lines, password):
    """Open each listed file according to type"""
    
    if lines:
        fh = FileHandles()
        try:
            SpssClient.StartClient()
            uialerts = SpssClient.GetUIAlerts()
            SpssClient.SetUIAlerts(False)
            for line in lines:
                line = fh.resolve(line.lstrip())   # file handles are supported for all file types
                ext = os.path.splitext(line)[-1].lower()
                if ext == ".sav":
                    cmd = """GET FILE="%s" """ % line
                    if password is not None:
                        cmd = cmd + """PASSWORD="%s". """ % password
                    spss.Submit(cmd)
                    # assign a random dataset name
                    spss.Submit("""DATASET NAME %s.""" % _("""Dataset""") + str(random.randint(1000, 100000)))
                    print(_("""Opened file %s""") % line)
                elif ext == ".sps":
                    try:
                        if password is None:
                            SpssClient.OpenSyntaxDoc(line)
                        else:
                            SpssClient.OpenSyntaxDoc(line, password)
                        print(_("""Opened file %s""") % line)
                    except:
                        print(_("""File: %s already open and has changed or could not be opened.  Not opened""") % line)
                elif ext == ".spv":
                    try:
                        if password is None:
                            SpssClient.OpenOutputDoc(line)
                        else:
                            SpssClient.OpenOutputDoc(line, password)
                        print(_("""Opened file %s""") % line)
                    except:
                        print(_("""File: %s already open and has changed or could not be opened.  Not opened""") % line)                
                else:
                    raise ValueError(_("""File to open has unknown extension: %s""") % line)
        except:
            print(_("""File open failure: %s""") % line)
        finally:
            SpssClient.SetUIAlerts(uialerts)
            SpssClient.StopClient()

# mapping of section names to functions  
dispatch = {
    None: donothing,
    "[PROJECT]": doproj,
    "[RUN]" : dorun,
    "[OPEN]" : doopen
}

scripttag = "Created by STATS OPEN PROJECT"
def setstartup(projfile, action, password):
    """Set project as startup, delete startup, or do nothing"""
    
    if action == "asis":
        return
    # This location might not be writeable
    installscript = spssaux.getSpssInstallDir() + os.sep + "scripts" + os.sep + "StartClient_.py"
    if not oktomodify(installscript):
        raise ValueError(_("""Cannot set new script or delete startup script, 
because existing script was not created by STATS OPEN PROJECT"""))
    if action == "delete":
        try:
            if os.path.exists(installscript):
                os.remove(installscript)
                print(_("""Startup script %s removed""") % installscript)
        except:
            raise ValueError(_("""Unable to remove startup script %s""") % installscript)
    else: # create install script
        if password:
            pwdsyn = """ PASSWORD="%" """ % password
        else:
            pwdsyn = ""
        # Write the script in utf-8 in case file name contains extended characters (also includes BOM)
        # First line is STATS OPEN PROJECT signature to protect other startup scripts
        
        content = """# %s
# -*- coding: utf_8_sig -*-
import SpssClient
SpssClient.StartClient()
try:
    SpssClient.RunSyntax(r'''STATS OPEN PROJECT FILE="%s" %s.''')
finally:
    SpssClient.StopClient()
"""  % (scripttag, projfile, pwdsyn)
        try:
            with codecs.EncodedFile(codecs.open(installscript, "wb"), 
                    "unicode_internal", "utf_8_sig") as f:
                f.write(content)
            print("Startup script written to %s" % installscript)
        except:
            raise ValueError(_("""Unable to write startup script to %s""") % installscript)

def oktomodify(installscript):
    """Return True if no script or okay to delete or replace
    
    installscript is the path"""
    
    if os.path.exists(installscript):
        if scripttag in open(installscript).readline():
            return True
        else:
            return False
    else:
        return True
    
    
class FileHandles(object):
    """manage and replace file handles in filespecs.
    
    For versions prior to 18, it will always be as if there are no handles defined as the necessary
    api is new in that version, but path separators will still be rationalized.
    """
    
    def __init__(self):
        """Get currently defined handles"""
        
        # If the api is available, make dictionary with handles in lower case and paths in canonical form, i.e.,
        # with the os-specific separator and no trailing separator
        # path separators are forced to the os setting
        if os.path.sep == "\\":
            ps = r"\\"
        else:
            ps = "/"
        try:
            self.fhdict = dict([(h.lower(), (re.sub(r"[\\/]", ps, spec.rstrip("\\/")), encoding))\
                for h, spec, encoding in spss.GetFileHandles()])
        except:
            self.fhdict = {}  # the api will fail prior to v 18
    
    def resolve(self, filespec):
        """Return filespec with file handle, if any, resolved to a regular filespec
        
        filespec is a file specification that may or may not start with a handle.
        The returned value will have os-specific path separators whether or not it
        contains a handle"""
        
        parts = re.split(r"[\\/]", filespec)
        # try to substitute the first part as if it is a handle
        parts[0] = self.fhdict.get(parts[0].lower(), (parts[0],))[0]
        return os.path.sep.join(parts)
    
    def getdef(self, handle):
        """Return duple of handle definition and encoding or None duple if not a handle
        
        handle is a possible file handle
        The return is (handle definition, encoding) or a None duple if this is not a known handle"""
        
        return self.fhdict.get(handle.lower(), (None, None))
    
    def createHandle(self, handle, spec, encoding=None):
        """Create a file handle and update the handle list accordingly
        
        handle is the name of the handle
        spec is the location specification, i.e., the /NAME value
        encoding optionally specifies the encoding according to the valid values in the FILE HANDLE syntax."""
        
        spec = re.sub(r"[\\/]", re.escape(os.path.sep), spec)   # clean up path separator
        cmd = """FILE HANDLE %(handle)s /NAME="%(spec)s" """ % locals()
        # Note the use of double quotes around the encoding name as there are some encodings that
        # contain a single quote in the name
        if encoding:
            cmd += ' /ENCODING="' + encoding + '"'
        spss.Submit(cmd)
        self.fhdict[handle.lower()] = (spec, encoding)

def Run(args):
    """Execute the STATS OPEN PROJECT extension command"""

    args = args[list(args.keys())[0]]

    oobj = Syntax([
        Template("FILE", subc="",  ktype="literal", var="projfile"),
        Template("PASSWORD", subc="", ktype="literal", var="password"),
        Template("STARTUP", subc="", ktype="str", var="startup",
            vallist=["asis", "set", "delete"]),
        
        Template("HELP", subc="", ktype="bool")])
    
    #enable localization
    global _
    try:
        _("---")
    except:
        def _(msg):
            return msg
    # A HELP subcommand overrides all else
    if "HELP" in args:
        #print helptext
        helper()
    else:
        processcmd(oobj, args, doproj)

def helper():
    """open html help in default browser window
    
    The location is computed from the current module name"""
    
    import webbrowser, os.path
    
    path = os.path.splitext(__file__)[0]
    helpspec = "file://" + path + os.path.sep + \
         "markdown.html"
    
    # webbrowser.open seems not to work well
    browser = webbrowser.get()
    if not browser.open_new(helpspec):
        print(("Help file not found:" + helpspec))
try:    #override
    from extension import helper
except:
    pass        