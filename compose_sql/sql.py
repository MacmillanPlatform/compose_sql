"""SQL composition module."""

# Copyright (C) 2016-2019 Daniele Varrazzo  <daniele.varrazzo@gmail.com>
# Copyright (C) 2019 Alieh Rymašeŭski  <alieh.rymasheuski@gmail.com>
#
# This file is a part of compose_sql.
#
# compose_sql is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# compose_sql is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with compose_sql.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ['Identifier', 'Placeholder', 'SQL']

import abc
import string


class _Composable(abc.ABC):
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._wrapped)

    @abc.abstractmethod
    def as_string(self):
        """Render self as a string value."""
        pass


class _Composed(_Composable):
    """A sequence of _Composable items."""

    def __init__(self, seq):
        wrapped = []
        for el in seq:
            if not isinstance(el, _Composable):
                raise TypeError('%s elements must be %s, got %r instead' %
                                (self.__class__.__name__, _Composable.__name__, el))
            wrapped.append(el)

        super().__init__(wrapped)

    def as_string(self):
        return ''.join(el.as_string() for el in self._wrapped)

    def __iter__(self):
        return iter(self._wrapped)


class SQL(_Composable):
    """A string-like SQL statement implementing join() and format() methods.

    Example:
        >>> stmt = sql.SQL('UPDATE {table} SET {column} = {placeholder} '
        ...                'WHERE {id} = :id')
        >>> print(stmt.format(table=sql.Identifier('namespace', 'tbl'),
        ...                   column=sql.Identifier('foo'),
        ...                   placeholder=sql.Placeholder('bar'),
        ...                   id=sql.Identifier('id')).as_string()
        UPDATE "namespace"."tbl" SET "foo" = :bar WHERE "id" = :id
    """

    def __init__(self, string):
        if not isinstance(string, str):
            raise TypeError('SQL parameter must be string')
        super().__init__(string)

    def as_string(self):
        return self._wrapped

    def format(self, **kwargs):
        """Render _Composable objects into a template.

        Note: only keyword parameters are supported.
        """
        result = []
        for literal_text, field_name, format_spec, conversion in string.Formatter().parse(self._wrapped):
            if format_spec:
                raise ValueError('No format specification is supported by SQL')
            if conversion:
                raise ValueError('No format conversion is supported by SQL')
            if literal_text:
                result.append(SQL(literal_text))

            if field_name is None:
                continue

            result.append(kwargs[field_name])

        return _Composed(result)

    def join(self, seq):
        """Get a _Composed with a sequence of _Composable joined through self.

        Similar to str.join() method.

        Example:
            >>> fields = ['id', 'name', 'age']
            >>> stmt = sql.SQL(', ').join(
            ...     sql.SQL('{f}={p}').format(f=f, p=p)
            ...     for f, p in [(sql.Identifier(i), sql.Placeholder(i)) for i in fields])
            >>> print(stmt.as_string())
            "id"=:id, "name"=:name, "age"=:age
        """
        result = []
        it = iter(seq)
        try:
            result.append(next(it))
        except StopIteration:
            pass
        else:
            for i in it:
                result.append(self)
                result.append(i)
        return _Composed(result)


class Identifier(_Composable):
    """An atomic or dot-separated SQL identifier."""

    def __init__(self, *strings):
        if not strings:
            raise TypeError('Identifier cannot be empty')

        for s in strings:
            if not isinstance(s, str):
                raise TypeError('SQL identifier parts must be strings')

        super().__init__(strings)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(repr(s) for s in self._wrapped))

    def as_string(self):
        return '.'.join(_quote(s) for s in self._wrapped)


class Placeholder(_Composable):
    """A placeholder for query parameters.

    Note: only "named" paramstyle defined by PEP249 is supported,
    therefore only valid Python identifiers are allowed as placeholders.
    """

    def __init__(self, name):
        if not name.isidentifier():
            raise ValueError('Only valid Python identifiers are allowed, got %r' % name)

        super().__init__(name)

    def as_string(self):
        return ":%s" % self._wrapped


def _quote(value):
    def duplicate_quote(value, quote):
        for char in value:
            if char == quote:
                yield char
            yield char

    return '{quote}{value}{quote}'.format(quote='"', value=''.join(duplicate_quote(value, '"')))
