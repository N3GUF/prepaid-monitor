import datetime


class Query:
    @staticmethod
    def SchInstanceStateQuery(instances: tuple) -> str:
        return """ select name
                        , started
                        , closed
                        , station
                        , status
                        , last_event
                     from OWS.sch_instance_state
                    where name in {}
	        	""".format(
            instances
        )

    @staticmethod
    def InvalidJobsQuery(instances: tuple) -> str:
        return """ select s.name
	             		, s.batch_role
	             		, s.started
	             		, s.closed
	             		, s.status
	             		, s.call_status
	             		, s.ext_next_start
						, i.name
						, i.station
	          		 from OWS.sch_job_state s
	          		 join OWS.sch_instance_state i on s.sch_instance__id = i.id
	         		where i.name in {}
	           		  and s.master_job is null
	           		  and s.status = 'I'
	        	 order by s.name
	        	""".format(
            instances
        )

    @staticmethod
    def JobStatusQuery(instances: tuple) -> str:
        return """ select s.name
		         , s.batch_role
		         , s.started
		         , s.closed
		         , s.status
	             , s.call_status
	             , s.ext_next_start
				 , i.name
				 , i.station
		      from OWS.sch_job_state s
		      join OWS.sch_instance_state i on s.sch_instance__id = i.id
		     where i.name in {}
		       and s.master_job is null
		       and s.status not in ('C', 'N')
		    order by s.name
		    """.format(
            instances
        )

    @staticmethod
    def ProcessLogJobQuery(last_run: datetime.datetime | None) -> str:
        if last_run:
            return """ select substr(process_name, 6) as "process_name"
							, started
							, finished
							, status
						from OWS.process_log
						where process_name like 'Job:%'
						and finished >= to_date('{}', 'MM-DD-YYYY HH24:MI:SS')
					order by started desc
					""".format(
                last_run.strftime("%m-%d-%Y %H:%M:%S")
            )
        else:
            return """ select substr(process_name, 6) as "process_name"
							, started
							, finished
							, status
						from OWS.process_log
						where process_name like 'Job:%'
						and finished > sysdate -3
					order by started desc
					"""

    @staticmethod
    def FileInfoQuery(last_run: datetime.datetime) -> str:
        return """ select info.creation_date
	                , info.FILE_ID
					, info.FILE_NAME
					, count(rec.id)
					, sum(doc.trans_amount)
                 from ows.doc doc
				    , ows.file_record rec
					, ows.file_info info
		        where info.creation_date >= to_date('{}', 'MM-DD-YYYY HH24:MI:SS')
                  and (info.file_name like '%DIRECTDEP%'
				    or info.file_name like '%PRENOTE%')
                  and rec.FILE_INFO__OID = info.id
                  and doc.id = rec.REF_RECORD
                  and rec.record_type != 'P'
				  and rec.ref_record is not null
		     group by info.creation_date
				    , info.FILE_ID
				    , info.file_name
             order by info.FILE_ID desc
		       """.format(
            last_run.strftime("%m-%d-%Y %H:%M:%S")
        )

    @staticmethod
    def AchFileQuery(last_run: datetime.datetime) -> str:
        return """ select file_type
      				, status
      				, file_name
      				, file_rec_date
      				, round(total_debit_amt / 100, 2)
      				, round(total_credit_amt / 100, 2)
                    , source_corp_acnt
                    , imm_origin_name
   				 from sdbatch1.ach_file
  				where file_type = 'ACH'
    			  and file_rec_date >= to_date('{}', 'MM-DD-YYYY HH24:MI:SS')
                 		       """.format(
            last_run.strftime("%m-%d-%Y %H:%M:%S")
        )

    @staticmethod
    def DelayedEcbFileQuery(upper_limit_hours: float, lower_limit_hours: float) -> str:
        return f""" select file_type
      					, status
      					, file_name
      					, file_rec_date
      					, round(total_debit_amt / 100, 2)
      					, round(total_credit_amt / 100, 2)
                        , source_corp_acnt
                        , imm_origin_name
					 from sdbatch1.ach_file
					where file_type='ECB'
  					  and STATUS in ('0','200','301','100')
                      and file_rec_date < sysdate - numtodsinterval({upper_limit_hours}, 'hour')
                      and file_rec_date > sysdate - numtodsinterval({lower_limit_hours}, 'hour')
                      and imm_origin_name = 'EMPLOYBRIDGE'
                      and file_review_st <> 'RDYFORPRCS'
                union all
                select file_type
      					, status
      					, file_name
      					, file_rec_date
      					, round(total_debit_amt / 100, 2)
      					, round(total_credit_amt / 100, 2)
                        , source_corp_acnt
                        , imm_origin_name
					 from sdbatch1.ach_file
					where file_type='ECB'
  					  and STATUS in ('0','200','301','100')
                      and file_rec_date < sysdate - numtodsinterval({upper_limit_hours}, 'hour')
                      and file_rec_date > sysdate - numtodsinterval({lower_limit_hours}, 'hour')
                      and imm_origin_name <> 'EMPLOYBRIDGE'
                   order by file_rec_date, source_corp_acnt
           """
