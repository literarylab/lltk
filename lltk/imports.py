# constants

nlp=None
ENGLISH=None
stopwords=set()
MANIFEST={}
spellingd={}
DEFAULT_NUM_PROC=4
PARALLELIZED_CMDS=['preprocess']
PART_REFERRING_CMDS=['install','preprocess','zip','upload','share']
FUNC_CMDS={'compile','preprocess','install'}





from pprint import pprint



import imp

import os,sys,ujson as json,pandas as pd,random,gzip,time,inspect
import re,configparser
from datetime import datetime
import urllib, tempfile
from os.path import expanduser


from tqdm import tqdm
from pprint import pprint
from lltk.tools import tools
from lltk.tools import *
from collections import defaultdict,Counter
from argparse import Namespace
import inspect
import numpy as np
import plotnine as p9, pandas as pd
from zipfile import ZipFile
import shutil,zipfile
import networkx as nx


DEFAULT_CORPUS = 'TxtLab'
DEFAULT_CORPUS_ID = 'txtlab'

ROOT = os.path.dirname(os.path.realpath(__file__))

import warnings,six,shutil
warnings.filterwarnings('ignore')
SPELLING_VARIANT_PATH=os.path.join(ROOT,'data/spelling_variants_from_morphadorner.txt')

HOME=os.path.expanduser("~")
MODERNIZE_SPELLING=False
config = tools.config

ZIP_PART_DEFAULTS={'txt','freqs','metadata','xml','raw'}
DOWNLOAD_PART_DEFAULTS=['metadata','freqs','txt']
PREPROC_CMDS=['txt','freqs','mfw','dtm']
DEST_LLTK_CORPORA=config.get('CLOUD_DEST','/Share/llp_corpora')
DEFAULT_MFW_N =25000
DEFAULT_DTM_N = 25000
DEFAULT_MFW_YEARBIN = 100
MANIFEST_REQUIRED_DATA=['name','id']

MANIFEST_DEFAULTS=dict(
	path_txt='txt',
	path_xml='xml',
	path_index='',
	ext_xml='.xml',
	ext_txt='.txt',

	path_model='',
	path_header=None,
	#path_metadata='metadata.txt',
	path_metadata='metadata.csv',
	path_notebook='notebook.ipynb',
	paths_text_data=[],
	paths_rel_data=[],
	class_name='',

	path_freq_table={},
	col_id='id',
	col_fn='fn',
	path_root='',
	path_raw='raw',
	path_spacy='spacy',
	#path_freqs=os.path.join('freqs',name),
	path_freqs='freqs',
	manifest={},
	path_python='',
	manifest_override=True,
	path_data='data',
	is_meta = '',
	public='',
	mfw_yearbin=False,
)

nlp=None
ENGLISH=None
stopwords=set()
MANIFEST={}



### Corpus related


PATH_HERE=os.path.abspath(os.path.dirname(__file__))
PATH_LLTK_HOME = os.path.join(HOME,'lltk_data')
PATH_CORPUS = config.get('PATH_TO_CORPORA', os.path.join(PATH_LLTK_HOME,'corpora') )
PATH_CORPUS_ZIP = os.path.join(PATH_CORPUS, 'lltk_corpora')
PATH_TO_CORPUS_CODE = config.get('PATH_TO_CORPUS_CODE', os.path.join(PATH_HERE,'corpus') )

DEFAULT_PATH_TO_MANIFEST = os.path.join(PATH_LLTK_HOME,'manifest.txt')
PATH_MANIFEST=os.path.join(PATH_TO_CORPUS_CODE,'manifest.txt')
PATH_MANIFEST_USER = config.get('PATH_TO_MANIFEST','')
PATH_MANIFEST_USER_LAB = PATH_MANIFEST_USER.replace('.txt','_lab.txt')
PATH_MANIFEST_USER_SHARE = PATH_MANIFEST_USER.replace('.txt','_share.txt')

PATH_MANIFESTS = tools.remove_duplicates([
	PATH_MANIFEST,
	os.path.join(PATH_TO_CORPUS_CODE,'manifest_local.txt'),
	os.path.abspath(os.path.join(PATH_TO_CORPUS_CODE,'..','..','lltk_manifest.txt')),
	os.path.abspath(os.path.join(PATH_CORPUS,'manifest.txt')),
	os.path.abspath(os.path.join(PATH_CORPUS,'manifest_local.txt')),
	os.path.abspath(os.path.join(PATH_HERE,'..','..','config','lltk_manifest.txt')),
	os.path.join(PATH_TO_CORPUS_CODE,'manifest_lab.txt'),
	os.path.join(PATH_LLTK_HOME,'manifest_share.txt'),
	os.path.join(PATH_LLTK_HOME,'manifest_lab.txt'),
	os.path.join(PATH_LLTK_HOME,'manifest.txt'),
	os.path.join(HOME,'lltk_manifest.txt'),
	PATH_MANIFEST_USER,
	PATH_MANIFEST_USER_LAB,
	PATH_MANIFEST_USER_SHARE
], remove_empty=True)
#print(PATH_MANIFESTS)

from pprint import pprint


from lltk.text.utils import *
from lltk.corpus.utils import *
from lltk.text.text import *
from lltk.corpus.corpus import *



