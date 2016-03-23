#!/usr/bin/env python
"""
Convert fastq files to unaligned BAM file with PCAWG style header using
biobambam2
"""
from __future__ import print_function

import argparse
import dateutil.parser
import pytz
import os
import random
import re
import shutil
import string
import subprocess
import sys


def collect_args():
    descr = 'Convert fastq files to unaligned BAM file with PCAWG style header'
    parser = argparse.ArgumentParser(
        description=descr
    )
    parser.add_argument("--fastq_1",
                        required=True,
                        help="fastq file to be converted to BAM")
    parser.add_argument("--fastq_2",
                        required=True,
                        help="fastq mate file to be converted to BAM")
    parser.add_argument("--output-dir",
                        dest="output_dir",
                        default="./",
                        help="unaligned BAM output")
    parser.add_argument("--output-filename",
                        dest="output_filename",
                        help="unaligned BAM output")
    parser.add_argument("--ID",
                        help="<centre_name>:<unique_text>")
    parser.add_argument("--CN",
                        help="<centre_name>")
    parser.add_argument("--DT",
                        help="YYYY-MM-DD'T'HH24:MI:SS.FFTZR")
    parser.add_argument("--LB",
                        help="WGS:<center_name>:<lib_id>")
    parser.add_argument("--PI",
                        help="predicted median insert size")
    parser.add_argument("--PL",
                        default="ILLUMINA",
                        choices=["CAPILLARY", "LS454", "ILLUMINA", "SOLID",
                                 "HELICOS", "IONTORRENT", "PACBIO"],
                        help="platform/technology used to produce the reads")
    parser.add_argument("--PM",
                        choices=["Illumina Genome Analyzer II",
                                 "Illumina HiSeq",
                                 "Illumina HiSeq 2000",
                                 "Illumina HiSeq 2500"],
                        help="platform model")
    parser.add_argument("--PU",
                        help="<center_name>:<run>_<lane>[#<tag>]")
    parser.add_argument("--SM",
                        help="uuid for sample")
    parser.add_argument("--CO",
                        action='append',
                        help="provide key value pairs for sample tracking data: \
                        dcc_project_code, submitter_donor_id, \
                        submitter_specimen_id, submitter_sample_id, \
                        dcc_specimen_type, use_cntl")
    return parser


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def execute(cmd):
    print("RUNNING...\n", cmd, "\n")
    process = subprocess.Popen(cmd,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()

    stderr = process.communicate()[1]
    if stderr is not None:
        print(stderr)
    if process.returncode != 0:
        print("[WARNING] command: {0} exited with code: {1}".format(
            cmd, process.returncode
        ))
    return process.returncode


def to_iso8601(time_string):
    parsed_time = dateutil.parser.parse(time_string)
    # add timezone info
    if parsed_time.tzinfo is None:
        # add +00:00 as tzinfo
        parsed_time.replace(tzinfo=pytz.timezone('UTC'))
    # remove microseconds
    if parsed_time.microsecond != 0:
        parsed_time.replace(microsecond=0)
    return parsed_time.isoformat()


def fastq2bam(args, tmp_path, output_dir, output_filename):
    #############################
    # write header
    #############################
    HD = "\t".join(["@HD", "VN:1.4"])

    # DT format validation
    if args.DT is not None:
        try:
            # convert to proper format if possible
            args.DT = to_iso8601(args.DT)
        except Exception as e:
            print("[WARNING]  DT field must be ISO 8061 compliant: \
            'YYYY-MM-DD\"T\"HH24:MI:SS.FFTZR'")
            print(e)
            raise

    RG_parts = ["@RG"]
    for key, value in vars(args).items():
        # all possible RG groups
        RG_keys = ['ID', 'CN', 'DS', 'DT', 'FO', 'KS', 'LB', 'PG', 'PI', 'PL',
                   'PM', 'PU', 'SM']
        if key in RG_keys and value is not None:
            RG_parts.append(":".join([key, value]))
    RG = "\t".join(RG_parts)

    # TODO: @CO input validation
    # if len(args.CO) != 6:
    #     raise ValueError("You must provide all sample tracking data")
    if args.CO is not None:
        CO = "\n".join(["\t".join(["@CO", key_val]) for key_val in args.CO])
    else:
        CO = ""

    formatted_header = "\n".join([HD, RG, CO])

    # write header to tmp file
    tmp_header_file = os.path.join(tmp_path, "header.sam")
    with open(tmp_header_file, 'w') as f:
        f.write(formatted_header)
        f.close()

    #############################
    # convert fastq to bam
    #############################
    tmp_bam = os.path.join(tmp_path, "tmp.bam")
    base_cmd = "fastqtobam I=%s I=%s md5=1 md5filename=%s.md5  > %s"
    cmd = base_cmd % (args.fastq_1, args.fastq_2, tmp_bam, tmp_bam)
    execute(cmd)

    #############################
    # replace header with PCAWG
    # style header
    #############################
    base_cmd = "cat %s | bamreset exclude=QCFAIL,SECONDARY,SUPPLEMENTARY resetheadertext=%s md5=1 md5filename=%s.md5 > %s"
    cmd = base_cmd % (tmp_bam,
                      tmp_header_file,
                      os.path.join(output_dir, output_filename),
                      os.path.join(output_dir, output_filename))
    execute(cmd)


def main():
    parser = collect_args()
    args = parser.parse_args()

    if args.output_filename is None:
        output_filename = re.sub("(\_[0-9]\.fastq|\.fastq|\_[0-9]\.fq|\.fq)",
                                 "",
                                 os.path.basename(args.fastq_1)) + ".bam"
    else:
        output_filename = os.path.basename(args.output_filename)

    output_dir = os.path.abspath(args.output_dir)
    if not os.path.isdir(output_dir):
        execute("mkdir -p {0}".format(output_dir))

    # setup tmp output directory to store intermediate files
    tmp_output_dir = id_generator()
    tmp_path = os.path.join(output_dir, tmp_output_dir)
    if not os.path.isdir(tmp_path):
        execute("mkdir -p {0}".format(tmp_path))

    try:
        fastq2bam(args, tmp_path, output_dir, output_filename)
    except Exception as e:
        print(e)
        raise
    finally:
        # cleanup
        shutil.rmtree(tmp_path)

if __name__ == "__main__":
    main()
