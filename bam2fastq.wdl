task bam2fastq {
     String bam    
     String output_dir

     command {
         bamtofastq exclude=SECONDARY,SUPPLEMENTARY,QCFAIL \
         filename=${bam} \
         inputformat=bam \
         collate=1 \
         outputperreadgroup=1 \
         outputdir=${output_dir} \
         tryoq=1
     }

     output {
        Array[String] fastq = glob("${output_dir}/*.fastq")
     }

     runtime {
         docker: "fastq2bam"
     }
}

workflow bam2fastq {
    call bam2fastq
}
