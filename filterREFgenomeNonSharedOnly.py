#!/usr/bin/env python2
'''
This script filters two genomes reference by keeping only fixed differences.

datafile:

#CHROM  POS Species1  Species2
scaffold_1  519 G GTTCGTCCCGTGTGAGTTCTCATTCAGCCATATTGTCAACTAACTCTGCGATATTCTTCACTC
scaffold_1  528 * A,G
scaffold_1  531 * C,T
scaffold_1  574 * C,T
scaffold_1  580 * A,T
scaffold_1  585 C C,G
scaffold_1  619 TA  T
scaffold_1  640 T A,T
scaffold_1  641 A A,T
scaffold_1  644 A A,G
scaffold_1  647 C,G A

outfile:

scaffold_1  519 G GTTCGTCCCGTGTGAGTTCTCATTCAGCCATATTGTCAACTAACTCTGCGATATTCTTCACTC
scaffold_1  528 * A,G
scaffold_1  531 * C,T
scaffold_1  574 * C,T
scaffold_1  580 * A,T
scaffold_1  619 TA  T
scaffold_1  647 C,G A

command:
$ python filterREFgenomeNonSharedOnly.py -i datafile -o outfile

contact Dmytro Kryvokhyzha dmytro.kryvokhyzha@evobio.eu
'''

import argparse, sys, re, collections

############################ options ##############################

class CommandLineParser(argparse.ArgumentParser): 
   def error(self, message):
      sys.stderr.write('error: %s\n' % message)
      self.print_help()
      sys.exit(2)

parser = CommandLineParser()
parser.add_argument('-i', '--input', help = 'name of the input file', type=str, required=True)
parser.add_argument('-o', '--output', help = 'name of the output file', type=str, required=True)
args = parser.parse_args()

############################ script ##############################

counter = 0

print('Opening the file...')
with open(args.input) as datafile:
  header_line = datafile.readline()
  print('Creating the output file...')
  output = open(args.output, 'w')
  output.write(header_line)
  
  for line in datafile:
    words = line.split()
    GT1 = words[2].split(",")
    GT2 = words[3].split(",")
    
    # check if there is overlap between two genomes
    if not(bool(set(GT1) & set(GT2))): 
      output.write(line)
      
    # track the progress:  
    counter += 1
    if counter % 1000000 == 0:
      print str(counter), "lines processed"

datafile.close()
output.close()
print('Done!\n')
