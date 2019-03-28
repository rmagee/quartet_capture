# -*- coding: utf-8 -*-
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2018 SerialLab Corp.  All rights reserved.
from rest_framework.parsers import BaseParser

class RawParser(BaseParser):
    """
    Lets the inbound data stay in raw format since the rule engine is ultimately
    handling the true parsing of inbound raw XML and JSON.
    """
    media_type = '*/*'

    def parse(self, stream, media_type=None, parser_context=None):
        return stream.read()


