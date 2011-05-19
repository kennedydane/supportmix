import sys
import os
import ConfigParser
import pylab
#from optparse import OptionParser
from optparse import OptionParser, OptionGroup, OptionValueError
DEBUG=False


CHROM=None
WIN=None
N_GENS=None
SAVE_FILE=None
CORRECT_FILE=None
FILE_NAMES=[]
DO_PLOT=None
RGB=None
CONFIGFILE=None
LABELS=None
IS_BEAGLE=None
MAP_DIR=None
N_PARALLEL=None


USAGE="""%prog [options] ancestralFile1 ancestralFile2 [...] admixedFile

where the ancestralFiles and admixedFiles are contain phased samples
in tab delimited format snps in rows and samples in columns.  One row
of column headers and two columns of header information (i.e. rsId and
position).  The files have to be from the same chromosome indicated by
including chr[0-9]* in the name.
"""

#--TODO Remove parser dependency
def fail(parser, str):
    sys.stderr.write('SupportMix ERROR: %s\n\n' %str)
    parser.print_usage()
    sys.exit(1)


def warn(str):
    sys.stderr.write('SupportMix WARNING!: %s\n' %str)
    

def determineChromosome(fileNames):
    """Estimates the chromosome name by searching for "chr" in input
    file names.
    Arguments:
    - @fileNames:List of fileNames 
    """
    import re 
    p = re.compile('chr\d*', re.IGNORECASE)
    try:
        found=[p.search(name).group() for name in fileNames]
        if not np.all(found[0]==np.asarray(found)): raise Error
        return found[0]
    except:
        fail(parser, 'If no chromosome is specified then all fileNames must contain the same pattern of: chr[0-9]*')


def createDataPath(dataPath='data'):
    """Returns the Current Path of the "executable" """
    #Check if running from the binary
    frozen = getattr(sys, 'frozen', None)
    if frozen:
        programPath= os.path.split(__file__.replace("%slibrary.zip"%os.path.sep,""))[0]
    else:
        programPath= os.path.split(__file__)[0]
    return os.path.join(programPath, dataPath)


def readConfig(configFile="supportMix.cfg"):
    config=ConfigParser.ConfigParser()
    config.read(configFile)
    return config

