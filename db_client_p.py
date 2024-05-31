import psycopg2
from psycopg2.extensions import connection, cursor
from psycopg2.extras import DictCursor, DictRow

from typing import Type


class DBPostgres:
    __instance = None

    # Singleton
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, dbname, user, password, host, port):
        self.__dbname = dbname
        self.__user = user
        self.__password = password
        self.__host = host
        self.__port = port

    def fetch_one(self, query: str, data: list | tuple | dict = None, factory: Type[list | dict] = None,
                  clean: bool = False):
        try:
            with self.__connect() as conn:
                with conn.cursor(cursor_factory=DictCursor if factory else factory) as cur:
                    self.__execute(cur, query, data)
                    return self.__fetch(cur, factory, clean)
        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def fetch_all(self, query: str, data: list | tuple | dict = None, factory: Type[list | dict] = None):
        try:
            with self.__connect() as conn:
                with conn.cursor(cursor_factory=DictCursor if factory else factory) as cur:
                    self.__execute(cur, query, data)
                    return [dict(i) for i in cur.fetchall()] if factory is dict else cur.fetchall()
        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def execute_query(self, query: str, data: list | tuple | dict = None, message: str = 'Ok'):
        try:
            with self.__connect() as conn:
                with conn.cursor() as cur:
                    self.__execute(cur, query, data)
                    print(message)
        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def __connect(self) -> connection:
        conn: connection = psycopg2.connect(
            dbname=self.__dbname,
            user=self.__user,
            password=self.__password,
            host=self.__host,
            port=self.__port
        )
        conn.autocommit = True

        return conn

    @staticmethod
    def __execute(cur: cursor, query: str, data: list | tuple | dict) -> None:
        """

        :param cur:
        :param query:
        :param data:
        :return:
        """
        if data:
            if isinstance(data, list):
                cur.executemany(query, data)
            else:
                cur.execute(query, data)

        else:
            cur.execute(query)

    @staticmethod
    def __fetch(cur: cursor, factory: Type[list | dict], clean: bool):
        """

        :param cur:
        :param factory:
        :param clean:
        :return:
        """
        record: DictRow = cur.fetchone()
        if record is None:
            return None
        if clean:
            if factory is dict:
                key, value = list(record.items())[0]
                return {key: value}

            return record[0]

        return dict(record) if factory is dict else record

    @staticmethod
    def __error(error) -> None:
        print(error)
