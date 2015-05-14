# Copyright (C) 2010-2015 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

import os
from subprocess import Popen

from lib.api.process import Process
from lib.common.exceptions import CuckooPackageError

class Package(object):
    """Base abstract analysis package."""
    PATHS = []

    def __init__(self, options={}):
        """@param options: options dict."""
        self.options = options
        self.pids = []

    def set_pids(self, pids):
        """Update list of monitored PIDs in the package context.
        @param pids: list of pids.
        """
        self.pids = pids

    def start(self):
        """Run analysis package.
        @raise NotImplementedError: this method is abstract.
        """
        raise NotImplementedError

    def check(self):
        """Check."""
        return True

    def _enum_paths(self):
        """Enumerate available paths."""
        for path in self.PATHS:
            basedir = path[0]
            if basedir == "SystemRoot":
                yield os.path.join(os.getenv("SystemRoot"), *path[1:])
            elif basedir == "ProgramFiles":
                yield os.path.join(os.getenv("ProgramFiles"), *path[1:])
                if os.getenv("ProgramFiles(x86)"):
                    yield os.path.join(os.getenv("ProgramFiles(x86)"),
                                       *path[1:])
            elif basedir == "HomeDrive":
                # os.path.join() does not work well when giving just C:
                # instead of C:\\, so we manually add the backslash.
                homedrive = os.getenv("HomeDrive") + "\\"
                yield os.path.join(homedrive, *path[1:])
            else:
                yield os.path.join(*path)

    def get_path(self, application):
        """Search for an application in all available paths.
        @param applicaiton: application executable name
        @return: executable path
        """
        for path in self._enum_paths():
            if os.path.exists(path):
                return path

        raise CuckooPackageError("Unable to find any %s executable." %
                                 application)

    def execute(self, path, args):
        """Starts an executable for analysis.
        @param path: executable path
        @param args: executable arguments
        @return: process pid
        """
        dll = self.options.get("dll")
        free = self.options.get("free")
        tool = self.options.get("tool")

        suspended = True
        if free:
            suspended = False

        p = Process()
        if not p.execute(path=path, args=args, suspended=suspended):
            raise CuckooPackageError("Unable to execute the initial process, "
                                     "analysis aborted.")

        if tool:
            tool_path = os.path.join(os.path.join(os.getenv("Temp"), "tool"), "tool")
            tool_args = self.options.get('tool_options') 
            cmd_list = [tool_path, tool_args, path, args]
            cwd = os.getcwd()
            os.chdir(os.getenv("Temp"))
            with open("out.log", 'w') as log:
                log.write(str(cmd_list))
                log.write("Test")
                log.write(cwd)
                log.write(os.getcwd())
            # 0x08000000 = CREATE_NO_WINDOW
            # Either set creation flag to CREATE_NO_WINDOW
            # or disable the human auxiliary module
            # because the module will interfere with the running tool
            creation_flag = 0x08000000
            with open('tool_output.log', 'w') as output_file:
                self.tool_process = Popen(cmd_list,
                                          stdout=output_file,
                                          stderr=output_file,
                                          creationflags=creation_flag,
                                          shell=False)
                self.tool_process.communicate()
            if self.tool_process < 0:
                raise CuckooPackageError("Unable to execute initial process, analysis aborted")

        if free:
            suspended = False

        p = Process()
        if not p.execute(path=path, args=args, suspended=suspended):
            raise CuckooPackageError("Unable to execute the initial process, "
                                     "analysis aborted.")

        if not free and suspended:
            p.inject(dll)
            p.resume()
            p.wait()
            p.close()
        
        return p.pid

    def package_files(self):
        """A list of files to upload to host.
        The list should be a list of tuples (<path on guest>, <name of file in package_files folder>).
        (package_files is a folder that will be created in analysis folder). 
        """
        return None
    
    def finish(self):
        """Finish run.
        If specified to do so, this method dumps the memory of
        all running processes.
        """
        if self.options.get("procmemdump"):
            for pid in self.pids:
                p = Process(pid=pid)
                p.dump_memory()
        
        return True

class Auxiliary(object):
    def __init__(self, options={}):
        self.options = options
