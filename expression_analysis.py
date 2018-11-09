#!/usr/bin/python
import sqlite3, csv, re
import sys


def createDBs(conn):
    interproscan7_table     = "create table interproscan7(trinity, random1, random2, sites, code1, description1, start, stop, evalue, random3, date, code2, description2, goterms, reactome)"
    expression_counts_table = "create table expression_counts (trinity, ho8_quants, ho7_quants)"
    interproscan8_table     = "create table interproscan8(trinity, random1, random2, sites, code1, description1, start, stop, evalue, random3, date, code2, description2, goterms, reactome)"
    fastaho7                = "create table fastaho7 (trinity, data BLOB)"
    fastaho8                = "create table fastaho8 (trinity, data BLOB)"
    fastaho7transdecoder    = "create table fastaho7transdecoder (trinity, data BLOB)"
    fastaho8transdecoder    = "create table fastaho8transdecoder (trinity, data BLOB)"
    ho8ids_with_quantids    = "create table ho8idswithquantsids (ho8ids, jointids)"

    cur = conn.cursor()
    cur.execute(interproscan7_table)
    cur.execute(interproscan8_table)
    cur.execute(expression_counts_table)
    cur.execute(fastaho7)
    cur.execute(fastaho8)
    cur.execute(fastaho7transdecoder)
    cur.execute(fastaho8transdecoder)
    cur.execute(ho8ids_with_quantids)


def testDB(cur):
    cur.execute("SELECT * from hostinfo")
    rows = cur.fetchall()
    for row in rows:
        print(row)

    return None


def loadInterproScan7(cur):
    tsv_data_file = open("./data/Ho7_K31_Trinity_InterProScan_1.tsv")
    tsv_reader = csv.reader(tsv_data_file, delimiter="\t")

    for i in tsv_reader:
        # Remove the .p1 from the trinity value
        #i[0] = re.sub(r'_i.*$', '', i[0])
        print(i)
        if len(i) < 15:
            continue
            cur.execute("INSERT INTO interproscan7 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(i))
        else:
            cur.execute("INSERT INTO interproscan7 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(i))


def loadInterproScan8(cur):
    tsv_data_file = open("./data/Ho8_k31_Trinity_InterProScan.tsv")
    tsv_reader = csv.reader(tsv_data_file, delimiter="\t")

    for i in tsv_reader:
        # Remove the .p1 from the trinity value
        #i[0] = re.sub(r'_i.*$', '', i[0])
        print(i)
        if len(i) < 15:
            continue
            cur.execute("INSERT INTO interproscan8 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(i))
        else:
            cur.execute("INSERT INTO interproscan8 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(i))





def loadNorm(cur):
    tsv_data_file = open("./norm")
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
    file_name = "%s_%s.csv" % ("interproscan7", filter)
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
    sql_view = ('CREATE VIEW expression_count_aggregates '
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

    file_name = "%s_%s.csv" % ("normAndHoData",filter)
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


def loadFastaDataHo7(cur):
    trinity = ""
    data = ""
    with open("./data/Ho7_K31_Trinity.fasta") as f:
        for i in f:
            match = re.search(r'^>TRINITY', i)
            #print i
            if (match):
                if (data != ""):
                    sql_insert = (trinity, data)
                    cur.execute("INSERT INTO fastaho7 VALUES (?, ?)", tuple(sql_insert))
                    data = i
                else:
                    data = i

                trinity_field = i.split(" ")
                #trinity = re.sub(r'_i.*$', '', trinity_field[0]).replace('>', '')
                trinity = trinity_field[0].replace('>', '')
            else:
                data += i

        # When EOF is reached commit the last values into SQL
        sql_insert = (trinity, data)
        cur.execute("INSERT INTO fastaho7 VALUES (?, ?)", tuple(sql_insert))


def loadFastaDataHo8(cur):
    trinity = ""
    data = ""
    with open("./data/Ho8_K31_Trinity.fasta") as f:
        for i in f:
            match = re.search(r'^>TRINITY', i)
            #print i
            if (match):
                if (data != ""):
                    sql_insert = (trinity, data)
                    cur.execute("INSERT INTO fastaho8 VALUES (?, ?)", tuple(sql_insert))
                    data = i
                else:
                    data = i

                trinity_field = i.split(" ")
                #trinity = re.sub(r'_i.*$', '', trinity_field[0]).replace('>', '')
                trinity = trinity_field[0].replace('>', '')
            else:
                data += i

        # When EOF is reached commit the last values into SQL
        sql_insert = (trinity, data)
        cur.execute("INSERT INTO fastaho8 VALUES (?, ?)", tuple(sql_insert))


def loadFastaDataHo7Transdecoder(cur):
    trinity = ""
    data = ""
    with open("./data/Ho7_K31_Trinity.fasta.transdecoder.pep") as f:
        for i in f:
            match = re.search(r'^>TRINITY', i)
            #print i
            if (match):
                if (data != ""):
                    sql_insert = (trinity, data)
                    cur.execute("INSERT INTO fastaho7transdecoder VALUES (?, ?)", tuple(sql_insert))
                    data = i
                else:
                    data = i

                trinity_field = i.split(" ")
                #trinity = re.sub(r'_i.*$', '', trinity_field[0]).replace('>', '')
                trinity = trinity_field[0].replace('>', '')
            else:
                data += i

        # When EOF is reached commit the last values into SQL
        sql_insert = (trinity, data)
        cur.execute("INSERT INTO fastaho7transdecoder VALUES (?, ?)", tuple(sql_insert))


def loadFastaDataHo8Transdecoder(cur):
    trinity = ""
    data = ""
    with open("./data/Ho8_K31_Trinity.fasta.transdecoder.pep") as f:
        for i in f:
            match = re.search(r'^>TRINITY', i)
            #print i
            if (match):
                if (data != ""):
                    sql_insert = (trinity, data)
                    cur.execute("INSERT INTO fastaho8transdecoder VALUES (?, ?)", tuple(sql_insert))
                    data = i
                else:
                    data = i

                trinity_field = i.split(" ")
                #trinity = re.sub(r'_i.*$', '', trinity_field[0]).replace('>', '')
                trinity = trinity_field[0].replace('>', '')
            else:
                data += i

        # When EOF is reached commit the last values into SQL
        sql_insert = (trinity, data)
        cur.execute("INSERT INTO fastaho8transdecoder VALUES (?, ?)", tuple(sql_insert))


def loadHo8idsWithQuantIds(cur):
    tsv_data_file = open("./data/ho8_ids_with_corresponding_combined_ho7_ho8_ids.csv")
    tsv_reader = csv.reader(tsv_data_file, delimiter="\t")

    for i in tsv_reader:
        # Remove the "_i1-4" from the trinity value
        #i[0] = re.sub(r'_i.*$', '', i[0])
        print(i)
        if len(i) == 0:
            continue
        else:
             cur.execute("INSERT INTO ho8idswithquantsids VALUES (?, ?)", tuple(i))




def fastaDataQuery(cur):
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
    loadInterproScan8(cur)
    loadNorm(cur)

    # PF00201
    getDataSet(cur, "PF00201")
    # PS00375
    getDataSet(cur, "PS00375")
    buildTempView(cur)
    getNormAndHoData(cur, "PF00201")
    getNormAndHoData(cur, "PS00375")
    loadFastaDataHo7(cur)
    loadFastaDataHo8(cur)
    loadFastaDataHo7Transdecoder(cur)
    loadFastaDataHo8Transdecoder(cur)
    loadHo8idsWithQuantIds(cur)


    conn.commit()
    conn.close()
