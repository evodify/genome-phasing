# Genome phasing
This is a pipeline to phase a genome into two homeologous subgenomes. Parental genomes are required.

The phasing is performed in two stages:

1. Generate phased haplotype blocks using [HapCUT](https://github.com/vibansal/hapcut)
2. Merge haplotype blocks into two continuous strings.

Preparing reference parental genomes performed as an intermediate step. 

Required files:  

1) VCF file with samples to phase  
2) BAM files for samples to phase  
3) VCF file with parental genomes  
4) FASTA file with a reference genome  

## Generate phased haplotype blocks using HapCUT

### Select a sample from a multisample VCF
Can be performed with [GATK](https://software.broadinstitute.org/gatk/gatkdocs/org_broadinstitute_gatk_tools_walkers_variantutils_SelectVariants.php) :
```
java -Xmx8g -jar GenomeAnalysisTK.jar \
  -T SelectVariants \
  -R reference.fa \
  -V multiple_sample.vcf \
  -sn sample1 \
  -o sample1.vcf
```

### Run HapCUT

In my experience, phasing SNPs-only data produced haplotypes that were more consistent with parental reference genomes than phasing both SNPs and indels. If indels information is not required, I recommend using only SNPs data.

```
extractHAIRS --VCF sample1.vcf --bam sample1.bam --maxmem 128000 --mbq 20 --mmq 30 --PEonly 1 > sample1.fragment_matrix
HAPCUT --fragments sample1.fragment_matrix --VCF sample1.vcf --output sample1.haplotype --maxiter 100 --maxmem 128000  > sample1.haplotype.log
```
To include indels, add to `extractHAIRS` command above the following options: `--ref reference.fa --indels 1`

## Generate parental reference genomes

### Convert VCF to tab-deilimited table

Performed with [GATK](https://software.broadinstitute.org/gatk/gatkdocs/org_broadinstitute_gatk_tools_walkers_variantutils_VariantsToTable.php) :
```
java -Xmx8g -jar GenomeAnalysisTK.jar \
 -T VariantsToTable \
 -R reference.fa \
 -V reference_genomes_GT.vcf \
 -F CHROM -F POS -F REF -F ALT -GF GT \
 -o reference_genomes_GT.table
```
`multiple_sample.vcf` should also be converted to `multiple_sample_GT.table` using this approach.

### Make reference file
```
python createREFgenomesForPhasing.py -i reference_genomes_GT.table -o reference_genomes_REF.tab -s1 parent1_1,parent1_2 -s2 parent2_1,parent2_2  -m 0.25
```
### Keep fixed differences only
```
python filterREFgenomeFixedOnly.py -i reference_genomes_REF.tab -o reference_genomes_REF.fixedOnly.tab
```
## Merge haplotype blocks
```
python assign_HapCUT_blocks.py -i sample1.haplotype -r reference_genomes_REF.fixedOnly.tab -o sample1.haplotype.PHASED
```
Chimeric blocks (the phasing state was supported by less than 90% of sites) were set to missing data.

### Merge heterozygous and homozygous sites

`sample1.haplotype.PHASED.tab` contains only heterozygous sites of sample1. However, originally sample1 also contained homozygous sites that were polymorphic in other samples. These homozygous sites need to be returned.
Phasing introduce some amount of missing data. To keep balance between missing data between homozygous and heterozygous sites, amount of introduced Ns need to be assessed and the same amount of Ns should be introduced to homozygous sites.
#### Estimate the reduction heterozygous fraction
##### Count heterozygous and homozygouse sites in original file
`n` should be replaced with number of samples + 3:
```
# homozygotsOriginal:
for i in {4..n}; do cut -f $i multiple_sample_GT.table | sed 's/\// /g;s/\./N/g' | awk '$1==$2 {print $0}' | grep -vc N; done
# heterozygotsOriginal:
for i in {4..n}; do cut -f $i multiple_sample_GT.table | sed 's/\// /g;s/\./N/g' | awk '$1!=$2 {print $0}' | grep -vc N; done
```
##### Count heterozygous and homozygouse sites in phased files
```
# homozygotsPhased:
for i in *GTblock.PHASED.tab; do awk '$3==$4 {print $3,$4}' $i | grep -cv N; done
# heterozygotsPhased:
for i in *GTblock.PHASED.tab; do awk '$3!=$4 {print $3,$4}' $i | grep -cv N; done
```
#### Estimate the missing data correction value.

homozygotsReduction = heterozygotsOriginal - heterozygotsPhased
CorrectionValue = homozygotsReduction-0.04  (0.04 was cchosen empirically because some Ns are introduced to homozygots in discarded all-Ns blocks)

#### Merge with introduction of Ns
```
python mergePhasedHeteroHomo_randomNs.py -p sample1.haplotype.PHASED -g multiple_sample_GT.table -o sample1.haplotype.PHASED.tab -Np 0.16
```
### Merge all phased files togather

### Merge phased SNPs with whole genome (optional)

```
python mergePHASEDsnps_withWholeGenome.py -p merged/all.GTblock.PHASED.tab -g /media/dmykr161/WD-4TB1/data/EBC/GVCF/HaplotypeCaller/all-sites/GVCF31all_REF_heter.DP6-100.calls.tab -o all.GTblock.PHASED.wholeGenome.tab -Np 0.16
```
Again, missing data is a problem here. Phasing introduced some amount of Ns, so this needs to be taken into account during merging with whole genome. CorrectionValue (0.16) is also used here. Unphased heterozygous sites are also set to Ns. 

**Note!** Check the ratio between polymorphic and non-polymorphic sites before and after phasing. It should be the same. If it is not, modify CorrectionValue until you get the same proportion. Artificially changing polymorphic/non-polymorphic ration can biase results in some subsequent analyses.
