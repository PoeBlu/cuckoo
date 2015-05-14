# Copyright (C) 2010-2014 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

import os

from lib.cuckoo.common.abstracts import Processing


class Tool(Processing):
    """Process standard output the tool produced."""

    def run(self):
        """Run analysis.
        @return: list of tool output files with related information.
        """
        self.key = "tool"
        tool_output = []
        tool_output_dir = os.path.join(self.analysis_path, "tool_output")

        for dir_name, dir_names, file_names in os.walk(tool_output_dir):
            for file_name in file_names:
                value = {'name': file_name, 'contents':  ''}
                if file_name == "tool_output.log":
                    with open(os.path.join(tool_output_dir, file_name), "r") as logfile:
                        value = {'name': file_name, 'contents': logfile.read()}
                tool_output.append(value)

        return tool_output
