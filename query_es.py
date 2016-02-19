#!/usr/bin/env python

from __future__ import print_function

import argparse
import os
import json

from elasticsearch import Elasticsearch
import pandas as pd


def collectArgs():
    descr = 'Search / Parse ElasticSearch Instance'
    parser = argparse.ArgumentParser(
        description=descr,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-s", "--server", dest="server",
                        default="192.168.99.100",
                        help="ES server address.")
    parser.add_argument("-q", "--query", dest="query",
                        default={'size': 10000,
                                 "query": {
                                     "bool": {
                                         "must": {"match": {"message": "prostate"}},
                                         "must": {"term": {"format": "rsem_genes_normalized"}},
                                         "must_not": {"term": {"sex": "female"}}
                                     }
                                 }},
                        help="Query body to post to ES.")
    parser.add_argument("-f", "--fields", dest="fields", nargs="+",
                        default=["individual_id", "gleason_score",
                                 "derived_data_file", "ccc_did"],
                        help="Fields to return after query.")
    parser.add_argument("-o", "--output-dir", dest="output_dir",
                        default="./",
                        help="query results will be written to this \
                        directory.")
    parser.add_argument("--output-json-template", dest="output_json",
                        action="store_true",
                        help="output query results as json template.")
    parser.add_argument("--output-json-fields", dest="output_json_fields",
                        action="store_true",
                        help="output individual fields from query results as json")
    return parser


def postQuery(es, query, fields):
    response = es.search(doc_type="aggregated-resource",
                         body=query,
                         fields=fields)
    print("%d documents found" % response['hits']['total'])
    return response


def parseResponse(response):
    parsed_response = pd.DataFrame()
    for doc in response['hits']['hits']:
        parsed_doc = pd.DataFrame(doc['fields'])
        parsed_response = parsed_response.append(parsed_doc, ignore_index=True)
    return parsed_response


if __name__ == '__main__':
    parser = collectArgs()
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    es = Elasticsearch([{"host": args.server,
                         "port": 9200}])
    result = postQuery(es=es,
                       query=args.query,
                       fields=args.fields)
    parsed_result = parseResponse(response=result)

    # write tsv
    parsed_result.to_csv(args.output_dir + "es_query_results.txt", sep="\t",
                         header=True, index=False)

    # write json templates
    if args.output_json:
        with open(args.output_dir + "es_query_results.json", "w") as outfile:
            json.dump(parsed_result.to_dict(orient="list"), outfile)
            outfile.close()

    # individual field outputs
    if args.output_json_fields:
        for field in args.fields:
            with open(args.output_dir + "/" + field + ".json", "w") as outfile:
                json.dump(parsed_result.to_dict(orient="list")[field], outfile)
                outfile.close()
