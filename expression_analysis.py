#/usr/bin/python
#import getpass
#import re
#import requests
import sqlite3, csv
import sys
#import unicodedata


def createDB(conn):
    interproscan7_table = "create table interproscan7(trinity, random1, random2, sites, codes1, description1, start, stop, evalue, randowm3, date, codes2, description2, goterms, reactom)"
    expression_counts_table = "create table expression_counts (trinity, ho8_quants, ho7_quants)"

    cur = conn.cursor()
    cur.execute(interproscan7_table)
    cur.execute(expression_counts_table)


def executeQuery(sql, username, password):
    base_url = "https://www.e-access.att.com"
    query_url = "%s/cnci/cgi-bin/rct/cce_query_out" % (base_url)

    payload = {'q1' : sql, 'CSV' : 'on'}
    headers = {'Content-Type' : 'application/json'}
    ro = requests.post(query_url, data=payload, headers=headers, auth=(username,password), verify=False)

    #print ro.status_code, ro.reason

#    return csv_file


def popInterProScan7(cur, data):
    for i in data:
        i = i.strip()
        if len(i) == 0:
            continue
        else:
            i = i.split("\t")
            cur.execute("INSERT INTO interpro_scan_7 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(i))

    return None

def popInterProScan8(cur, data):
    for i in data:
        i = i.strip()
        if len(i) == 0:
            continue
        else:
            i = i.split("\t")
            cur.execute("INSERT INTO interpro_scan_7 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(i))

    return None

def testDB(cur):
    cur.execute("SELECT * from hostinfo")
    rows = cur.fetchall()
    for row in rows:
        print(row)

    return None

# PF00201
def getDataSet(cur, filter):
    cur.execute("SELECT trinity,start,stop FROM interproscan7 WHERE codes1 LIKE ?", (filter,))
    file_name = "candidate_expression_%s.csv" % (filter)
    rows = cur.fetchall()
    data = []
    fo = open(file_name, 'w')
    for row in rows:
        info = "%s,%s,%s\n" % (row[0],row[1],row[2])
        data.append(info)
        print info

    fo.writelines(data)
    fo.close()

if __name__ == "__main__":
    conn = sqlite3.Connection("expression_data.sqlite3")
    #conn = sqlite3.Connection(":memory:")
    #cur = createDB(conn)
    cur = conn.cursor()
    '''
    tsv_data_file = open(sys.argv[1])
    tsv_reader = csv.reader(tsv_data_file, delimiter="\t")

    for i in tsv_reader:
        print(i)
        #i = i.strip()
        if len(i) == 0:
            continue
        else:
            #i = i.split(", ")
            cur.execute("INSERT INTO interproscan7 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(i))
     '''


    # PF00201
    getDataSet(cur, "PF00201")
    # PS00375
    getDataSet(cur, "PS00375")
    conn.commit()
    conn.close()