##Thinking of moving some of the validation here
#def validateOptions(params):
##    config=readConfig()
#    if params['rgb']!=None:
#        params['rgb']=validateColors(params['rgb'])
#        params['doPlot']=True
#        rawConfiguration['doPlot']=True
#    if params['labels']!=None:
#        params['labels']=validateLabels(params['labels'])
#        params['doPlot']=True
#        rawConfiguration['doPlot']=True       
#    if params['rgb']!=None and len(params['rgb'])<len(params['fileNames'])-1:
#        fail(parser, 'too few colors specified to --RGB')
#    if params['labels']!=None and len(params['labels'])<len(params['fileNames'])-1:
#        fail(parser, 'too few labels specified to --labels')
#    if params['chrom']==0: #Use filenames to guess the chromsome used
#        params['chrom']=determineChromosome(params['fileNames']).replace('chr','')
#        sys.stderr.write('WARNING! No chromosome was specified assuming: %s\n'%params['chrom'])


   
def getConfigOptions(configFile):
    
    config=readConfig(configFile)
    configData={}
    
    if config.has_option('parameters', 'chromosome'):
        configData['chrom']=config.getint('parameters', 'chromosome')
    else:
        configData['chrom']=CHROM
    
    if config.has_option('parameters', 'window'):
        configData['win']=config.getint('parameters','window')
    else:
        configData['win']=WIN
    
    if config.has_option('parameters','generations'):
        configData['nGens']=config.getfloat('parameters','generations')
    else:
        configData['nGens']=N_GENS
        
    if config.has_option('parameters','saveFile'):
        configData['saveFile']=config.get('parameters','saveFile')
    else:
        configData['saveFile']='outSupportMix'
        
    if config.has_option('parameters','parallel'):
        configData['nParallel']=config.get('parameters','parallel')
    else:
        configData['nParallel']=None
    
    if config.has_option('parameters','mapDir'):
        configData['mapDir']=config.get('parameters','mapDir')
    else:
        configData['mapDir']=None
    
    #File related processing
    if config.has_section('data location'):
        baseDataDir=config.get('data location','baseDataDir')
    else:
        baseDataDir=None
    
    #here we assume that all the files including the ancestry file are located 
    #in the data path
    #If the ancestry file's full path is specified the path will be used instead.
    #Otherwise will try to locate the file in the data dir
    
    #ancestryFile=""
    if config.has_option('parameters','ancestryFile'):
        ancestryFile=config.get('parameters','ancestryFile')
    else:
        ancestryFile=None
        raise ConfigParser.Error("Undefined Ancestry file")
    
    if ancestryFile:
        if os.path.exists(ancestryFile):
            configData['correctFile']=ancestryFile
        
        elif baseDataDir!=None:
            #Check for ancestry file in data path
            ancestryFile=os.path.join(baseDataDir,ancestryFile)
            if os.path.exists(ancestryFile):
                configData['correctFile']=ancestryFile
            else:
                raise ConfigParser.Error("Can't find Ancestry File")
            
    
    
    fileNames=[]
    admixed=None
    for itemLabel,fileItem in config.items('input'):
        #fileItem=inputItem
        
        if baseDataDir!=None:
            fileItem=os.path.join(baseDataDir,fileItem)
        #Validate file existence
        if not os.path.exists(fileItem):
            raise ConfigParser.Error("Can't find file: %s"%fileItem)
            
        if itemLabel!='admixed':
            fileNames.append(fileItem)
        else:
            admixed=fileItem
    
    if admixed:
        fileNames.append(admixed)
    else:
        raise ConfigParser.Error("Admixed population not defined")
    
    configData['fileNames']=fileNames
    
    if config.has_section('plot options'):
        #configData['doPlot']=config.getboolean('plot options', 'plot')
        
        if config.has_option('plot options', 'plot'):
            configData['doPlot']=config.get('plot options', 'plot')
        else:
            configData['doPlot']=None
        
        if config.has_option('plot options', 'RGB'):
            configData['rgb']=config.get('plot options', 'RGB')
            configData['doPlot']=True
        else:
            configData['rgb']=None
        
        if config.has_option('plot options', 'labels'):
            configData['labels']=config.get('plot options', 'labels')
            configData['doPlot']=True
        else:
            configData['labels']=None
        
    return configData

def writeConfigFile(configData,configFileName='outSupportMix.cfg'):
    '''Writes a configuration file for the current settings
    '''
    
    config=ConfigParser.ConfigParser()
    #config=ConfigParser.RawConfigParser()
    
    #print "DATA Received by writeConfig",configData
    
    config.add_section('parameters')
    #chromValue=configData.chrom
    config.set('parameters', 'chromosome', configData['chrom'])
    config.set('parameters', 'window', configData['win'])
    config.set('parameters', 'generations', configData['nGens'])
    config.set('parameters', 'saveFile', configData['saveFile'])
    config.set('parameters', 'saveFile', configData['saveFile'])
    
    if configData['nParallel']!=None:
        config.set('parameters','parallel', configData['nParallel'])
    if configData['mapDir']!=None:
        config.set('parameters','mapDir', configData['mapDir'])
    
    if configData['correctFile']:
        baseDataDir, ancestryFile=os.path.split(configData['correctFile'])
        config.set('parameters', 'ancestryFile', ancestryFile)
    else:
        baseDataDir=None
    
    config.add_section('input')
    baseItemLabel="sample%d"
    #here we are not checking that all the files have the same path coming in
    #We are assuming that all the files are path of the data path if it was been 
    #defined. Thus only the base name of the file is kept.
    #@TODO: Check that fileNames is not empty
    for i,fileItem in enumerate(configData['fileNames'][:-1]):
        config.set('input', baseItemLabel%(i+1), os.path.basename(fileItem))
    
    if baseDataDir:
        config.set('input','admixed', os.path.basename(configData['fileNames'][-1]))
    else:
        baseDataDir, admixed = os.path.split(configData['fileNames'][-1])
        config.set('input','admixed', admixed)
    
    
    if baseDataDir!='':
        config.add_section('data location')
        config.set('data location', 'baseDataDir', baseDataDir)
    
    if configData['doPlot']:
        config.add_section('plot options')
        config.set('plot options','plot',configData['doPlot'])
        
        if configData['rgb']:
            config.set('plot options','RGB',configData['rgb'])
        if configData['labels']:
            config.set('plot options','labels',configData['labels'])
    #        config.set('plot options','labels',",".join(configData['labels']))

    with open(configFileName, 'wb') as configfile:
        configfile.write("#SupportMix configuration file.\n#To run type: SupportMix -C %s\n"%(configFileName))
        config.write(configfile)

        
