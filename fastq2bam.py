#!/usr/bin/env python
"""
Convert fastq files to unaligned BAM file with PCAWG style header using
biobambam2 version 2.0.30
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
                        help="Fastq file to be converted to BAM")
    parser.add_argument("--fastq_2",
                        required=False,
                        help="Fastq mate file to be converted to BAM")
    parser.add_argument("--is-gz",
                        dest="is_gz",
                        default="True",
                        choices=["True", "False"],
                        help="Input fastq files are gzipped. Default: True")
    parser.add_argument("--namescheme",
                        default="generic",
                        choices=["generic", "c18s", "c18pe", "pairedfiles"],
                        help="")
    parser.add_argument("--qualityoffset",
                        type=int,
                        help="Quality offset. Default: 33")
    parser.add_argument("--qualitymax",
                        type=int,
                        help="Maximum valid quality value. Default: 41")
    parser.add_argument("--checkquality",
                        default="True",
                        choices=["True", "False"],
                        help="Check quality. Default: True")
    parser.add_argument("--output-dir",
                        dest="output_dir",
                        default="./",
                        help="Output directory")
    parser.add_argument("--output-filename",
                        dest="output_filename",
                        help="File name for Unaligned BAM output")
    parser.add_argument("--ID",
                        required=True,
                        help="Read group identifier. Each @RG line must have a \
                        unique ID. The value of ID is used in the RG tags of \
                        alignment records. Must be unique among all read \
                        groups in header section. Read group IDs may be \
                        modified when merging SAM files in order to handle \
                        collisions. Ex: <centre_name>:<unique_text>")
    parser.add_argument("--CN",
                        help="Name of sequencing center producing the read")
    parser.add_argument("--DS",
                        help="Description")
    parser.add_argument("--DT",
                        help="Date the run was produced (ISO8601 date or \
                        date/time)")
    parser.add_argument(
        "--FO",
        help="Flow order. The array of nucleotide bases that correspond to the \
        nucleotides used for each flow of each read. Multi-base flows are \
        encoded in IUPAC format, and non-nucleotide flows by various other \
        characters. Format: /\*|[ACMGRSVTWYHKDBN]+/")
    parser.add_argument("--KS",
                        help="The array of nucleotide bases that correspond to \
                        the key sequence of each read.")
    parser.add_argument("--LB",
                        required=True,
                        help="Library. Ex: 'WGS:<center_name>:<lib_id>'")
    parser.add_argument("--PG",
                        help="Programs used for processing the read group. \
                        Default: fastqtobam")
    parser.add_argument("--PI",
                        help="Predicted median insert size")
    parser.add_argument("--PL",
                        required=True,
                        default="ILLUMINA",
                        choices=["CAPILLARY", "LS454", "ILLUMINA", "SOLID",
                                 "HELICOS", "IONTORRENT", "PACBIO"],
                        help="Platform/technology used to produce the reads")
    parser.add_argument("--PM",
                        choices=["Illumina Genome Analyzer II",
                                 "Illumina HiSeq",
                                 "Illumina HiSeq 2000",
                                 "Illumina HiSeq 2500"],
                        help="Platform model")
    parser.add_argument("--PU",
                        help="Platform unit. Ex: '<center_name>:<run>_<lane>[#<tag>]'")
    parser.add_argument("--SM",
                        required=True,
                        help="Sample id")
    parser.add_argument("--CO",
                        action='append',
                        help="Comment lines - provide key value pairs for \
                        sample tracking data: \
                        dcc_project_code, \
                        submitter_donor_id, \
                        submitter_specimen_id,\
                        submitter_sample_id, \
                        dcc_specimen_type, \
                        use_cntl")
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
        sys.stderr.write(stderr)
    if process.returncode != 0:
        sys.stderr.write("[ERROR] command: {0} exited with code: {1}".format(
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


def fastq2bam(args, output_dir, output_filename):
    if args.DT is not None:
        try:
            # try to convert DT to ISO 8061 formatted datetime
            args.DT = to_iso8601(args.DT)
        except Exception:
            sys.stderr.write(
                "[ERROR]  DT field was not able to be expressed as an " +
                "ISO 8061 compliant datetime: 'YYYY-MM-DD\"T\"HH24:MI:SS'")
            raise

    base_cmd = ["fastqtobam", "I={0}".format(args.fastq_1)]
    if args.fastq_2 is not None:
        base_cmd.append("I={0}".format(args.fastq_2))

    # ID is required
    base_cmd.append("RGID={0}".format(args.ID))
    for key, value in sorted(vars(args).items()):
        RG_keys = ['CN', 'DS', 'DT', 'FO', 'KS', 'LB', 'PG', 'PI', 'PL',
                   'PM', 'PU', 'SM']
        if key in RG_keys and value is not None:
            if key == "DT":
                base_cmd.append("RG{0}={1}".format(key, to_iso8601(value)))
            else:
                base_cmd.append("RG{0}={1}".format(key, value))

    if args.is_gz == "True":
        base_cmd.append("gz=1")

    if args.checkquality == "False":
        base_cmd.append("checkquality=0")

    for key, value in vars(args).items():
        valid_args = ['qualityoffset', 'qualitymax', 'namescheme']
        if key in valid_args and value is not None:
            base_cmd.append("{0}={1}".format(key, value))

    base_cmd.append("> {0}".format(os.path.join(output_dir, output_filename)))
    cmd = " ".join(base_cmd)
    execute(cmd)


def fastq2bam_2step(args, tmp_path, output_dir, output_filename):
    #############################
    # write header
    #############################
    HD = "\t".join(["@HD", "VN:1.4"])
    RG_parts = ["@RG"]
    for key, value in vars(args).items():
        RG_keys = ['ID', 'CN', 'DS', 'DT', 'FO', 'KS', 'LB', 'PG', 'PI', 'PL',
                   'PM', 'PU', 'SM']
        if key in RG_keys and value is not None:
            if key == "DT":
                RG_parts.append(":".join([key, to_iso8601(value)]))
            else:
                RG_parts.append(":".join([key, value]))
    RG = "\t".join(RG_parts)
    CO = "\n".join(["\t".join(["@CO", key_val]) for key_val in args.CO])
    formatted_header = "\n".join([HD, RG, CO])

    # write header to tmp file
    tmp_header_file = os.path.join(tmp_path, "header.txt")
    with open(tmp_header_file, 'w') as f:
        f.write(formatted_header)
        f.close()

    #############################
    # convert fastq to bam
    #############################
    tmp_bam = os.path.join(tmp_path, "tmp.bam")

    base_cmd = ["fastqtobam", "I={0}".format(args.fastq_1)]

    if args.fastq_2 is not None:
        base_cmd.append("I={0}".format(args.fastq_2))

    if args.is_gz == "True":
        base_cmd.append("gz=1")

    if args.checkquality == "False":
        base_cmd.append("checkquality=0")

    for key, value in vars(args).items():
        valid_args = ['qualityoffset', 'qualitymax', 'namescheme']
        if key in valid_args and value is not None:
            base_cmd.append("{0}={1}".format(key, value))

    base_cmd.append("> {0}".format(tmp_bam))
    cmd = " ".join(base_cmd)
    execute(cmd)

    #############################
    # replace header with PCAWG
    # style header
    #############################
    base_cmd = "cat %s | bamreset resetheadertext=%s > %s"
    cmd = base_cmd % (tmp_bam,
                      tmp_header_file,
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

    if args.CO is None:
        fastq2bam(args, output_dir, output_filename)
    else:
        # setup tmp output directory to store intermediate files
        tmp_output_dir = id_generator()
        tmp_path = os.path.join(output_dir, tmp_output_dir)
        if not os.path.isdir(tmp_path):
            execute("mkdir -p {0}".format(tmp_path))
        try:
            fastq2bam_2step(args, tmp_path, output_dir, output_filename)
        except Exception:
            raise
        finally:
            # cleanup
            shutil.rmtree(tmp_path)

if __name__ == "__main__":
    main()
