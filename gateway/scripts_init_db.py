from app.db.bootstrap import run_sql_file

if __name__ == '__main__':
    run_sql_file('migrations/0001_initial.sql')
    print('Initialized database schema.')