def validateColors(value):
    conv=pylab.mpl.colors.ColorConverter()
    try:
        values=[conv.to_rgba(c) for c in value.split(',')]
        return values
    except:
        supportConfig.fail(parser, 'color specification to %s incorrect' %"RGB")


def validateLabels(value):
    try: 
        labels=value.split(',')
        return labels
    except:
        supportConfig.fail(parser, 'label specification to %s incorrect' %"labels")


def getParameters(rawConfiguration):
    
    rawConfiguration['chrom']=CHROM
    rawConfiguration['win']=WIN
    rawConfiguration['nGens']=N_GENS
    rawConfiguration['saveFile']=SAVE_FILE
    rawConfiguration['correctFile']=CORRECT_FILE
    rawConfiguration['fileNames']=FILE_NAMES
    rawConfiguration['doPlot']=DO_PLOT
    rawConfiguration['labels']=RGB
    rawConfiguration['rgb']=CONFIGFILE
    rawConfiguration['configFile']=LABELS
    rawConfiguration['isBeagle']=IS_BEAGLE
    rawConfiguration['nParallel']=MAP_DIR
    rawConfiguration['mapDir']=N_PARALLEL

    #Command Line parsing of parameters
    parser = OptionParser(usage=USAGE)
    parser.add_option('-c', '--chromosome', type='str', dest='chrom',
                      help='Chromsome being analyzed (default guessed from file names)', metavar='N')
    parser.add_option('-w', '--window', type='int', dest='win',
                      help='Number of SNPs in each window (default 100)', metavar='N')
    parser.add_option('-g', '--generations', type='float', dest='nGens',
                      help='Number of generations since admixture used in hmm. (default 6)', metavar='N')
    parser.add_option('-s', '--save', type='str', dest='saveFile',
                      help='Destination file to save output (default outSupportMix)', metavar='file')
    parser.add_option('-a', '--ancestryFile', type='string', dest='correctFile',
                      help='FILE contains correct classifications in tab delimited format with SNPs in rows and samples in columns (first two columns contain rsID and position. ', metavar='FILE')
    parser.add_option('-C', '--config', type='string', dest='configFile',
                      help='Use a config file instead of parameters', metavar='file')
    parser.add_option('-P', type='int', dest='nParallel', metavar='N',
                      help="Run up to N processes in parallel at the same time (default 1)")
    parser.add_option('-m', '--map-dir', type='string', dest='mapDir', metavar='directory',
                      help="path to a directory of genetic map files.  The directory must contain a series of files which names containing chrN where N varies over all chromosomes in the input files  (example: genetic_map_chr1_b36.txt and genetic_map_chr22_b36.txt).  These files contain three, white spaced dilimeted columns: position [bp], combined rate [cM/Mb], Genetic Map [cM].  Example files for human genome release 36 can be found at, ftp://ftp.hapmap.org/hapmap/recombination/2008-03_rel22_B36/rates/ and for relase 37 at, ftp://ftp.hapmap.org/hapmap/recombination/2011-01_phaseII_B37/genetic_map_HapMapII_GRCh37.tar.gz")
    parser.add_option('--generateConfig', action='store_true', dest='generateConfig',
                      help='Create a sample configuration file with default parameters')
    parser.add_option('-t', action='store_true', dest='isBeagle',
                      help='DEPRECATED Do not use!!!!!!!!!')
    group = OptionGroup(parser, 'Plotting Options', 'Use these options to generate graphics and customize graphics.'
                    'It is believed that some of them bite.')
    group.add_option('-p', '--plot', dest='doPlot', action='store_true',
                      help='Generate graphical output')
    group.add_option('--RGB', type='string',  dest='rgb', metavar='colors',
                      help='Color specifications of different populations for graphing : ')
    group.add_option('--labels', type='string', dest='labels', metavar='labels',
                      help='populations labels for graphing Example: ceu,yri,mkk')
    parser.add_option_group(group)
    
    (cmdOptions, args) = parser.parse_args()
    #Config file parsing
    if cmdOptions.generateConfig:
        sys.stdout.write("Generating default config file...\n")
        defaultConfigFile="supportMixConfigExample.cfg"
        rawConfiguration['correctFile']="ancestryfileHere.txt"
        rawConfiguration['fileNames']=['sample1.txt','sample2.txt','myDataDirectoryHere/myAdmixedFileHere.txt']
        writeConfigFile(rawConfiguration,defaultConfigFile)
        sys.stdout.write("Configuration example saved to: %s\n"%defaultConfigFile)
        sys.exit(0)
        
    if cmdOptions.configFile:
        if DEBUG:
            print "Running with options listed in:", os.path.abspath(cmdOptions.configFile)
        if os.path.exists(cmdOptions.configFile):
            try:
                configData=getConfigOptions(cmdOptions.configFile)
                for k,value in configData.iteritems():
                    if value!=None:
                        rawConfiguration[k]=value
            except ConfigParser.Error as errorMsg:
                sys.stderr.write('SupportMix ERROR: %s\n\n' %errorMsg)
            #Added support for chromosome only and ancestry files on the config file
            #         Is this really a stupid idea?  Should we ship a default config file instead?
            #Francisco: Should probably be 86 now?
