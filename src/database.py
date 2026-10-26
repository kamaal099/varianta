"""Small local DuckDB registry for analysis metadata."""
import json, os
import duckdb

DB_PATH=os.environ.get("EXPERIMENTIQ_DB","varianta.duckdb")
def init_db():
    con=duckdb.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS analyses (
      analysis_id BIGINT PRIMARY KEY DEFAULT nextval('analysis_seq'),
      experiment_name VARCHAR, data_source VARCHAR, created_at TIMESTAMP DEFAULT current_timestamp,
      decision VARCHAR, report_json JSON)""") if False else None
    con.execute("CREATE SEQUENCE IF NOT EXISTS analysis_seq START 1")
    con.execute("""CREATE TABLE IF NOT EXISTS analyses (
      analysis_id BIGINT DEFAULT nextval('analysis_seq'), experiment_name VARCHAR,
      data_source VARCHAR, created_at TIMESTAMP DEFAULT current_timestamp,
      decision VARCHAR, report_json JSON)""")
    con.close()
def save_analysis(name, source, validation, conversion, decision, report):
    try:
        con=duckdb.connect(DB_PATH)
        con.execute("INSERT INTO analyses (experiment_name,data_source,decision,report_json) VALUES (?,?,?,?)",
                    [name,source,decision["outcome"],json.dumps(report,default=str)])
        con.close()
    except Exception:
        # Dashboard remains usable if local registry is temporarily unavailable.
        pass
