import iris

def run_sql(query):
    rs=iris.sql.exec(query)
    for idx, row in enumerate(rs):
        print(f"[{idx}]: {row}")