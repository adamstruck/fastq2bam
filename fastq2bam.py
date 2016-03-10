#!/usr/bin/env python

from __future__ import print_function

import argparse
import logging
import os
import random
import re
import shutil
import string
import subprocess


def collect_args():
    descr = 'Convert fastq files to unaligned BAM file with PCAWG style header'
    parser = argparse.ArgumentParser(
        description=descr
    )
    parser.add_argument("--fastq_1",
                        required=True,
                        help="fastq file")
    parser.add_argument("--fastq_2",
                        required=True,
                        help="fastq mate file")
    parser.add_argument("--output-file", dest="output_file",
                        help="unaligned BAM output")
    parser.add_argument("--ID",
                        help="<centre_name>:<unique_text>")
    parser.add_argument("--CN",
                        help="<centre_name>")
    parser.add_argument("--DT",
                        help="YYYY-MM-DD'T'HH24:MI:SS.FFTZR")
    parser.add_argument("--LB",
                        help="WGS:<center_name>:<lib_id>")
    parser.add_argument("--PI", type=int,
                        help="predicted median insert size")
    parser.add_argument("--PL", default="ILLUMINA",
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
    parser.add_argument("--CO", action='append',
                        help="provide key value pairs for sample tracking data: \
                        dcc_project_code, submitter_donor_id, \
                        submitter_specimen_id, submitter_sample_id, \
                        dcc_specimen_type, use_cntl")
    return parser


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def execute(cmd):
    logging.info("RUNNING: %s" % (cmd))
    print("RUNNING...\n", cmd, "\n")
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if stderr is not None:
        print(stderr)
    if stdout is not None:
        print(stdout)
    return p.returncode


def fastq2bam():
    parser = collect_args()
    args = parser.parse_args()

    if args.output_file is None:
        args.output_file = re.sub("(\_[0-9]\.fastq|\_[0-9]\.fq|)",
                                  "",
                                  os.path.basename(args.fastq_1)) + ".bam"

    # setup tmp output directory to store intermediate files
    tmp_output_dir = id_generator()
    output_dir = os.path.dirname(os.path.abspath(args.output_file))
    global tmp_path
    tmp_path = os.path.join(output_dir, tmp_output_dir)
    if os.path.isdir(tmp_path):
        pass
    else:
        os.mkdir(tmp_path)

    #############################
    # write header
    #############################
    HD = "\t".join(["@HD", "VN:1.4"])
    # TODO: DT format validation
    RG_parts = ["@RG"]
    for key, value in vars(args).items():
        if key not in ['fastq_1', 'fastq_2', 'output_file', 'map', 'CO'] and value is not None:
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
    cmd = base_cmd % (tmp_bam, tmp_header_file, args.output_file, args.output_file)
    execute(cmd)

if __name__ == "__main__":
    fastq2bam()
    # cleanup
    shutil.rmtree(tmp_path)
