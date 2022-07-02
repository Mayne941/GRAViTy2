#!/usr/bin/env python2.7
from app.src.read_genome_desc_table import ReadGenomeDescTable
from app.src.pphmmdb_construction import PPHMMDBConstruction
from app.src.ucf_virus_annotator import UcfVirusAnnotator
from app.src.virus_classification import VirusClassificationAndEvaluation

from app.utils.check_input import check_FILEPATH, check_FILEPATHS, check_PERCENT, check_PROB, check_POS, check_POSINTEGER, check_NONNEG, check_NONNEGINTEGER, check_NONPOS, check_N_AlignmentMerging
from app.utils.str_to_bool import str2bool

import optparse, os, multiprocessing

import textwrap
class IndentedHelpFormatterWithNL(optparse.IndentedHelpFormatter):
	def format_description(self, description):
		if not description: return ""
		desc_width = self.width - self.current_indent
		indent = " "*self.current_indent
		# the above is still the same
		bits = description.split('\n')
		formatted_bits = [
			textwrap.fill(bit,
				desc_width,
				initial_indent=indent,
				subsequent_indent=indent)
			for bit in bits]
		result = "\n".join(formatted_bits) + "\n"
		return result
	
	def format_option(self, option):
		# The help for each option consists of two parts:
		#	 * the opt strings and metavars
		#	 eg. ("-x", or "-fFILENAME, --file=FILENAME")
		#	 * the user-supplied help string
		#	 eg. ("turn on expert mode", "read data from FILENAME")
		#
		# If possible, we write both of these on the same line:
		#	 -x		turn on expert mode
		#
		# But if the opt string list is too long, we put the help
		# string on a second line, indented to the same column it would
		# start in if it fit on the first line.
		#	 -fFILENAME, --file=FILENAME
		#			 read data from FILENAME
		result = []
		opts = self.option_strings[option]
		opt_width = self.help_position - self.current_indent - 2
		if len(opts) > opt_width:
			opts = "%*s%s\n" % (self.current_indent, "", opts)
			indent_first = self.help_position
		else: # start help on same line as opts
			opts = "%*s%-*s	" % (self.current_indent, "", opt_width, opts)
			indent_first = 0
		result.append(opts)
		if option.help:
			help_text = self.expand_default(option)
			# Everything is the same up through here
			help_lines = []
			for para in help_text.split("\n"):
				help_lines.extend(textwrap.wrap(para, self.help_width))
			# Everything is the same after here
			result.append("%*s%s\n" % (
				indent_first, "", help_lines[0]))
			result.extend(["%*s%s\n" % (self.help_position, "", line)
				for line in help_lines[1:]])
		elif opts[-1] != "\n":
			result.append("\n")
		return "".join(result)

