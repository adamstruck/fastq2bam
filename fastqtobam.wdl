task fastq2bam {
     String fastq_1
     String? fastq_2
     Int is_gzipped
     String namescheme
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
         fastqtobam \
             verbose=1 \
             I=${fastq_1} \
             ${'I=' + fastq_2} \
             gz=${is_gzipped} \
             namescheme=${namescheme} \ 
             ${'checkquality=' + checkquality} \
             ${'qualityoffset=' + qualityoffset} \
             ${'qualitymax=' + qualitymax} \
             RGID=${ID} \
             ${'RGCN=' + CN} \
             ${'RGDS=' + DS} \
             ${'RGDT=' + DT} \
             ${'RGFO=' + FO} \
             ${'RGKS=' + KS} \
             RGLB=${LB} \
             ${'RGPG=' + PG} \
             ${'RGPI=' + PI} \
             RGPL=${PL} \
             ${'RGPM=' + PM} \
             ${'RGPU=' + PU} \
             RGSM=${SM} \
             > ${output_dir}/${output_filename}
     }

     output {
        String unaligned_bam = "${output_dir}/${output_filename}"
     }

     runtime {
         docker: "biobambam2"
     }
}

workflow fastq2bam {
    call fastq2bam
}
