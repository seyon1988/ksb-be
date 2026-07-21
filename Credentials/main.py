import psycopg2


def main():
    conn = psycopg2.connect('postgres://avnadmin:<redacted>@pg-3e00cdfd-seyon-0c3e.d.aivencloud.com:12186/defaultdb?sslmode=require')

    query_sql = 'SELECT VERSION()'

    cur = conn.cursor()
    cur.execute(query_sql)

    version = cur.fetchone()[0]
    print(version)


if __name__ == "__main__":
    main()