def main ():
	parser = optparse.OptionParser(	usage = "usage: %prog [options]",
					version = "%prog 1.1.0",
					formatter = IndentedHelpFormatterWithNL())
	
	parser.add_option(	'--GenomeDescTableFile_UcfVirus',
				dest 	= "GenomeDescTableFile_UcfVirus",
				help 	= "Full path to the Virus Metadata Resource-like (VMR-like) tab delimited file of unclassified viruses, wth headers. "
					  "VMR can be downloaded from https://talk.ictvonline.org/taxonomy/vmr/",
				metavar	= "FILEPATH",
				type	= "string",
				action	= "callback",
				callback= check_FILEPATH,
	)
	parser.add_option(	'--ShelveDir_UcfVirus',
				dest	= "ShelveDir_UcfVirus",
				help	= "Full path to the shelve directory of unclassified viruses, storing GRAViTy outputs.",
				metavar	= "DIRECTORYPATH",
				type	= "string",
	)
	parser.add_option(	'--ShelveDirs_RefVirus',
				dest	= "ShelveDirs_RefVirus",
				help	= "Full path(s) to the shelve director(y/ies) of reference virus(es). "
					  "For example: 'path/to/shelve/ref1, path/to/shelve/ref2, ...'",
				metavar	= "DIRECTORYPATH",
				type	= "string",
	)
	
	parser.add_option(	'--Database',
				dest	= "Database",
				default	= None,
				help	= "GRAViTy will only analyse genomes that are labelled with DATABASE in the database column. "
					  "The database column can be specified by the DATABASE HEADER argument. "
					  "If 'None', all entries are analysed. [default: %default]",
				metavar	= "DATABASE",
				type	= "string",
	)
	parser.add_option(	'--Database_Header',
				dest	= "Database_Header",
				default	= None,
				help	= "The header of the database column. Cannot be 'None' if DATABASE is specified. [default: %default]",
				metavar	= "DATABASE COLUMN HEADER",
				type	= "string",
	)
	'''
	parser.add_option(	'--TaxoGrouping_Header',
				dest	= "TaxoGrouping_Header",
				default	= "Family",
				help	= "The header of the Taxonomic grouping column. [default: %default]",
				metavar	= "TAXOGROUPING COLUMN HEADER",
				type	= "string",
	)
	parser.add_option(	'--TaxoGroupingFile',
				dest 	= "TaxoGroupingFile",
				default	= None,
				help 	= "It is possible that the user might want to associate different viruses with different taxonomic assignment levels, "
					  "e.g. family assignments for some viruses, and subfamily or genus assignments for some other viruses, etc. "
					  "To accomodate this need, the user can either add a column in the VMR file, and use --TaxoGrouping_Header to specify the column (see --TaxoGrouping_Header). "
					  "Alternatively, the user can provide a file (with no header) that contains a single column of taxonomic groupings for all viruses in the order that appears in the VMR file. "
					  "The user can specify the full path to the taxonomic grouping file using this options. "
					  "If this option is used, it will override the one specified by --TaxoGrouping_Header. [default: %default]",
				metavar	= "FILEPATH",
				type	= "string",
				action	= "callback",
				callback= check_FILEPATH,
	)
	'''
	parser.add_option(	'--GenomeSeqFile_UcfVirus',
				dest	= "GenomeSeqFile_UcfVirus",
				help	= "Full path to the genome sequence GenBank file of unclassified viruses.",
				metavar	= "FILEPATH",
				type	= "string",
				#action	= "callback",
				#callback= check_FILEPATH,
	)
	parser.add_option(	'--UseUcfVirusPPHMMs',
				dest	= "UseUcfVirusPPHMMs",
				default	= True,
				help	= "Annotate reference and unclassified viruses using the PPHMM database derived from unclassified viruses if True. [default: %default]",
				metavar	= "BOOLEAN",
				type	= "choice",
				choices	= ["True", "False",],
	)
	parser.add_option(	'--GenomeSeqFiles_RefVirus',
				dest	= "GenomeSeqFiles_RefVirus",
				default	= None,
				help	= "Full path(s) to the genome sequence GenBank file(s) of reference viruses. "
					  "For example: 'path/to/GenBank/ref1, path/to/GenBank/ref2, ...' "
					  "This cannot be 'None' if UseUcfVirusPPHMMs = True. ",
				metavar	= "FILEPATH",
				type	= "string",
				action	= "callback",
				callback= check_FILEPATHS,
	)
	
	ProtExtractionGroup 	= optparse.OptionGroup(	parser		= parser,
							title		= "Protein extraction options",
							description	= "Protein sequences are extracted from the genome sequence GenBank File. "
									  "If the file contains protein sequences, GRAViTy will use those annotations. "
									  "Otherwise, protein sequences will be inferred using the genetic code specified in the VMR file, 'Genetic code table' column")
	ProtExtractionGroup.add_option(	'--ProteinLength_Cutoff',
					dest	= "ProteinLength_Cutoff",
					default	= 100,
					help	= "Proteins with length < LENGTH aa will be ignored [default: %default]",
					metavar	= "LENGTH",
					type	= "int",
					action	= "callback",
					callback= check_NONNEGINTEGER,
	)
	ProtExtractionGroup.add_option(	'--IncludeProteinsFromIncompleteGenomes',
					dest	= "IncludeProteinsFromIncompleteGenomes",
					default	= True,
					help	= "Include protein sequences from incomplete genomes to the database if True. [default: %default]",
					metavar	= "BOOLEAN",
					type	= "choice",
					choices	= ["True", "False",],
	)
	parser.add_option_group(ProtExtractionGroup)
	
	ProtClusteringGroup	= optparse.OptionGroup( parser		= parser,
							title		= "Protein clustering options",
							description	= "Protein sequences are clustered based on ALL-VERSUS-ALL BLASTp hit scores. "
									  "In summary, a protein database is constructed, and all protein sequences (queries) are searched against the database one by one using BLASTp. "
									  "Protein-protein pairwise similarity scores (bit scores) are collected, and subsequently used for protein clustering by the MCL algorithm. "
									  "Sequneces in each cluster are then aligned by using MUSCLE, and turned into a protein profile hidden Markov model (PPHMM).")
	ProtClusteringGroup.add_option(	'--BLASTp_evalue_Cutoff',
					dest	= "BLASTp_evalue_Cutoff",
					default	= 1E-3,
					help	= "Threshold for protein sequence similarity detection. "
						  "A hit with an E-value > E-VALUE will be ignored. [default: %default]",
					metavar	= "E-VALUE",
					type	= "float",
					action	= "callback",
					callback= check_POS,
	)
	ProtClusteringGroup.add_option(	'--BLASTp_PercentageIden_Cutoff',
					dest	= "BLASTp_PercentageIden_Cutoff",
					default	= 50,
					help	= "Threshold for protein sequence similarity detection. "
						  "A hit with a percentage identity < PERCENTAGE IDENTITY will be ignored. [default: %default]",
					metavar	= "PERCENTAGE IDENTITY",
					type	= "float",
					action	= "callback",
					callback= check_PERCENT,
	)
	ProtClusteringGroup.add_option(	'--BLASTp_QueryCoverage_Cutoff',
					dest	= "BLASTp_QueryCoverage_Cutoff",
					default	= 75,
					help	= "Threshold for protein sequence similarity detection. "
						  "A hit with a query coverage < COVERAGE will be ignored. [default: %default]",
					metavar	= "COVERAGE",
					type	= "float",
					action	= "callback",
					callback= check_PERCENT,
	)
	ProtClusteringGroup.add_option(	'--BLASTp_SubjectCoverage_Cutoff',
					dest	= "BLASTp_SubjectCoverage_Cutoff",
					default	= 75,
					help	= "Threshold for protein sequence similarity detection. "
						  "A hit with a subject coverage < COVERAGE will be ignored. [default: %default]",
					metavar	= "COVERAGE",
					type	= "float",
					action	= "callback",
					callback= check_PERCENT,
	)
	ProtClusteringGroup.add_option(	'--BLASTp_num_alignments',
					dest	= "BLASTp_num_alignments",
					default	= 1000000,
					help	= "Maximum number of sequences to be considered in a BLASTp search. [default: %default]",
					metavar	= "BLAST ALIGNMENT NUMBER",
					type	= "int",
					action	= "callback",
					callback= check_POSINTEGER,
	)
	ProtClusteringGroup.add_option(	'--BLASTp_N_CPUs',
					dest	= "BLASTp_N_CPUs",
					default	= multiprocessing.cpu_count(),
					help	= "The number of threads (CPUs) to use in the BLASTp search. [default: %default - all threads]",
					metavar	= "THREADS",
					type	= "int",
					action	= "callback",
					callback= check_POSINTEGER,
	)
	
	ProtClusteringGroup.add_option(	'--MUSCLE_GapOpenCost',
					dest	= "MUSCLE_GapOpenCost",
					default	= -3.0,
					help	= "MUSCLE gap opening panelty for aligning protein sequences. [default: %default]",
					metavar	= "gap opening panelty",
					type	= "float",
					action	= "callback",
					callback= check_NONPOS,
	)
	ProtClusteringGroup.add_option(	'--MUSCLE_GapExtendCost',
					dest	= "MUSCLE_GapExtendCost",
					default	= -0.00,
					help	= "MUSCLE gap extension panelty for aligning protein sequences. [default: %default]",
					metavar	= "gap extension panelty",
					type	= "float",
					action	= "callback",
					callback= check_NONPOS,
	)
	
	ProtClusteringGroup.add_option(	'--ProtClustering_MCLInflation',
					dest	= "ProtClustering_MCLInflation",
					default	= 2,
					help	= "Cluster granularity. Increasing INFLATION will increase cluster granularity. [default: %default]",
					metavar	= "INFLATION",
					type	= "float",
					action	= "callback",
					callback= check_POS,
	)
	parser.add_option_group(ProtClusteringGroup)
	
	MergingProtAlnsGroup	= optparse.OptionGroup( parser		= parser,
							title		= "Protein alignment merging options",
							description	= "Protein alignments can be merged to reduce the number of protein profile hidden markov models (PPHMMs) in the PPHMM database. "
									  "In summary, a database of PPHMMs is constructed, and all PPHMMs (queries) are searched against the database one by one using HHsuite (hhsearch, see 'HHsuite options' for more options). "
									  "PPHMM-PPHMM pairwise similarity scores are collected, and subsequently used for PPHMM clustering by MCL algorithm. "
									  "Sequneces in the same PPHMM cluster are then re-aligned using MUSCLE.")
	MergingProtAlnsGroup.add_option('--N_AlignmentMerging',
					dest	= "N_AlignmentMerging",
					default	= 0,
					help	= "Number of rounds of alignment merging. ROUND == 0 means no merging. ROUND == -1 means merging until exhausted. [default: %default]",
					metavar	= "ROUND",
					type	= "int",
					action	= "callback",
					callback= check_N_AlignmentMerging,
	)
	
	MergingProtAlnsGroup.add_option('--PPHMMClustering_MCLInflation_ForAlnMerging',
					dest	= "PPHMMClustering_MCLInflation_ForAlnMerging",
					default	= 5,
					help	= "Cluster granularity. Increasing INFLATION will increase cluster granularity. [default: %default]",
					metavar	= "INFLATION",
					type	= "float",
					action	= "callback",
					callback= check_POS,
	)
	
	MergingProtAlnsGroup.add_option('--HMMER_PPHMMDB_ForEachRoundOfPPHMMMerging',
					dest	= "HMMER_PPHMMDB_ForEachRoundOfPPHMMMerging",
					default	= True,
					help	= "Make a HMMER PPHMM DB for each round of protein merging if True. [default: %default]",
					metavar	= "BOOLEAN",
					type	= "choice",
					choices	= ["True", "False",],
	)
	parser.add_option_group(MergingProtAlnsGroup)
	
	HHsuiteGroup	= optparse.OptionGroup( parser		= parser,
						title		= "HHsuite options",
						description	= "HHsuite (hhsearch) is used to search PPHMMs against a database of PPHMMs. "
								  "Here are some options regarding hhsearch. ")
	HHsuiteGroup.add_option('--HHsuite_evalue_Cutoff',
				dest	= "HHsuite_evalue_Cutoff",
				default	= 1E-6,
				help	= "Threshold for PPHMM similarity detection. "
					  "A hit with an E-value > E-VALUE will be ignored. [default: %default]",
				metavar = "E-VALUE",
				type	= "float",
				action	= "callback",
				callback= check_POS,
	)
	HHsuiteGroup.add_option('--HHsuite_pvalue_Cutoff',
				dest	= "HHsuite_pvalue_Cutoff",
				default	= 0.05,
				help	= "Threshold for PPHMM similarity detection. "
					  "A hit with a p-value > P-VALUE will be ignored. [default: %default]",
				metavar	= "P-VALUE",
				type	= "float",
				action	= "callback",
				callback= check_PROB,
	)
	HHsuiteGroup.add_option('--HHsuite_N_CPUs',
				dest	= "HHsuite_N_CPUs",
				default	= multiprocessing.cpu_count(),
				help	= "Number of threads (CPUs) to use in the hhsearch search. [default: %default - all threads]",
				metavar	= "THREADS",
				type	= "int",
				action	= "callback",
				callback= check_POSINTEGER,
	)
	HHsuiteGroup.add_option('--HHsuite_QueryCoverage_Cutoff',
				dest	= "HHsuite_QueryCoverage_Cutoff",
				default	= 85,
				help	= "Threshold for PPHMM similarity detection. "
					  "A hit with a query coverage < COVERAGE will be ignored [default: %default]",
				metavar	= "COVERAGE",
				type	= "float",
				action	= "callback",
				callback= check_PERCENT,
	)
	HHsuiteGroup.add_option('--HHsuite_SubjectCoverage_Cutoff',
				dest	= "HHsuite_SubjectCoverage_Cutoff",
				default	= 85,
				help	= "Threshold for PPHMM similarity detection. "
					  "A hit with a subject coverage < COVERAGE will be ignored [default: %default]",
				metavar	= "COVERAGE",
				type	= "float",
				action	= "callback",
				callback= check_PERCENT,
	)
	parser.add_option_group(HHsuiteGroup)
	
	VirusAnnotationUsingRefDBGroup 	= optparse.OptionGroup(	parser		= parser,
								title		= "Unclassified virus annotation options",
								description	= "Virus genomes are 6-framed translated and are scanned against the reference PPHMM database(s), using HMMER (hmmscan). "
										  "Two types of information are collected: PPHMM hit scores (PPHMM signatures) and hit locations (PPHMM LOCATION signatures). ")
	
	VirusAnnotationUsingRefDBGroup.add_option('--AnnotateIncompleteGenomes_UcfVirus',
					dest	= "AnnotateIncompleteGenomes_UcfVirus",
					default	= True,
					help	= "Annotate all unclassified viruses using reference PPHMM database(s) if True, otherwise only complete genomes. [default: %default]",
					metavar	= "BOOLEAN",
					type	= "choice",
					choices	= ["True", "False",],
	)
	VirusAnnotationUsingRefDBGroup.add_option('--UsingDatabaseIncludingIncompleteRefViruses',
					dest	= "UsingDatabaseIncludingIncompleteRefViruses",
					default	= False,
					help	= "Annotate unclassified viruses using the PPHMM and GOM databases derived from all reference viruses if True, "
						  "otherwise using those derived from complete reference genomes only. [default: %default]",
					metavar	= "BOOLEAN",
					type	= "choice",
					choices	= ["True", "False",],
	)
	#VirusAnnotationUsingRefDBGroup.add_option('--SeqLength_Cutoff',
	#				dest	= "SeqLength_Cutoff",
	#				default	= 0,
	#				help	= "Sequences with length < LENGTH nt will be ignored [default: %default]",
	#				metavar	= "LENGTH",
	#				type	= "int",
	#				action	= "callback",
	#				callback= check_NONNEGINTEGER,
	#)
	parser.add_option_group(VirusAnnotationUsingRefDBGroup)
	
	HMMERGroup	= optparse.OptionGroup( parser		= parser,
						title		= "HMMER options",
						description	= "HMMER (hmmscan) is used to search virus (translated) genomes against a database of PPHMMs. "
								  "Here are some options regarding hmmscan. ")
	
	HMMERGroup.add_option(	'--HMMER_N_CPUs',
				dest	= "HMMER_N_CPUs",
				default	= multiprocessing.cpu_count(),
				help	= "Number of threads (CPUs) to use in the hmmscan search. [default: %default - all threads]",
				metavar	= "THREADS",
				type	= "int",
				action	= "callback",
				callback= check_POSINTEGER,
	)
	HMMERGroup.add_option(	'--HMMER_C_EValue_Cutoff',
				dest	= "HMMER_C_EValue_Cutoff",
				default	= 1E-3,
				help	= "Threshold for HMM-protein similarity detection. "
					  "A hit with an E-value > E-VALUE will be ignored. [default: %default]",
				metavar	= "E-VALUE",
				type	= "float",
				action	= "callback",
				callback= check_POS,
	)
	HMMERGroup.add_option(	'--HMMER_HitScore_Cutoff',
				dest	= "HMMER_HitScore_Cutoff",
				default	= 0,
				help	= "Threshold for HMM-protein similarity detection. "
					  "A hit with a score < SCORE will be ignored. [default: %default]",
				metavar	= "SCORE",
				type	= "float",
				action	= "callback",
				callback= check_NONNEG,
	)	
	parser.add_option_group(HMMERGroup)
	
	SimilarityMeasurementGroup = optparse.OptionGroup(	parser		= parser,
								title		= "Virus (dis)similarity measurement options",
								description	= "Unlike in many traditional approaches that represent a virus using its molecular sequences, "
										  "in GRAViTy, a virus is represented by 3 signatures: a PPHMM signature, a PPHMM LOCATION signature, and a GOM signature. "
										  "For each virus pair, generalised Jaccard similarity scores (GJ) between their PPHMM signatures (GJ_P), PPHMM LOCATION signatures (GJ_L), and GOM signatures (GJ_G) are computed. "
										  "An overall similarity between a pair of viruses is computed based on these 3 quantities. "
										  "Various schemes of overall similarity measurement are implemented in GRAViTy, specified by using 'SimilarityMeasurementScheme' argument. "
										  "See help text of 'SimilarityMeasurementScheme' for more details. "
										  "The degree of overall similarity (S) is ranging between 0 and 1. "
										  "An overall distance (D) between a pair of viruses is 1 - S, thus again ranging between 0 and 1."
										  "In addition, GRAViTy allows users to transform the overall distance as well, governed by parameter 'p'. "
										  "See the help text of 'p' for more details.",
										  )
	SimilarityMeasurementGroup.add_option(	'--SimilarityMeasurementScheme',
						dest	= "SimilarityMeasurementScheme",
						default	= "PG",
						help	= "Virus similarity measurement SCHEMEs. [default: %default]\n "
							  "If SCHEME = 'P', an overall similarity between two viruses is their GJ_P.\n "
							  "If SCHEME = 'L', an overall similarity between two viruses is their GJ_L.\n "
							  "If SCHEME = 'G', an overall similarity between two viruses is their GJ_G.\n "
							  "If SCHEME = 'PG', an overall similarity between two viruses is a geometric mean - or a 'composite generalised Jaccard score' (CGJ) - of their GJ_P and GJ_G.\n "
							  "If SCHEME = 'PL', an overall similarity between two viruses is a geometric mean - or a 'composite generalised Jaccard score' (CGJ) - of their GJ_P and GJ_L.",
						metavar	= "SCHEME",
						type	= "choice",
						choices	= ["P", "G", "L", "PG", "PL"],
	)
	SimilarityMeasurementGroup.add_option(	'--p',
						dest	= "p",
						default	= 1,
						help	= "Distance transformation P coefficient, 0 <= P. [default: %default]\n "
							  "D = 1 - S**P.\n "
							  "If P = 1, no distance transformation is applied.\n "
							  "If P > 1, shallow branches will be stretched out so shallow splits can be seen more clearly.\n "
							  "If p < 1, deep branches are stretch out so that deep splits can be seen more clearly.\n "
							  "If p = 0, the entire dendrogram will be reduced to a single branch (root), with all taxa forming a polytomy clade at the tip of the dendrogram.\n "
							  "If p = Inf, the resultant dendrogram will be star-like, with all taxa forming a polytomy clade at the root.",
						metavar	= "P",
						type	= "float",
						action	= "callback",
						callback= check_NONNEG,
	)
	parser.add_option_group(SimilarityMeasurementGroup)
	
	VirusClassificationGroup = optparse.OptionGroup(	parser		= parser,
								title		= "Virus classification options",
								description	= "In summary, GRAViTy proposes a candidate taxonomic group for an unclassified virus by identifying the most similar virus(es) in the refernece database(s). "
										  "To validate the candidate taxonomic assignment, GRAViTy employs two-step evaluation protocol.\n\n"
										  
										  "In the first step, GRAViTy checks whether or not the unclassified virus is 'similar enough' to the proposed candidate group, of which the CGJ similarity threshold is group specific. "
										  "To estimate the threshold for a particular taxonomic group, GRAViTy builds distributions of its inter-group and intra-group CGJ similarity scores. "
										  "GRAViTy then computes the score that best separate the two distributions using the support vector machine (SVM) algorithm. "
										  "The SVM algorithm used is implemented in SVC function, available from Scikit-learn python library, with 'balanced' class weight option. "
										  "If the observed CGJ similarity is less than the threshold, the candidate taxonomic assignment is rejected, and the sample is relabelled as 'Unclassified', "
										  "otherwise, the second step of the evaluation will be employed to further evaluate the candidate taxonomic assignment.\n\n"
										  
										  "In the second step, a dendrogram containing reference viruses and the unclassified virus is used, and the evaluator will look at its neighbourhood. "
										  "The taxonomic proposal will be accepted if any of the following conditions are met:\n"
										  "\ti)	the sister clade is composed entirely of the members of the proposed candidate taxonomic group\n"
										  "\tii)	the immediate out group is composed entirely of the members of the proposed candidate taxonomic group\n"
										  "\tiii)	one of the two basal branches of its sister clade leading to a clade that is composed entirely of the members of the proposed candidate taxonomic group\n"
										  "To best estimate the placement of viruses, if multiple unclassified viruses are to be analysed at the same time, "
										  "a dendrogram containing all unclassified viruses will be used. "
										  "Furthermore, since there can be multiple reference databases, there are possibilities that a virus might be assigned to multiple taxonomic groups belonging to different databases. "
										  "In such cases, the finalised taxonomic assignment is the one associated with the highest CGJ similarity score.\n\n"
										  
										  "GRAViTy can also perform bootstrapping to evaluate the uncertainty of the proposed taxonomic group.")
	VirusClassificationGroup.add_option(	'--Dendrogram_LinkageMethod',
						dest	= "Dendrogram_LinkageMethod",
						default	= "average",
						help	= "LINKAGE for dendrogram construction. [default: %default]\n "
							  "If LINKAGE = 'single', the nearest point algorithm is used to cluster viruses and compute cluster distances.\n "
							  "If LINKAGE = 'complete', the farthest point algorithm is used to cluster viruses and compute cluster distances.\n "
							  "If LINKAGE = 'average', the UPGMA algorithm is used to cluster viruses and compute cluster distances.\n "
							  "If LINKAGE = 'weighted', the WPGMA algorithm is used to cluster viruses and compute cluster distances.\n "
							  "If LINKAGE = 'centroid', the UPGMC algorithm is used to cluster viruses and compute cluster distances.\n "
							  "If LINKAGE = 'median', the WPGMC algorithm is used to cluster viruses and compute cluster distances.\n "
							  "If LINKAGE = 'ward', the incremental algorithm is used to cluster viruses and compute cluster distances.",
						metavar	= "LINKAGE",
						type	= "choice",
						choices	= ["single", "complete", "average", "weighted", "centroid", "median", "ward"],
	)
	VirusClassificationGroup.add_option(	'--Bootstrap',
						dest	= "Bootstrap",
						default	= True,
						help	= "Perform bootstrapping if True. [default: %default]",
						metavar	= "BOOLEAN",
						type	= "choice",
						choices	= ["True", "False",],
	)
	VirusClassificationGroup.add_option(	'--N_Bootstrap',
						dest	= "N_Bootstrap",
						default	= 10,
						help	= "The number of pseudoreplicate datasets by resampling. [default: %default]",
						metavar	= "NUMBER",
						type	= "int",
						action	= "callback",
						callback= check_POSINTEGER,
	)
	VirusClassificationGroup.add_option(	'--Bootstrap_method',
						dest	= "Bootstrap_method",
						default	= "booster",
						help	= "Two METHODs for dendrogram summary construction are implemented in GRAViTy. [default: %default] "
							  "If METHOD = 'sumtrees', SumTrees (Sukumaran, J & MT Holder, 2010, Bioinformatics; https://dendropy.org/programs/sumtrees.html) will be used to summarize non-parameteric bootstrap support for splits on the best estimated dendrogram. The calculation is based on the standard Felsenstein bootstrap method.\n "
							  "If METHOD = 'booster', BOOSTER (Lemoine et al., 2018, Nature; https://booster.pasteur.fr/) will be used. With large trees and moderate phylogenetic signal, BOOSTER tends to be more informative than the standard Felsenstein bootstrap method.",
						metavar	= "METHOD",
						type	= "choice",
						choices	= ["booster", "sumtrees"],
	)
	VirusClassificationGroup.add_option(	'--Bootstrap_N_CPUs',
						dest	= "Bootstrap_N_CPUs",
						default	= multiprocessing.cpu_count(),
						help	= "Number of threads (CPUs) to use in dendrogram summary. Only used when 'Bootstrap_method' == 'booster' [default: %default - all threads]",
						metavar	= "THREADS",
						type	= "int",
						action	= "callback",
						callback= check_POSINTEGER,
	)
	
	VirusClassificationGroup.add_option(	'--DatabaseAssignmentSimilarityScore_Cutoff',
						dest	= "DatabaseAssignmentSimilarityScore_Cutoff",
						default	= 0.01,
						help	= "Threshold to determine if the unclassified virus at least belongs to a particular database. [default: %default] "
							  "For example, an unclassified virus is assigned to the family 'X' in the reference 'Baltimore group X' database, with the (greatest) similarity score of 0.1. "
							  "This score might be too low to justify that the virus is a member of the family 'X', and fail the similarity threshold test. "
							  "However, since the similarity score of 0.1 > %default, GRAViTy will make a guess that it might still be a virus of the 'Baltimore group X' database, under the default setting.",
						metavar	= "SCORE",
						type	= "int",
						action	= "callback",
						callback= check_POS,
	)
	VirusClassificationGroup.add_option(	'--N_PairwiseSimilarityScores',
						dest	= "N_PairwiseSimilarityScores",
						default	= 10000,
						help	= "Number of data points in the distributions of intra- and inter-group similarity scores used to estimate the similarity threshold. [default: %default]",
						metavar	= "NUMBER",
						type	= "int",
						action	= "callback",
						callback= check_POSINTEGER,
	)	
	parser.add_option_group(VirusClassificationGroup)
	
	HeatmapConstructionGroup = optparse.OptionGroup(	parser		= parser,
								title		= "Heatmap construction options",
								description	= "GRAViTy can generate a heatmap (with the dendrogram) to represent the pairwise (dis)similarity matrix")
	HeatmapConstructionGroup.add_option(	'--Heatmap_WithDendrogram',
						dest	= "Heatmap_WithDendrogram",
						default	= True,
						help	= "Construct (dis)similarity heatmap with dendrogram if True. [default: %default]",
						metavar	= "BOOLEAN",
						type	= "choice",
						choices	= ["True", "False",],
	)
	HeatmapConstructionGroup.add_option(	'--Heatmap_DendrogramSupport_Cutoff',
						dest	= "Heatmap_DendrogramSupport_Cutoff",
						default	= 0.75,
						help	= "Threshold for the BOOTSTRAP SUPPORT to be shown on the dendrogram on the heatmap. [default: %default]",
						metavar	= "BOOTSTRAP SUPPORT",
						type	= "float",
						action	= "callback",
						callback= check_PROB,
	)
	parser.add_option_group(HeatmapConstructionGroup)
	
	VirusGroupingGroup = optparse.OptionGroup(	parser		= parser,
							title		= "Virus grouping options",
							description	= "GRAViTy can estimate the distance cutoff that best separates the input reference taxonomic groupings, and report virus groups suggested by the estimated cutoff. "
									  "Theil's uncertainty correlation for the reference taxonomic grouping given the predicted grouping, and vice versa, are reported. "
									  "Symmetrical Theil's uncertainty correlation between the reference and predicted taxonomic grouping are also reported.")
	VirusGroupingGroup.add_option(	'--VirusGrouping',
					dest	= "VirusGrouping",
					default	= True,
					help	= "Perform virus grouping if True. [default: %default]",
					metavar	= "BOOLEAN",
					type	= "choice",
					choices	= ["True", "False",],
	)
	parser.add_option_group(VirusGroupingGroup)
	
	options, arguments = parser.parse_args()
	
	print("Input for ReadGenomeDescTable:")
	print("="*100)
	
	print("\n")
	print("Main input")
	print("-"*50)
	print("GenomeDescTableFile_UcfVirus: %s"%options.GenomeDescTableFile_UcfVirus)
	print("ShelveDir_UcfVirus: %s"		%options.ShelveDir_UcfVirus)
	print("Database: %s"			%options.Database)
	print("Database_Header: %s"		%options.Database_Header)
	#print "TaxoGrouping_Header: %s"	%options.TaxoGrouping_Header
	#print "TaxoGroupingFile: %s"		%options.TaxoGroupingFile
	print("="*100)
	
	if (options.Database != None and options.Database_Header == None):
		raise optparse.OptionValueError("You have specified DATABASE as %s, 'Database_Header' cannot be 'None'"%options.Database)
	
	if (options.Database == None and options.Database_Header != None):
		Proceed = input ("You have specified 'Database_Header' as %s, but 'Database' is 'None'. GRAViTy will analyse all genomes. Do you want to proceed? [Y/n]: " %options.Database_Header)
		if Proceed != "Y":
			raise SystemExit("GRAViTy terminated.")
	
	if not os.path.exists(options.ShelveDir_UcfVirus):
		os.makedirs(options.ShelveDir_UcfVirus)
	
	ReadGenomeDescTable(
		GenomeDescTableFile	= options.GenomeDescTableFile_UcfVirus,
		ShelveDir		= options.ShelveDir_UcfVirus,
		Database		= options.Database,
		Database_Header		= options.Database_Header,
		#TaxoGrouping_Header	= options.TaxoGrouping_Header,
		#TaxoGroupingFile	= options.TaxoGroupingFile,
		)
	
	if str2bool(options.UseUcfVirusPPHMMs) == True:
		print("Input for PPHMMDBConstruction:")
		print("="*100)
		print("Main input")
		print("-"*50)
		print("GenomeSeqFile_UcfVirus: %s"	%options.GenomeSeqFile_UcfVirus)
		print("ShelveDir_UcfVirus: %s"		%options.ShelveDir_UcfVirus)
		
		print("\n")
		print("Protein extraction options")
		print("-"*50)
		print("ProteinLength_Cutoff: %s"	%options.ProteinLength_Cutoff)
		print("IncludeProteinsFromIncompleteGenomes: %s"%options.IncludeProteinsFromIncompleteGenomes)
		
		print("\n")
		print("Protein clustering options")
		print("-"*50)
		print("BLASTp_evalue_Cutoff: %s"	%options.BLASTp_evalue_Cutoff)
		print("BLASTp_PercentageIden_Cutoff: %s"%options.BLASTp_PercentageIden_Cutoff)
		print("BLASTp_QueryCoverage_Cutoff: %s"	%options.BLASTp_QueryCoverage_Cutoff)
		print("BLASTp_SubjectCoverage_Cutoff: %s"%options.BLASTp_SubjectCoverage_Cutoff)
		print("BLASTp_num_alignments: %s"	%options.BLASTp_num_alignments)
		print("BLASTp_N_CPUs: %s"		%options.BLASTp_N_CPUs)
		
		print("MUSCLE_GapOpenCost: %s"		%options.MUSCLE_GapOpenCost)
		print("MUSCLE_GapExtendCost: %s"	%options.MUSCLE_GapExtendCost)
		
		print("ProtClustering_MCLInflation: %s"%options.ProtClustering_MCLInflation)
		
		print("\n")
		print("Protein alignment merging options")
		print("-"*50)
		print("N_AlignmentMerging: %s"		%options.N_AlignmentMerging)
		
		print("HHsuite_evalue_Cutoff: %s"	%options.HHsuite_evalue_Cutoff)
		print("HHsuite_pvalue_Cutoff: %s"	%options.HHsuite_pvalue_Cutoff)
		print("HHsuite_N_CPUs: %s"		%options.HHsuite_N_CPUs)
		print("HHsuite_QueryCoverage_Cutoff: %s"%options.HHsuite_QueryCoverage_Cutoff)
		print("HHsuite_SubjectCoverage_Cutoff: %s"%options.HHsuite_SubjectCoverage_Cutoff)
		
		print("PPHMMClustering_MCLInflation_ForAlnMerging: %s"%options.PPHMMClustering_MCLInflation_ForAlnMerging)
		
		print("HMMER_PPHMMDB_ForEachRoundOfPPHMMMerging: %s"%options.HMMER_PPHMMDB_ForEachRoundOfPPHMMMerging)
		print("="*100)
		
		PPHMMDBConstruction (
			GenomeSeqFile = options.GenomeSeqFile_UcfVirus,
			ShelveDir = options.ShelveDir_UcfVirus,
			
			ProteinLength_Cutoff = options.ProteinLength_Cutoff,
			IncludeIncompleteGenomes = str2bool(options.IncludeProteinsFromIncompleteGenomes),
			
			BLASTp_evalue_Cutoff = options.BLASTp_evalue_Cutoff,
			BLASTp_PercentageIden_Cutoff = options.BLASTp_PercentageIden_Cutoff,
			BLASTp_QueryCoverage_Cutoff = options.BLASTp_QueryCoverage_Cutoff,
			BLASTp_SubjectCoverage_Cutoff = options.BLASTp_SubjectCoverage_Cutoff,
			BLASTp_num_alignments = options.BLASTp_num_alignments,
			BLASTp_N_CPUs = options.BLASTp_N_CPUs,
			
			MUSCLE_GapOpenCost = options.MUSCLE_GapOpenCost,
			MUSCLE_GapExtendCost = options.MUSCLE_GapExtendCost,
			
			ProtClustering_MCLInflation = options.ProtClustering_MCLInflation,
			
			N_AlignmentMerging = options.N_AlignmentMerging,
			
			HHsuite_evalue_Cutoff = options.HHsuite_evalue_Cutoff,
			HHsuite_pvalue_Cutoff = options.HHsuite_pvalue_Cutoff,
			HHsuite_N_CPUs = options.HHsuite_N_CPUs,
			HHsuite_QueryCoverage_Cutoff = options.HHsuite_QueryCoverage_Cutoff,
			HHsuite_SubjectCoverage_Cutoff = options.HHsuite_SubjectCoverage_Cutoff,
			
			PPHMMClustering_MCLInflation = options.PPHMMClustering_MCLInflation_ForAlnMerging,
			
			HMMER_PPHMMDB_ForEachRoundOfPPHMMMerging = str2bool(options.HMMER_PPHMMDB_ForEachRoundOfPPHMMMerging),
			)
	
	print("Input for UcfVirusAnnotator:")
	print("="*100)
	print("Main input")
	print("-"*50)
	print("GenomeSeqFile_UcfVirus: %s"%options.GenomeSeqFile_UcfVirus)
	print("ShelveDir_UcfVirus: %s"%options.ShelveDir_UcfVirus)
	print("ShelveDirs_RefVirus: %s"%options.ShelveDirs_RefVirus)
	
	print("\n")
	print("Unclassified virus annotation options")
	print("-"*50)
	print("AnnotateIncompleteGenomes_UcfVirus: %s"%options.AnnotateIncompleteGenomes_UcfVirus)
	print("UsingDatabaseIncludingIncompleteRefViruses: %s"%options.UsingDatabaseIncludingIncompleteRefViruses)	
	#print "SeqLength_Cutoff: %s"%options.SeqLength_Cutoff
	print("HMMER_N_CPUs: %s"%options.HMMER_N_CPUs)
	print("HMMER_C_EValue_Cutoff: %s"%options.HMMER_C_EValue_Cutoff)
	print("HMMER_HitScore_Cutoff: %s"%options.HMMER_HitScore_Cutoff)
	print("="*100)
	
	UcfVirusAnnotator (
		GenomeSeqFile_UcfVirus = options.GenomeSeqFile_UcfVirus,
		ShelveDir_UcfVirus = options.ShelveDir_UcfVirus,
		ShelveDirs_RefVirus = options.ShelveDirs_RefVirus,
		
		IncludeIncompleteGenomes_UcfVirus = str2bool(options.AnnotateIncompleteGenomes_UcfVirus),
		IncludeIncompleteGenomes_RefVirus = str2bool(options.UsingDatabaseIncludingIncompleteRefViruses),
		#SeqLength_Cutoff = options.SeqLength_Cutoff,
		SeqLength_Cutoff = 0,
		HMMER_N_CPUs = options.HMMER_N_CPUs,
		HMMER_C_EValue_Cutoff = options.HMMER_C_EValue_Cutoff,
		HMMER_HitScore_Cutoff = options.HMMER_HitScore_Cutoff,
		)
	
	print("Input for VirusClassificationAndEvaluation:\n")
	print("="*100)
	print("Main input")
	print("-"*50)
	print("ShelveDir_UcfVirus: %s"%options.ShelveDir_UcfVirus)
	print("ShelveDirs_RefVirus: %s"%options.ShelveDirs_RefVirus)
	print("AnnotateIncompleteGenomes_UcfVirus: %s"%options.AnnotateIncompleteGenomes_UcfVirus)
	print("UsingDatabaseIncludingIncompleteRefViruses: %s"%options.UsingDatabaseIncludingIncompleteRefViruses)
	
	print("\n")
	print("Virus annotation (with PPHMM database derived from unclassified viruses) options")
	print("-"*50)
	print("UseUcfVirusPPHMMs: %s"%options.UseUcfVirusPPHMMs)
	print("GenomeSeqFile_UcfVirus: %s"%options.GenomeSeqFile_UcfVirus)
	print("GenomeSeqFiles_RefVirus: %s"%options.GenomeSeqFiles_RefVirus)
	#print "SeqLength_Cutoff: %s"%options.SeqLength_Cutoff
	print("HMMER_N_CPUs: %s"%options.HMMER_N_CPUs)
	print("HMMER_C_EValue_Cutoff: %s"%options.HMMER_C_EValue_Cutoff)
	print("HMMER_HitScore_Cutoff: %s"%options.HMMER_HitScore_Cutoff)
	
	print("\n")
	print("Virus (dis)similarity measurement options")
	print("-"*50)
	print("SimilarityMeasurementScheme: %s"%options.SimilarityMeasurementScheme)
	print("p: %s"%options.p)
	
	print("\n")
	print("Virus classification options")
	print("-"*50)
	print("Dendrogram_LinkageMethod: %s"%options.Dendrogram_LinkageMethod)
	print("Bootstrap: %s"%options.Bootstrap)
	print("N_Bootstrap: %s"%options.N_Bootstrap)
	print("Bootstrap_method: %s"%options.Bootstrap_method)
	print("Bootstrap_N_CPUs: %s"%options.Bootstrap_N_CPUs)	
	print("DatabaseAssignmentSimilarityScore_Cutoff: %s"%options.DatabaseAssignmentSimilarityScore_Cutoff)
	print("N_PairwiseSimilarityScores: %s"%options.N_PairwiseSimilarityScores)
	
	print("\n")
	print("Heatmap construction options")
	print("-"*50)
	print("Heatmap_WithDendrogram: %s"%options.Heatmap_WithDendrogram)
	print("Heatmap_DendrogramSupport_Cutoff: %s"%options.Heatmap_DendrogramSupport_Cutoff)
	
	print("\n")
	print("Virus grouping options")
	print("-"*50)
	print("VirusGrouping: %s"%options.VirusGrouping)
	print("="*100)
	
	VirusClassificationAndEvaluation (
		ShelveDir_UcfVirus = options.ShelveDir_UcfVirus,
		ShelveDirs_RefVirus = options.ShelveDirs_RefVirus,
		IncludeIncompleteGenomes_UcfVirus = str2bool(options.AnnotateIncompleteGenomes_UcfVirus),
		IncludeIncompleteGenomes_RefVirus = str2bool(options.UsingDatabaseIncludingIncompleteRefViruses),
		
		UseUcfVirusPPHMMs = str2bool(options.UseUcfVirusPPHMMs),
		GenomeSeqFile_UcfVirus = options.GenomeSeqFile_UcfVirus,
		GenomeSeqFiles_RefVirus = options.GenomeSeqFiles_RefVirus,
		#SeqLength_Cutoff = options.SeqLength_Cutoff,
		SeqLength_Cutoff = 0,
		HMMER_N_CPUs = int(options.HMMER_N_CPUs),
		HMMER_C_EValue_Cutoff = float(options.HMMER_C_EValue_Cutoff),
		HMMER_HitScore_Cutoff = float(options.HMMER_HitScore_Cutoff),
		
		SimilarityMeasurementScheme = options.SimilarityMeasurementScheme,
		p = float(options.p),
		Dendrogram_LinkageMethod = options.Dendrogram_LinkageMethod,
		
		DatabaseAssignmentSimilarityScore_Cutoff = float(options.DatabaseAssignmentSimilarityScore_Cutoff),
		N_PairwiseSimilarityScores = int(options.N_PairwiseSimilarityScores),
		
		Heatmap_WithDendrogram = str2bool(options.Heatmap_WithDendrogram),
		Heatmap_DendrogramSupport_Cutoff = float(options.Heatmap_DendrogramSupport_Cutoff),
		
		Bootstrap = str2bool(options.Bootstrap),
		N_Bootstrap = int(options.N_Bootstrap),
		Bootstrap_method = options.Bootstrap_method,
		Bootstrap_N_CPUs = int(options.Bootstrap_N_CPUs),
		
		VirusGrouping = str2bool(options.VirusGrouping),
		)

if __name__ == '__main__':
	main()



