from abc import ABC, abstractmethod
import cx_Oracle

# from datalayer.ppd_prd import *


class db(ABC):
    @abstractmethod
    def fetchRows(self, query: str) -> list:
        """Fetch Rows from a database"""


class way4Db(db):
    def __init__(self, logger, dsn, user, password):
        self.logger = logger
        self.dsn = dsn
        self.user = user
        self.password = password
        # self.dsn_tns = cx_Oracle.makedsn(
        #     host=host, port=port, service_name=service_name
        # )

    def fetchRows(self, query: str) -> list:
        """Query the database.

        Arguments:
            query:  DB query

        Returns:
            list:   List of rows
        """
        try:
            self.logger.debug("Fetching data from database.")
            self.logger.debug(f"query: {query}")

            with cx_Oracle.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
                encoding="UTF-8",
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchall()

        except Exception as e:
            self.logger.error("An has occured while fetching data.")

            for arg in e.args:
                self.logger.error(arg)

            return []

        return rows
