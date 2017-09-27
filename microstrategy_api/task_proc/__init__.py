from microstrategy_api.task_proc.attribute import Attribute
from microstrategy_api.task_proc.exceptions import MstrClientException
from microstrategy_api.task_proc.object_type import ObjectType, ObjectTypeIDDict, ObjectSubTypeIDDict, ObjectSubType
from microstrategy_api.task_proc.task_proc import TaskProc
from microstrategy_api.task_proc.report import Report
from microstrategy_api.task_proc.document import Document

"""
This API only supports xml format, as it relies on the format for parsing
the data into python data structures

Forked from https://github.com/infoscout/py-mstr

* Converted to support python 3
* Renamed from MstrClient to TaskProc
* Converted XML parsing from pyQuery to BeautifulSoup 4
* Greatly enhanced folder browsing
* Added document running ability

Original license:

The MIT License (MIT)

Copyright (c) 2014 InfoScout

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""






