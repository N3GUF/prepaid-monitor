from datetime import datetime, timedelta
from sqlalchemy.sql import func
from xmlrpc.client import Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import (
    create_engine,
    ForeignKey,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    or_,
)

Base = declarative_base()


class Sch_Instance_State(Base):
    __tablename__ = "sch_instance_state"
    __table_args__ = {"schema": "ows", "quote": False}
    id = Column(Integer, primary_key=True)
    name = Column(String)
    started = Column(DateTime)
    closed = Column(DateTime)
    station = Column(String)
    status = Column(String)
    last_event = Column(String)

    def __repr__(self):
        return (
            "<Sch_Instance_State(name='%s', started='%s', closed='%s, station='%s', status='%s, last_event='%s')>"
            % (
                self.name,
                self.started,
                self.closed,
                self.station,
                self.status,
                self.last_event,
            )
        )


class Sch_Job_State(Base):
    __tablename__ = "sch_job_state"
    __table_args__ = {"schema": "ows", "quote": False}
    id = Column(Integer, primary_key=True)
    master_job = Column(Integer, nullable=True)
    name = Column(String)
    batch_role = Column(String)
    started = Column(DateTime)
    closed = Column(DateTime)
    status = Column(String)
    call_status = Column(String)
    next_start = Column(DateTime)
    sch_instance_state__id = Column(Integer, ForeignKey("Sch_Instance_State.id"))

    def __repr__(self):
        return (
            "<Sch_Job_State(name='%s', batch_role='%s', started='%s', closed='%s, status='%s', call_status='%s, next_start='%s')>"
            % (
                self.name,
                self.batch_role,
                self.started,
                self.closed,
                self.status,
                self.call_status,
                self.next_start,
            )
        )


class Process_Log(Base):
    __tablename__ = "process_log"
    __table_args__ = {"schema": "ows", "quote": False}
    id = Column(Integer, primary_key=True)
    process_name = Column(String)
    started = Column(DateTime)
    finished = Column(DateTime)
    last_updated = Column(DateTime)
    status = Column(String)

    def __repr__(self):
        return (
            "<SchedulerInstance(process_name='%s', started='%s', finished='%s, status='%s')>"
            % (
                self.process_name,
                self.started,
                self.finished,
                self.status,
            )
        )


class Doc(Base):
    __tablename__ = "Doc"
    __table_args__ = {"schema": "ows", "quote": False}
    id = Column("id", Integer, primary_key=True)
    trans_amount = Column("trans_amount", Float)


class File_Info(Base):
    __tablename__ = "File_Info"
    __table_args__ = {"schema": "ows", "quote": False}
    id = Column(Integer, primary_key=True)
    file_id = Column(String)
    file_name = Column(String)
    creation_date = Column(DateTime)


class File_Record(Base):
    __tablename__ = "File_Record"
    __table_args__ = {"schema": "ows", "quote": False}
    id = Column(Integer, primary_key=True)
    file_info__oid = Column(Integer, ForeignKey("File_Info.id"))
    ref_record = Column(Integer, ForeignKey("Doc.id"))
    record_type = Column(String)


class DB:
    def __init__(
        self, dsn: String, user: String, password: String, echo: Boolean = False
    ):
        self.__dsn = dsn
        self.__user = user
        self.__password = password
        self.__echo = echo
        self.__connString = "oracle://{}:{}@{}".format(
            self.__user, self.__password, self.__dsn
        )
        self.engine = create_engine(self.__connString, echo=self.__echo)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def get_sch_instance_states(self, sch_list):
        result = []

        try:
            result = (
                self.session.query(Sch_Instance_State)
                .filter(Sch_Instance_State.name.in_(sch_list))
                .all()
            )

        except Exception as e:
            return result, e
        else:
            return result, None

    def get_invalid_jobs(self, sch_list):
        result = []

        try:
            result = (
                self.session.query(Sch_Job_State, Sch_Instance_State)
                .join(
                    Sch_Instance_State,
                    Sch_Job_State.sch_instance_state__id == Sch_Instance_State.id,
                )
                .filter(
                    Sch_Instance_State.name.in_(sch_list),
                    Sch_Job_State.master_job == None,
                    Sch_Job_State.status == "I",
                )
                .order_by(Sch_Job_State.name)
                .all()
            )

        except Exception as e:
            return result, e
        else:
            return result, None

    def get_sch_job_states(self, sch_list):
        result = []

        try:
            result = (
                self.session.query(Sch_Job_State, Sch_Instance_State)
                .join(
                    Sch_Instance_State,
                    Sch_Job_State.sch_instance_state__id == Sch_Instance_State.id,
                )
                .filter(
                    Sch_Instance_State.name.in_(sch_list),
                    Sch_Job_State.master_job == None,
                    ~Sch_Job_State.status.in_(["C", "N"]),
                )
                .order_by(Sch_Job_State.name)
                .all()
            )

        except Exception as e:
            return result, e
        else:
            return result, None

    def get_sch_job_processes(self):
        result = []

        try:
            result = (
                self.session.query(
                    func.substr(Process_Log.process_name, 6).label("process_name"),
                    Process_Log.started,
                    Process_Log.finished,
                    Process_Log.status,
                )
                .filter(
                    Process_Log.process_name.like("Job:%"),
                    Process_Log.last_updated > datetime.now() + timedelta(days=-3),
                )
                .order_by(Process_Log.started.desc())
            )

        except Exception as e:
            return result, e
        else:
            return result, None

    def get_file_infos(self, prevMinutes: int):
        result = []

        try:
            result = (
                self.session.query(
                    File_Info.creation_date.label("creation_date"),
                    File_Info.file_id.label("file_id"),
                    File_Info.file_name.label("file_name"),
                    func.count(File_Record.id).label("transactions"),
                    func.sum(Doc.trans_amount).label("amount"),
                )
                .select_from(Doc)
                .join(File_Record, Doc.id == File_Record.ref_record)
                .join(File_Info, File_Record.file_info__oid == File_Info.id)
                .filter(
                    File_Info.creation_date
                    > datetime.now() - timedelta(minutes=prevMinutes),
                    File_Record.record_type != "P",
                    File_Record is not None,
                    or_(
                        File_Info.file_name.like("%DIRECTDEP%"),
                        File_Info.file_name.like("%PRENOTE%"),
                    ),
                )
                .group_by(
                    File_Info.creation_date,
                    File_Info.file_id,
                    File_Info.file_name,
                )
                .order_by(File_Info.file_id.desc())
                .all()
            )

        except Exception as e:
            return result, e
        else:
            return result, None
