task fastq2bam {
     String fastq_1
     String? fastq_2
     String is_gzipped
     String? checkquality
     String? qualityoffset
     Int? qualitymax
     String? output_dir
     String? output_filename
     String ID
     String? CN
     String? DS
     String? DT
     String? FO
     String? KS
     String LB
     String? PG
     String? PI
     String PL
     String? PM
     String? PU
     String SM

     command {
         python fastq2bam.py \
             --fastq_1 ${fastq_1} \
             ${'--fastq_2 ' + fastq_2} \
             --is-gz ${is_gzipped} \
             ${'--checkquality ' + checkquality} \
             ${'--qualityoffset ' + qualityoffset} \
             ${'--qualitymax ' + qualitymax} \
             ${'--output-filename ' + output_filename} \
             ${'--output-dir ' + output_dir} \
             --ID ${ID} \
             ${'--CN ' + CN} \
             ${'--DS ' + DS} \
             ${'--DT ' + DT} \
             ${'--FO ' + FO} \
             ${'--KS ' + KS} \
             --LB ${LB} \
             ${'--PG ' + PG} \
             ${'--PI ' + PI} \
             --PL ${PL} \
             ${'--PM ' + PM} \
             ${'--PU ' + PU} \
             --SM ${SM}
     }

     output {
        String unaligned_bam = "${output_file}"
     }

     runtime {
         docker: "biobambam"
     }
}

workflow fastq2bam {
    call fastq2bam
}
