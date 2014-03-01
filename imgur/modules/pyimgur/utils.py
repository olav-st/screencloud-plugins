# This file is part of PyImgur.

# PyImgur is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# PyImgur is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with PyImgur.  If not, see <http://www.gnu.org/licenses/>.

"""Utility functionality for PyImgur. Not intended for end-user usage"""


import sys


class Disable_stdout():
    def __enter__(self):
        self.original_stdout = sys.stdout  # keep a reference to STDOUT
        sys.stdout = NullDevice()  # redirect the real STDOUT

    def __exit__(self):
        sys.stdout = self.original_stdout


class NullDevice():
    def write(self, s):
        pass
