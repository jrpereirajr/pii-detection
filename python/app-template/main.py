import iris

from sql_utils import run_sql

query="Select * from dc_python.PersistentClass"
print("Running SQL query "+query)
run_sql(query)