
class Query:

    def __init__(self, model_class):
        self.__model_class = model_class
        self.__where = []
        self.__params = []
        self.__order = []
        self.__limit = None
        self.__offset = None
        self.__model_columns = set(self.__model_class.get_columns())

    
    @staticmethod
    def add_value(value):
        from liteorm import Model
        return value.get_pk_val() if isinstance(value, Model) else value


    def where(self, column, value):
        assert column in self.__model_columns
        self.__where.append(column + ' = ?')
        self.__params.append(self.add_value(value))
        return self


    def where_not(self, column, value):
        assert column in self.__model_columns
        self.__where.append(column + ' != ?')
        self.__params.append(self.add_value(value))
        return self


    def where_null(self, column):
        assert column in self.__model_columns
        self.__where.append(column + ' is null')
        return self


    def where_not_null(self, column):
        assert column in self.__model_columns
        self.__where.append(column + ' is not null')
        return self


    def where_lt(self, column, value):
        assert column in self.__model_columns
        self.__where.append(column + ' < ?')
        self.__params.append(self.add_value(value))
        return self


    def where_gt(self, column, value):
        assert column in self.__model_columns
        self.__where.append(column + ' > ?')
        self.__params.append(self.add_value(value))
        return self


    def where_leq(self, column, value):
        assert column in self.__model_columns
        self.__where.append(column + ' <= ?')
        self.__params.append(self.add_value(value))
        return self


    def where_geq(self, column, value):
        assert column in self.__model_columns
        self.__where.append(column + ' >= ?')
        self.__params.append(self.add_value(value))
        return self


    def where_between(self, column, low, high):
        assert column in self.__model_columns
        self.__where.append('(' + column + ' BETWEEN ? AND ?)')
        self.__params.append(self.add_value(low))
        self.__params.append(self.add_value(high))
        return self


    def where_val_between(self, value, col_low, col_high):
        assert col_low in self.__model_columns
        assert col_high in self.__model_columns
        self.__where.append(f'(? BETWEEN {col_low} AND {col_high})')
        self.__params.append(self.add_value(value))
        return self


    def where_in(self, column, values):
        assert column in self.__model_columns
        if len(values) == 0: return self
        self.__where.append(column + ' IN (' + ', '.join(['?']*len(values)) + ')')
        self.__params.extend(map(self.add_value, values))
        return self


    def where_not_in(self, column, values):
        assert column in self.__model_columns
        if len(values) == 0: return self
        self.__where.append(column + ' NOT IN (' + ', '.join(['?']*len(values)) + ')')
        self.__params.extend(map(self.add_value, values))
        return self


    def __where_in_generic(self, column, subqueries, subquery_field, join_subqueries, negative):
        assert column in self.__model_columns
        assert isinstance(subqueries, (list, tuple))
        assert len(subqueries) >= 1
        sq0 = subqueries[0]
        if len(subqueries) > 1:
            for subquery in subqueries:
                assert isinstance(subquery, Query)
                assert subquery.__model_class == sq0.__model_class
        assert subquery_field is None or subquery_field in sq0.__model_columns
        if subquery_field is None:
            subquery_field = sq0.__model_class.primary_key
        negative_sql = 'NOT' if negative else ''
        sub_sql = f' {join_subqueries} '.join([subquery.generate_sql([subquery_field]) for subquery in subqueries])
        self.__where.append(f'{column} {negative_sql} IN ({sub_sql})')
        for subquery in subqueries:
            self.__params.extend(subquery.__params)
        return self


    def where_in_query(self, column, subquery, subquery_field=None):
        return self.__where_in_generic(column, [subquery], subquery_field, '', False)


    def where_not_in_query(self, column, subquery, subquery_field=None):
        return self.__where_in_generic(column, [subquery], subquery_field, '', True)


    def where_in_union(self, column, subquery, subquery_field=None):
        return self.__where_in_generic(column, [subquery], subquery_field, 'UNION', False)


    def where_not_in_union(self, column, subquery, subquery_field=None):
        return self.__where_in_generic(column, [subquery], subquery_field, 'UNION', True)


    def where_in_union_all(self, column, subqueries, subquery_field=None):
        return self.__where_in_generic(column, subqueries, subquery_field, 'UNION ALL', False)


    def where_not_in_union_all(self, column, subqueries, subquery_field=None):
        return self.__where_in_generic(column, subqueries, subquery_field, 'UNION ALL', True)


    def where_in_intersect(self, column, subqueries, subquery_field=None):
        return self.__where_in_generic(column, subqueries, subquery_field, 'INTERSECT', False)


    def where_not_in_intersect(self, column, subqueries, subquery_field=None):
        return self.__where_in_generic(column, subqueries, subquery_field, 'INTERSECT', True)


    def limit(self, value):
        self.__limit = None if value is None else int(value)
        return self


    def offset(self, value):
        self.__offset = None if value is None else int(value)
        return self


    def limits(self, offset, limit):
        self.__limit = None if offset is None else int(limit)
        self.__offset = None if limit is None else int(offset)
        return self


    def order(self, column, direction='ASC'):
        assert column in self.__model_columns
        assert direction.upper() in {'ASC', 'DESC'}
        self.__order.append(column + ' ' + direction)
        return self


    def generate_sql(self, columns):
        assert all(map(lambda x: x in self.__model_columns, columns))
        columns_list = columns
        columns = ', '.join(columns_list)
        sql = f'SELECT {columns} FROM {self.__model_class.table_name}'
        if len(self.__where):
            sql += ' WHERE ' + ' AND '.join(self.__where)
        if len(self.__order):
            sql += ' ORDER BY ' + ', '.join(self.__order)
        if self.__limit is not None:
            sql += f' LIMIT {self.__limit} '
        if self.__offset is not None:
            sql += f' OFFSET {self.__offset} '
        return sql


    def delete(self):
        sql = self.generate_sql([self.__model_class.primary_key])
        cursor = self.__model_class.database.get_cursor()
        cursor.execute(f'DELETE FROM {self.__model_class.table_name} WHERE {self.__model_class.primary_key} IN ({sql})', self.__params)
        self.__model_class.invalidate_model_cache()
        return cursor.rowcount


    def get(self):
        cursor = self.__model_class.database.get_cursor()
        cursor.execute(self.generate_sql(self.__model_class.get_columns()), self.__params)
        return (self.__model_class.add_cache(row)().fill(row) for row in cursor)


    def get_one(self):
        self.__limit = 1
        for val in self.get():
            return val
        return None

    