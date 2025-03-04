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
import modin.pandas.base as base

from collections import defaultdict


def _set_attribute_on_obj(
    name: str,
    extensions_dict: dict,
    obj: Union[pd.DataFrame, pd.Series, ModuleType],
    engine,
    storage_format,
):
    """
    Create a new or override existing attribute on obj.


    Returns
    -------
    decorator
        Returns the decorator function.
    """

    def decorator(new_attr: Any):
        """
        The decorator for a function or class to be assigned to name

        Parameters
        ----------
        new_attr : Any
            The new attribute to assign to name.

        Returns
        -------
        new_attr
            Unmodified new_attr is return from the decorator.
        """
        extensions_dict[(storage_format, engine)][name] = new_attr
        return new_attr

    return decorator


_PD_OVERRIDES = defaultdict(dict)

from modin.config import StorageFormat, Engine


def register_base_accessor(name: str, engine, storage_format):
    return _set_attribute_on_obj(
        name, base._BASE_EXTENSIONS, object(), engine, storage_format
    )


def register_dataframe_accessor(name: str, engine, storage_format):
    """
    Registers a dataframe attribute with the name provided.

    This is a decorator that assigns a new attribute to DataFrame. It can be used
    with the following syntax:

    ```
    @register_dataframe_accessor("new_method")
    def my_new_dataframe_method(*args, **kwargs):
        # logic goes here
        return
    ```

    The new attribute can then be accessed with the name provided:

    ```
    df.new_method(*my_args, **my_kwargs)
    ```

    Parameters
    ----------
    name : str
        The name of the attribute to assign to DataFrame.

    Returns
    -------
    decorator
        Returns the decorator function.
    """
    return _set_attribute_on_obj(
        name, pd.dataframe._DATAFRAME_EXTENSIONS_, pd.DataFrame, engine, storage_format
    )


def register_series_accessor(name: str, engine: str, storage_format: str):
    """
    Registers a series attribute with the name provided.

    This is a decorator that assigns a new attribute to Series. It can be used
    with the following syntax:

    ```
    @register_series_accessor("new_method")
    def my_new_series_method(*args, **kwargs):
        # logic goes here
        return
    ```

    The new attribute can then be accessed with the name provided:

    ```
    s.new_method(*my_args, **my_kwargs)
    ```

    Parameters
    ----------
    name : str
        The name of the attribute to assign to Series.

    Returns
    -------
    decorator
        Returns the decorator function.
    """
    # DO NOT MERGE FIXME
    return _set_attribute_on_obj(
        name, pd.series._SERIES_EXTENSIONS_, pd.Series, engine, storage_format
    )


def register_pd_accessor(name, engine, storage_format):

    def wrapper(value):
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
