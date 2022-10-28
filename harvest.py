import csv
import mysql.connector

from dateutil.rrule import rrule, MONTHLY
from datetime import datetime, timedelta

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, MetadataReader
from oaipmh import error as oaipmhError

URL = 'http://oai.narcis.nl/oai'

MAX_RECORD_FILE = 25000  # Max record per CSV file
CSV = {
    "file": False,
    "writer": None,
    "write_count": 1,  # Counts the number of records written in one file - for file split
    "file_count": 1  # Counts the number of files written in a two date period - for file naming
}


def get_csv(file_count, from_date, until_date, new=True):
    # file name
    file_name = create_file_name(file_count, from_date, until_date)
    print(' > Creating file', file_count, from_date.strftime('%Y%m%d'), until_date.strftime('%Y%m%d'), file_name)

    # create a new file
    f = open(file_name, 'w', newline='')
    fieldnames = ['doi', 'institute', 'datestamp', 'type', 'identifiers', 'date', 'source', 'rights', 'partof',
                  'creators', 'title']
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='$', quotechar='"')
    writer.writeheader()
    return {"file": f, "writer": writer}


# Get oaipmh client
def get_client():
    registry = MetadataRegistry()

    # instantiate the oai_Reader with the right metadata
    oai_dc_reader = MetadataReader(
        fields={
            'title': ('textList', 'oai_dc:dc/dc:title/text()'),
            'creator': ('textList', 'oai_dc:dc/dc:creator/text()'),
            'subject': ('textList', 'oai_dc:dc/dc:subject/text()'),
            'description': ('textList', 'oai_dc:dc/dc:description/text()'),
            'publisher': ('textList', 'oai_dc:dc/dc:publisher/text()'),
            'contributor': ('textList', 'oai_dc:dc/dc:contributor/text()'),
            'date': ('textList', 'oai_dc:dc/dc:date/text()'),  # publicatie datum voor de instelling
            'type': ('textList', 'oai_dc:dc/dc:type/text()'),
            'format': ('textList', 'oai_dc:dc/dc:format/text()'),
            'identifier': ('textList', 'oai_dc:dc/dc:identifier/text()'),
            'source': ('textList', 'oai_dc:dc/dc:source/text()'),
            'language': ('textList', 'oai_dc:dc/dc:language/text()'),
            'relation': ('textList', 'oai_dc:dc/dc:relation/text()'),
            'coverage': ('textList', 'oai_dc:dc/dc:coverage/text()'),
            'rights': ('textList', 'oai_dc:dc/dc:rights/text()'),
            'ispartof': ('textList', 'oai_dc:dc/dc:isPartOf/text()')
        },
        namespaces={
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            'dc': 'http://purl.org/dc/elements/1.1/'}
    )

    registry.registerReader('oai_dc', oai_dc_reader)
    client = Client(URL, registry)
    return client


# This function will harvest everything between two dates
def initial_harvest():
    from_date = datetime.fromisoformat('2022-09-01')
    # until_date = datetime.fromisoformat('2017-02-01')
    until_date = datetime.fromisoformat('2022-10-01')

    client = get_client()

    # Set start cycle date for the initial iteration
    start_itr = from_date

    for end_itr in rrule(freq=MONTHLY, dtstart=from_date, until=until_date)[1:]:

        print('# Processing dates: %s to %s , count: %s' % (
        start_itr.strftime('%Y%m%d'), end_itr.strftime('%Y%m%d'), CSV['write_count']))

        # reset file on every pair of dates
        if CSV["file"] is not False:
            CSV["file"].close()
            CSV["file"] = False
            CSV["writer"] = False
            CSV["file_count"] = 1
            CSV["write_count"] = 1

        try:

            records = client.listRecords(metadataPrefix='oai_dc', from_=start_itr, until=end_itr, set='publication')

            for num, record in enumerate(records):
                if record[0].isDeleted() is False and record[1] is not None:
                    rd = get_record_data(record)
                    # continue if pubtype is not present or if it's an article
                    if not rd['type'] or rd['type'] == 'info:eu-repo/semantics/article':
                        if write_record_to_csv(rd, end_itr, start_itr) is True:
                            CSV["write_count"] += 1
                            write_record_to_mysql(rd)

        except oaipmhError.NoRecordsMatchError as e:
            print("     !!!!! Exception: ", e)

        # print some info
        print('     >>> written %d records between %s and %s' % (CSV['write_count'] - 1, start_itr, end_itr))

        # change start iteration date to the current end iteration date close current file
        start_itr = end_itr

    print('## END PROCESSING', from_date, until_date)


