task fastq2bam {
     String fastq_1
     String fastq_2
     String output_file
     String ID
     String CN
     String DT
     String LB
     String PI
     String PL
     String PM
     String PU
     String SM
     Array[String] CO

     command {
         python fastq2bam.py \
             --fastq_1 ${fastq_1} \
             --fastq_2 ${fastq_2} \
             --output-file ${output_file} \
             --ID ${ID} \
             --CN ${CN} \
             --DT ${DT} \
             --LB ${LB} \
             --PI ${PI} \
             --PL ${PL} \
             --PM ${PM} \
             --PU ${PU} \
             --SM ${SM} \
             --CO ${sep='--CO ' CO}
     }

     output {
        String unaligned_bam = "${output_file}"
     }

     runtime {
         docker: "fastq2bam"
     }
}

workflow fastq2bam {
    call fastq2bam
}
