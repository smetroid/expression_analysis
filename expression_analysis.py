#!/usr/bin/python
import sqlite3, csv, re
import sys


def createDBs(conn):
    interproscan7_table = "create table interproscan7(trinity, random1, random2, sites, code1, description1, start, stop, evalue, random3, date, code2, description2, goterms, reactome)"
    expression_counts_table = "create table expression_counts (trinity, ho8_quants, ho7_quants)"

    cur = conn.cursor()
    cur.execute(interproscan7_table)
    cur.execute(expression_counts_table)


def testDB(cur):
    cur.execute("SELECT * from hostinfo")
    rows = cur.fetchall()
    for row in rows:
        print(row)

    return None


def loadInterproScan7(cur):
    tsv_data_file = open(sys.argv[1])
    tsv_reader = csv.reader(tsv_data_file, delimiter="\t")

    for i in tsv_reader:
        # Remove the .p1 from the trinity value
        i[0] = re.sub(r'_i.*$', '', i[0])
        print(i)
        if len(i) < 15:
            continue
            cur.execute("INSERT INTO interproscan7 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(i))
        else:
            cur.execute("INSERT INTO interproscan7 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(i))


def loadNorm(cur):
    tsv_data_file = open(sys.argv[2])
    tsv_reader = csv.reader(tsv_data_file, delimiter="\t")

    for i in tsv_reader:
        # Remove the "_i1-4" from the trinity value
        i[0] = re.sub(r'_i.*$', '', i[0])
        print(i)
        if len(i) == 0:
            continue
        else:
            cur.execute("INSERT INTO expression_counts VALUES (?, ?, ?)", tuple(i))


def getDataSet(cur, filter):
    cur.execute("SELECT trinity,start,stop FROM interproscan7 WHERE code1 LIKE ?", (filter,))
    file_name = "%s_%s.csv" % (sys.argv[2], filter)
    rows = cur.fetchall()
    data = []
    fo = open(file_name, 'w')
    for row in rows:
        info = "%s,%s,%s\n" % (row[0],row[1],row[2])
        data.append(info)

    fo.writelines(data)
    fo.close()


def buildTempView(cur):
    #Generate a temporary view for the ho8 and ho7 quants aggregate counts
    sql_view = ('CREATE TEMP VIEW expression_count_aggregates '
                'AS '
                'SELECT trinity, SUM(ho8_quants) as ho8_quants, '
                'SUM(ho7_quants) as ho7_quants '
                'FROM expression_counts '
                'GROUP BY trinity ')

    cur.execute(sql_view)


def getNormAndHoData(cur, filter):

    sql      = ('SELECT DISTINCT inter.trinity, inter.start, inter.stop, '
                'ec.ho8_quants, ec.ho7_quants '
                'FROM interproscan7 inter '
                'INNER JOIN expression_count_aggregates ec '
                'ON inter.trinity = ec.trinity '
                'WHERE code1 LIKE "%s" '
                'ORDER BY inter.trinity ')

    file_name = "%s_%s.csv" % (sys.argv[1],filter)
    print sql % (filter)
    cur.execute(sql % (filter))
    rows = cur.fetchall()

    data = []
    header = "%s,%s,%s,%s,%s\n" % ("trinity", "start", "stop", "ho8_quants", "ho7_quants")
    data.append(header)
    fo = open(file_name, 'w')
    for row in rows:
        info = "%s,%s,%s,%s,%s\n" % (row[0],row[1],row[2],row[3],row[4])
        data.append(info)

    fo.writelines(data)
    fo.close()


if __name__ == "__main__":
    conn = sqlite3.Connection("expression_data.sqlite3")
    #conn = sqlite3.Connection(":memory:")
    createDBs(conn)
    cur = conn.cursor()
    loadInterproScan7(cur)
    loadNorm(cur)


    # PF00201
    getDataSet(cur, "PF00201")
    # PS00375
    getDataSet(cur, "PS00375")
    buildTempView(cur)
    getNormAndHoData(cur, "PF00201")
    getNormAndHoData(cur, "PS00375")


    conn.commit()
    conn.close()
