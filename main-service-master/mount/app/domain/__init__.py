from abc import ABC, abstractmethod


class DBQueryExecutor(ABC):
    @abstractmethod
    async def exec_write(self, query, *args):
        """
        Executes an write query
        """

    @abstractmethod
    async def exec_read(self, query, *args, only_one=False):
        """
        Execute a read query
        """


class BaseRepo:

    async def search(self, only_one=False, **kwargs):
        sql = self._base_read()
        where = []
        args = []

        for (k, v) in kwargs.items():
            if v is not None:
                args.append(v)
                position = len(args)
                where.append(f"{k} = ${position}")
    
        if where:
            sql = "{} WHERE {}".format(sql, ' AND '.join(where))

        recs = await self.db.exec_read(sql, *args)
        if recs and only_one:
            return recs[0]
            
        return recs       
    

    async def bulk_get_ints(self, field, value_list):
        values = ','.join(map(str, value_list))
        sql = self._base_read() + f""" WHERE {field} IN ({values})"""
        recs = await self.db.exec_read(sql)

        return recs


    @abstractmethod
    def _base_read(self):
        raise NotImplementedError("Please Implement this method")
