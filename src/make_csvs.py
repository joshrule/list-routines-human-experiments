from os.path import exists, basename
from sqlalchemy import create_engine, MetaData, Table
import glob
import json
import pandas as pd


def make_csvs(out_dir):

    trials_path = out_dir + '/trials.csv'
    participants_path = out_dir + '/participants.csv'
    times_path = out_dir + '/times.csv'
    stimuli_path = out_dir + '/stimuli.csv'

    if not (exists(trials_path) and exists(participants_path) and exists(times_path)):

        # What database are we using?
        database_url = 'mysql+pymysql://ubuntu:yx#Ff@#PQodKkGX4DJ2Sy#iar@M9Nh57@127.0.0.1:3306/list_routines'
        # What table holds the relevant data?
        table_name = 'turkdata'
        # Where is the actual experiment data stored?
        data_column_name = 'datastring'
        # if you have workers you wish to exclude, add them here
        exclude = []
        # versions of the experiment to include
        versions = ["0.0.5"]
        # status codes of subjects who completed experiment
        # - NOT_ACCEPTED = 0
        # - ALLOCATED = 1
        # - STARTED = 2
        # * COMPLETED = 3
        # * SUBMITTED = 4
        # * CREDITED = 5
        # - QUITEARLY = 6
        # * BONUSED = 7
        # USE ME FOR TESTING
        statuses = [3, 4, 5, 7]
        # USE ME FOR LIVE EXPERIMENTS
        # statuses = [5,7]

        data = filter_rows(
            collect_rows(database_url, table_name), statuses, exclude, versions)

        make_csv(trials_path, create_trial_df, data, data_column_name)
        make_csv(participants_path, create_participant_df, data, data_column_name)
        make_csv(times_path, create_time_df, data, data_column_name)

    if not exists(stimuli_path):
        # Where are the stimuli?
        stimuli_dirs = [
            '../experiment/static/data/model',
            '../experiment/static/data/dataset',
        ]
        create_stimuli_df(stimuli_dirs).to_csv(stimuli_path, index=False)


def make_csv(path, fn, data, data_column_name):
    print(f"checking for {path}...")
    if not exists(path):
        print(f"  making {path}!")
        df = fn(data, data_column_name)
        df.to_csv(path, index=False)

def create_time_df(data, data_column_name):
    records = []
    for row in data:
        participant_data = json.loads(row[data_column_name])['data']
        records.append(create_instruction_record(participant_data))
        records.append(create_prequiz_record(participant_data))
        records.extend(create_block_records(participant_data))
        records.append(create_postquiz_record(participant_data))
    return pd.DataFrame(records)

def create_instruction_record(data):
    times = [trial['dateTime'] for trial in data if trial['trialdata']['phase'] == "INSTRUCTIONS"]
    return {
        'uniqueid': data[0]['uniqueid'],
        'time': max(times) - min(times),
        'block': 'instructions',
    }

def create_prequiz_record(data):
    times = [trial['dateTime'] for trial in data if trial['trialdata']['phase'] == "prequiz"]
    return {
        'uniqueid': data[0]['uniqueid'],
        'time': max(times) - min(times),
        'block': 'prequiz',
    }

def create_postquiz_record(data):
    times = [trial['dateTime'] for trial in data if trial['trialdata']['phase'] == "postquiz"]
    return {
        'uniqueid': data[0]['uniqueid'],
        'time': max(times) - min(times),
        'block': 'postquiz',
    }

def create_block_records(src_data):
    data = src_data[:]
    blocks = sorted(list(set(trial['trialdata']['block'] for trial in data if trial['trialdata']['phase'] == 'TEST')))
    while data[0]['trialdata']['phase'] != 'TEST':
        data.pop(0)
    records = []

    uniqueid = data[0]['uniqueid']
    block = data[0]['trialdata']['block']
    start = data[0]['dateTime']

    while True:
        while 'block' in data[0]['trialdata'] and data[0]['trialdata']['block'] == block:
            data.pop(0)
        stop = data[0]['dateTime']
        records.append({
            'uniqueid': uniqueid,
            'time': stop - start,
            'block': block,
        })
        if data[0]['trialdata']['phase'] == 'TEST':
            block = data[0]['trialdata']['block']
            start = data[0]['dateTime']
        else:
            return records

def create_participant_df(data, data_column_name):
    return pd.DataFrame(
        [create_participant_record(row, data_column_name) for row in data])


def create_participant_record(row, data_column_name):
    record = json.loads(row[data_column_name])
    del record['data']
    del record['eventdata']
    record.update(record['questiondata'])
    del record['questiondata']
    record['uniqueid'] = row['uniqueid']
    record['ipadress'] = row['ipaddress']
    record['browser'] = row['browser']
    record['platform'] = row['platform']
    record['codeversion'] = row['codeversion']
    record['beginhit'] = row['beginhit']
    record['beginexp'] = row['beginexp']
    record['endhit'] = row['endhit']
    record['bonus'] = row['bonus']
    record['status'] = row['status']
    record['mode'] = row['mode']
    return record


def create_trial_df(data, data_column_name):
    return pd.DataFrame((
        create_trial_record(trial) for row in data
        for trial in json.loads(row[data_column_name])['data']
        if trial['trialdata']['phase'] == 'TEST'
    ))


def create_trial_record(trial):
    return dict(uniqueid=trial['uniqueid'], **trial['trialdata'])


def create_stimuli_df(stimuli_dirs):
    return pd.DataFrame(stimuli_records(stimuli_dirs))


def stimuli_records(stimuli_dirs):
    for dirname in stimuli_dirs:
        purpose = basename(dirname)
        for filename in glob.iglob(dirname + '/*.json'):
            basefilename = basename(filename)
            fid = basefilename[0:4]
            order = basefilename[5:6]
            with open(filename) as fd:
                data = json.load(fd)
                for trial, record in enumerate(data['examples'], 1):
                    yield {
                        'purpose': purpose,
                        'order': order,
                        'trial': trial,
                        'id': fid,
                        'program': data['program'],
                        'input': record['i'],
                        'output': record['o'],
                    }


def collect_rows(db_url, table_name):
    """read all the rows of a table in a MYSQL database"""
    # boilerplace sqlalchemy setup
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.bind = engine
    table = Table(table_name, metadata, autoload=True)
    # make a query and loop through
    s = table.select()
    rows = s.execute()
    return rows


def filter_rows(rows, statuses, excludes, versions):
    """collect all rows matching our criteria"""
    return [
        row for row in rows
        # use subjects who completed
        if row['status'] in statuses and
        # the right version of the experiment
        row['codeversion'] in versions and
        # while it was live
        row['mode'] == 'live' and
        # and aren't excluded
        row['workerid'] not in excludes
    ]

if __name__ == "__main__":
    make_csvs(out_dir='.')