def recurring_harvest(hours):
    # from_date = '2022-07-13T22:00:00Z'
    # from_date = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%SZ")
    until_date = datetime.now()
    # from_date = until_date - timedelta(hours=hours)
    from_date = datetime.fromisoformat('2022-09-01')

    client = get_client()
    try:
        records = client.listRecords(metadataPrefix='oai_dc', from_=from_date, until=until_date, set='publication')
        for num, record in enumerate(records):
            if record[0].isDeleted() is False and record[1] is not None:
                rd = get_record_data(record)
                # continue if pubtype is not present or if it's an article
                if not rd['type'] or rd['type'] == 'info:eu-repo/semantics/article':
                    write_record_to_csv(rd, until_date, from_date)
                    write_record_to_mysql(rd)

    except Exception as e:
        print("!!!!! Exception:", e)


# def harvest(from_date, until_date):
#     client = get_client()
#
#     with open('harvest.csv', 'w', newline='') as f:
#         fieldnames = ['doi', 'institute', 'datestamp', 'type', 'identifiers', 'date', 'source', 'rights', 'partof',
#                       'creators', 'title']
#         writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='$', quotechar='"')
#         writer.writeheader()
#
#         records = client.listRecords(metadataPrefix='oai_dc', from_=from_date, until=until_date, set='publication')
#         # to make it more robust, we would have to check if the list isn't empty
#
#         for num, record in enumerate(records):
#             # print('%0.6d %s' % (num, record[0].identifier()))
#
#             # check if item has been deleted
#             # deleted items have 'header status=deleted' and no metadata
#             # if not deleted, get metadata: title, creator, date, type, source, identifier
#             # field 'ispartof' is not included in the module, so we hacked it in
#
#             if record[0].isDeleted():
#                 print("item deleted")
#             elif record[1] is not None:
#                 write_record_to_csv(record, writer)

def get_record_data(record):
    header = record[0]
    datestamp = header.datestamp()
    institute = header.identifier()
    fields = record[1].getMap()
    pub_type = fields['type'][0] if type(fields['type']) is list and len(fields['type']) > 0 else ''

    identifiers = list_2_string(fields['identifier'])
    itemdate = fix_item_date(fields['date'])

    doi = ''
    for id in fields['identifier']:
        if id.startswith('10.'):
            doi = id
    if len(doi) > 254:
        print('DOI too long: ', doi)
        doi = doi[:254]

    source = list_2_string(fields['source'])
    rights = list_2_string(fields['rights'])
    partof = list_2_string(fields['ispartof'])
    creator = list_2_string(fields['creator'])
    title = list_2_string(fields['title'])

    return {'doi': doi, 'institute': institute, 'datestamp': datestamp, 'type': pub_type,
            'identifiers': identifiers, 'date': itemdate, 'source': source, 'rights': rights,
            'partof': partof, 'creators': creator, 'title': title}


def write_record_to_csv(record_data, end_itr, start_itr):
    """
    Write a record to CSV, if the record is written return true
    """

    # Get file if exists or create e new one
    writer = get_file_writer(end_itr, start_itr)
    writer.writerow(record_data)
    return True

    return False


def get_file_writer(end_itr, start_itr):
    # Create the file
    if CSV["write_count"] >= MAX_RECORD_FILE:
        # Get another file
        CSV["file"].close()
        CSV["file_count"] += 1
        CSV["write_count"] = 1

    if CSV["file"] is False or CSV["file"].closed:
        csv_file = get_csv(CSV["file_count"], start_itr, end_itr, True)
        CSV["writer"] = csv_file["writer"]
        CSV["file"] = csv_file["file"]

    return CSV["writer"]


def create_file_name(file_count, from_date, until_date):
    file_name = 'harvest/%s-%s_%d.csv' % (
        from_date.strftime('%Y%m%d'), until_date.strftime('%Y%m%d'), file_count
    )
    return file_name


def write_record_to_mysql(rd):
    mydb = mysql.connector.connect(
        host="localhost",
        port="3305",
        user="root",
        password="stocazzo",
        database="ukbasis"
    )

    mycursor = mydb.cursor()

    sql = "INSERT INTO narcis (doi, type, datestamp, identifiers, date, title) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (rd['doi'], rd['type'], rd['datestamp'], rd['identifiers'], rd['date'], rd['title'])
    mycursor.execute(sql, val)

    mydb.commit()


def fix_item_date(date):
    if type(date) is not list or len(date) == 0:
        return ''

    date_string = date[0]
    date_parts = date_string.split("-")
    year = date_parts[0]
    month = date_parts[1].zfill(2) if 1 < len(date_parts) else '01'
    day = date_parts[2].zfill(2) if 2 < len(date_parts) else '01'
    return year + "-" + month + "-" + day


def list_2_string(list):
    if len(list) == 1:
        return list[0]
    return ','.join(f'"{w}"' for w in list)


if __name__ == '__main__':
    recurring_harvest(12)
    # initial_harvest()
