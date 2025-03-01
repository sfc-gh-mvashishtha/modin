# Licensed to Modin Development Team under one or more contributor license agreements.
# See the NOTICE file distributed with this work for additional information regarding
# copyright ownership.  The Modin Development Team licenses this file to you under the
# Apache License, Version 2.0 (the "License"); you may not use this file except in
# compliance with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from types import ModuleType
from typing import Any, Union

import modin.pandas as pd
from collections import defaultdict


def register_dataframe_extension(engine, storage_format, dataframe_class):
    pd.dataframe._DATAFRAME_EXTENSIONS_[(engine, storage_format)] = dataframe_class


def register_series_extension(engine, storage_format, series_class):
    pd.series._SERIES_EXTENSIONS_[(engine, storage_format)] = series_class


from modin.config import Backend, get_execution, StorageFormat, Engine


_PD_OVERRIDES = defaultdict()


def register_pd_accessor(name, engine, storage_format):

    def wrapper(value):
        # if name == "concat":
        #     breakpoint()
        _PD_OVERRIDES[(engine, storage_format, name)] = value
        return value

    return wrapper


import sys
from types import ModuleType
import itertools


class VerboseModule(ModuleType):

    def __getattribute__(self, name):
        if (Engine.get(), StorageFormat.get(), name) in _PD_OVERRIDES:
            return _PD_OVERRIDES[(Engine.get(), StorageFormat.get(), name)]
        return super().__getattribute__(name)

    def __dir__(self):
        result = set(
            itertools.chain(
                super().__dir__(),
                (
                    name
                    for engine, storage_format, name in _PD_OVERRIDES
                    if engine == Engine.get() and storage_format == StorageFormat.get()
                ),
            )
        )
        return result


sys.modules[pd.__name__].__class__ = VerboseModule