#            if len(rawConfiguration['fileNames'])==1:  #no ancestral files given run in default with all HGDP populations
#                admixed=rawConfiguration['fileNames']
#                rawConfiguration['fileNames']=glob.glob(HGDP_BASENAME%rawConfiguration['chrom'])
#                rawConfiguration['fileNames'].extend(admixed)
#            elif len(rawConfiguration['fileNames'])==2:  #too few ancestral files given 
#                fail(parser, 'Not enough ancestral populations were given')
        else:
            fail(parser, 'Invalid Config File Specified')
    else:
        cmdOptions.fileNames=args
                    
    #Overwrite the "raw" configuration values with command line values whenever
    for key,value in cmdOptions.__dict__.iteritems():
        if value!=None:
            rawConfiguration[key]=value
    #keep the original parameters
    params=rawConfiguration.copy()
    
    if len(params['fileNames'])<3:
        fail(parser, 'Not enough ancestral populations were given')
    

    if params['rgb']!=None:
        params['rgb']=validateColors(params['rgb'])
        params['doPlot']=True
        rawConfiguration['doPlot']=True
    if params['labels']!=None:
        params['labels']=validateLabels(params['labels'])
        params['doPlot']=True
        rawConfiguration['doPlot']=True       
    if params['rgb']!=None and len(params['rgb'])<len(params['fileNames'])-1:
        fail(parser, 'too few colors specified to --RGB')
    if params['labels']!=None and len(params['labels'])<len(params['fileNames'])-1:
        fail(parser, 'too few labels specified to --labels')
    if params['chrom']==0: #Use filenames to guess the chromsome used
        params['chrom']=determineChromosome(params['fileNames']).replace('chr','')
        warn('No chromosome was specified assuming: %s\n'%params['chrom'])
        #sys.stderr.write('WARNING! No chromosome was specified assuming: %s\n'%params['chrom'])
        
    return params



if __name__ =="__main__":
   
    print getConfigOptions("supportMix.cfg")
    
