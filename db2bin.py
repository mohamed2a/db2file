# -*- coding: utf-8 -*-
import os
import argparse
from sqlalchemy.orm import create_session
from sqlalchemy.orm import eagerload_all
import codecs
from sqlacodegen.codegen import *


import sys

from sqlalchemy import *

VERSION = "1.1"
SERVER_TYPE = {'mysql': 'mysql://{0}:{1}@{2}/{3}',
               'sqlite': 'sqlite://{4}',
               'oracle': 'oracle://{0}:{1}@{2}/{3}',
               'postgresql': 'postgresql://{0}:{1}@{2}/{3}',
               'mssql': 'mssql://{0}:{1}@{2}/{3}'}

output_filename = 'classes.py'


def welcome():
    print("***********************************************************")
    print("*   Master Spécialisé Big Data & Cloud Computing - BD2C   *")
    print("***********************************************************")
    print("version: " + VERSION)


# build database link from parameters
def build_url(args):
    if args.type in SERVER_TYPE:
        print("Server Type : " + args.server)
        connect_string = SERVER_TYPE[args.type].format(args.username, args.password, args.server, args.database, args.location)
        print("Database connectionString = " + connect_string)
    else:
        print("Database Server Type not recognized!")
        exit(1)

    return connect_string


def generate(connect_string):
    print("Generating SQLAlchemy model code from an existing database...")

    # repetition -- Mr.Rachid will found a solution for this
    engine = create_engine(connect_string)
    metadata = MetaData(bind=engine)

    metadata.reflect(engine, views=True)
    outfile = codecs.open(output_filename, 'w', encoding='utf-8') if output_filename else sys.stdout
    generator = CodeGenerator(metadata, noindexes=False, noconstraints=False, nojoined=False, noinflect=False,
                              noclasses=False)
    generator.render(outfile)
    print("Generated [OK].")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build Database URL from parameters.')
    parser.add_argument('-t', '--type', help='Database server type', required=True)
    args = parser.parse_known_args()

    server_param_required = args[0].type != 'sqlite'
    parser.add_argument('-s', '--server', help='Database server type', default="localhost")
    parser.add_argument('-u', '--username', help='Database server type', required=server_param_required)
    parser.add_argument('-p', '--password', help='Database server type', required=server_param_required)
    parser.add_argument('-d', '--database', help='Database name', required=server_param_required)
    parser.add_argument('-l', '--location', help='Database path', required=not server_param_required)
    parser.add_argument('-o', '--output', help='Output file', required=False)
    args = parser.parse_args()

    # building connection string
    url = build_url(args)
    welcome()

    # Connect to the database
    try:
        engine = create_engine(url)
        metadata = MetaData(bind=engine)
        engine.connect()
    except Exception as err:
        print("Can't connect to database server. Verify your input parameters:\n%s" %err)
        exit(1)

    # Generate SQLAlchemy Model from Database
    from multiprocessing import Process

    gen_process = Process(target=generate, args=(url,))
    gen_process.start()
    gen_process.join()

    # import generated classes
    import classes
    import inspect
    import pickle

    # open a session to execute queries
    session = create_session(bind=engine)

    # get all classes from the generated module
    for name, obj in inspect.getmembers(classes):

        # get a list of generated classes only, without other classes like 'Integer','DateTime'...etc
        if inspect.isclass(obj) and obj.__module__ == 'classes':
            print("\nRetrieving data from Table \"" + obj.__tablename__ + "\" ...")

            # similar to "select * from Table"
            data = session.query(obj).options(eagerload_all("*")).all()

            # make directory if doesn't exist
            if not os.path.exists('data'):
                os.mkdir('data')

            # save the object list in a binary file (serialization)
            with open("data/" + obj.__tablename__ + '.bin', 'wb') as output:
                pickle.dump(data, output)

            print("Finished successfully [OK]")