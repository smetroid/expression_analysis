#!/usr/bin/python
import sqlite3, csv, re
import sys


def createDBs(conn):
    interproscan7_table = "create table interproscan7(trinity, random1, random2, sites, code1, description1, start, stop, evalue, random3, date, code2, description2, goterms, reactome)"
    expression_counts_table = "create table expression_counts (trinity, ho8_quants, ho7_quants)"
    fasta                   = "create table fasta (trinity, data BLOB)"

    cur = conn.cursor()
    cur.execute(interproscan7_table)
    cur.execute(expression_counts_table)
    cur.execute(fasta)


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


def loadFastaData(cur):
    trinity = ""
    data = ""
    with open(sys.argv[3]) as f:
        for i in f:
            match = re.search(r"^>TRINITY", i)
            print i
            if (match):
                if (data == ""):
                    trinity_field = re.split(" ", match.group(0))
                    trinity = trinity_field[0]
                    data = i
                else:
                    # print trinity
                    # print data
                    sql_insert = (trinity, data)
                    cur.execute("INSERT INTO fasta VALUES (?, ?)", tuple(sql_insert))

                    trinity_field = re.split(" ", match.group(0))
                    trinity = trinity_field[0]
                    data = i
            else:
                data += i

        # When EOF is reached commit the last values into SQL
        sql_insert = (trinity, data)
        cur.execute("INSERT INTO fasta VALUES (?, ?)", tuple(sql_insert))


def fastData():
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
    loadFastaData(cur)


    conn.commit()
    conn.close()
