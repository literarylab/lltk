from lltk.imports import *

### Accessing corpora

def corpora(load=True,load_meta=False,incl_meta_corpora=True):
	manifest=load_manifest()
	for corpus_name in sorted(manifest):
		if not incl_meta_corpora and manifest[corpus_name]['is_meta']: continue
		corpus_obj=load_corpus(corpus_name, manifestd=manifest[corpus_name], load_meta=load_meta) if load else manifest[corpus_name]
		# print(corpus_name, corpus_obj)
		if corpus_obj is None: continue
		yield (corpus_name, corpus_obj)

def check_corpora(paths=['path_raw','path_xml','path_txt','path_freqs','path_metadata'],incl_meta_corpora=False):
	old=[]
	#clist=tools.cloud_list()
	print('{:25s} {:32s} {:12s} {:12s} {:12s} {:12s} {:12s}'.format('[CORPUS]','[DESCRIPTION]',' [RAW?]',' [XML?]',' [TXT?]',' [FREQS?]',' [METADATA?]'))
	for cname,corpus in corpora(load=True,incl_meta_corpora=incl_meta_corpora):
		if corpus is None: continue
		print('{:25s} {:30s}'.format(cname, corpus.desc[:25]),end=" ")
		for path in paths:
			pathtype=path.replace('path_','')
			pathval = getattr(corpus,path)
			#pathval = corpus.get(path,'')
			exists = '↓' if os.path.exists(pathval) and (not os.path.isdir(pathval) or bool(os.listdir(pathval))) else ' '

			#exists_cloud = '↑' if f'{corpus.id}_{pathtype}.zip' in clist else ' '
			exists_link = '↑' if hasattr(corpus,f'url_{pathtype}') else ' '
			zip_fn=f'{corpus.id}_{pathtype}.zip'
			#exists_zip = '←' if os.path.exists(os.path.join(PATH_CORPUS_ZIP,zip_fn)) else ' '
			cell=' '.join([x for x in [exists,exists_link,pathtype] if x])
			print('{:12s}'.format(cell),end=' ')

		print()
			#odx={'name':cname,'id':corpus.id,'path_type':path, 'path_value':pathval, 'exists':exists}
			#old+=[odx]
	#import pandas as pd
	#df=pd.DataFrame(old)
	#print(df)
	#return df

def induct_corpus(name_or_id_or_C):
	C=lltk.load(name_or_id) if type(name_or_id_or_C)==str else name_or_id_or_C
	ifn_py=C.path_python
	ifn_ipynb=C.path_notebook
	ofn_py=os.path.join(PATH_TO_CORPUS_CODE, C.id, os.path.basename(C.path_python))
	ofn_ipynb=os.path.join(PATH_TO_CORPUS_CODE, C.id, os.path.basename(C.path_notebook))
	# print(ifn_py,'-->',ofn_py)
	# print(ifn_ipynb,'-->',ofn_ipynb)
	check_copy_file(ifn_py,ofn_py)
	check_copy_file(ifn_ipynb,ofn_ipynb)

def showcorp():
	return print(status_corpora_markdown())

def status_corpora_markdown(maxcolwidth=45,link=False,public_only=False):
	df=status_corpora(link=link,public_only=public_only).set_index('name')
	for col in df.columns:
		df[col]=df[col].apply(lambda x: str(x)[:maxcolwidth])
	return df.to_markdown()

def status_corpora(parts=['metadata','freqs','txt','xml','raw'],link=True,public_only=True):
	ld=[]
	for cname,C in corpora(load=True,incl_meta_corpora=False):
		dx=defaultdict(str)
		dx['name']=cname
		dx['desc']=C.desc.strip() if (not link or not C.link.strip()) else f'[{C.desc.strip()}]({C.link.strip()})'
		for pk in parts: dx[pk]=''
		ppub = {x.strip() for x in C.public.split(',') if x.strip()}
		for p in parts:
			ppath=C.has_data(p)
			if not link and ppath and (not public_only or p in ppub):
				dx[p]='✓'
			else:
				url=C.has_url(p)
				if url and (not public_only or p in ppub):
					dx[p]+='↓' if not link else f'[↓]({url})'
		# if not ppub and public_only: dx['raw']='☂'
		ld.append(dx)
	return pd.DataFrame(ld).fillna('')



def status_corpora_readme():
	df=status_corpora(link=False,public_only=True)
	df['name']=df.name.apply(lambda name: f'[{name}](lltk/lltk/corpus/{name})')
	print(df.set_index('name').to_markdown())






def to_authorkey(name):
	return zeropunc(to_lastname(name))




def corpus_names():
	return sorted([cname for cname,cd in corpora(load=False)])




def share_corpora():
	allstr=[]
	for cname,corpus in corpora(load=True,incl_meta_corpora=False):
		allstr+=[corpus.share()]
	allstr='\n\n'.join(allstr)
	ofn=PATH_MANIFEST_USER_SHARE
	with open(ofn,'w') as of:
		of.write('# Download URLs for corpora found on cloud\n\n' + allstr+'\n')
		print('>> saved:',ofn)




def fix_meta(metadf, badcols={'_llp_','_lltk_','corpus','index','id.1','url_wordcount','url_text'},order=['id','author','title','year']):
	prefixcols = [col for col in order if col in set(metadf.columns)]
	badcols|=set(prefixcols)
	newcols = prefixcols+[col for col in metadf.columns if not col in badcols and not col.startswith('Unnamed:')]
	metadf = metadf[newcols]
	return metadf

def clean_meta(meta):
	# clean year?
	if 'year' in set(meta.columns):
		newyears=pd.to_numeric(meta.year,errors='coerce',downcast='integer')
	if False in [(x==y) for x,y in zip(meta.year, newyears)]:
		meta['year_orig']=meta.year
	meta['year']=newyears
	return meta






def start_new_corpus_interactive(args,import_existing=False):
	import os
	import lltk
	from lltk import tools

	keys_mentioned =['path_root','path_xml','path_txt','path_python','path_metadata','class_name','name','id','desc','link']
	for k in keys_mentioned:
		if not hasattr(args,k):
			setattr(args,k,'')

	try:
		print('### LLTK: Start up a new corpus ###')

		name,idx=args.name,args.id
		if not name: name=input('\n>> (1) Set name of corpus (CamelCase, e.g. ChadwyckPoetry): ').strip()
		if not idx: idx=input('>> (2) Set ID of corpus (lower-case, e.g chadwyck_poetry): ').strip()


		## Set defaults
		path_root_default=idx
		path_code_default=idx+'.py'
		path_txt_default='txt'
		#path_xml_default='xml'
		path_xml_default='xml'
		path_metadata_default='metadata.csv'
		class_name_default = ''.join([x for x in name if x.isalnum() or x=='_'])

		# import vs create
		# if importing, we're finding an existing directory
		# if creating, we're specifying a future directory
		sources = ['.',lltk.PATH_CORPUS] if import_existing else [lltk.PATH_CORPUS,'.']

		def get_path_abs(path,sources=sources,rel_to=None):
			if not path: return ''
			if os.path.isabs(path):
				rpath=path
			else:
				rpath=''
				for source in sources:
					spath=os.path.join(source,path)
					#if os.path.isabs(spath): return spath
					if os.path.exists(spath):
						rpath=os.path.abspath(spath)
						break
			if not rpath: return ''

			if rel_to:
				return os.path.relpath(rpath,rel_to)
			else:
				return os.path.abspath(rpath)




		attrs={}

		def do_path(path,path_name,msg,root,default,remove_root=True,create=True):
			if not hasattr(args,'defaults'): args.defaults=None
			if not path and not args.defaults:
				path=get_path_abs(input(msg).strip())
			else:
				print(msg)
				#print(f'   -{path_name} set from command line...')
			path_abs_default=os.path.join(root,default)
			path_abs=path=get_path_abs(path)
			if not path:
				path=default
				path_abs=os.path.join(root,path)
			if not path: return ''
			link_to=path_abs_default if path_abs!=path_abs_default else None
			if create: tools.check_make_dir(path_abs) #,link_to=link_to)

			#print('?',path,path_name,path_abs,path_abs_default)
			#if not path_name in {'path_xml'} or os.path.exists(path_abs):
			#print('>> setting: %s =' % path_name,path)
			if remove_root:
				#print(path_name+'\n'+path+'\n'+root)
				if path.startswith(root):
					path=path[len(root):]
					if path and path[0] in {'/','\\'}: path=path[1:]
				#print(path,'\n\n')


			prefix='   %s =' % path_name

			#print(prefix,path)
			print(f'\n   [manifest] {path_name} = {path}')
			print(f'   [abs path] {path_abs}\n')

			if path_abs and link_to and os.path.dirname(path_abs)!=os.path.dirname(link_to):
				tools.symlink(path_abs,link_to)



			return path

		path_config=tools.get_config_file_location()
		path_to_corpora=lltk.config.get('PATH_TO_CORPORA','')

		corpus_msg_root=f'If a relative path is given and it does not point to an existing file,\n       it is assumed relative to {path_to_corpora}'
		msg=f'\n----\n\n>> (3) Set path to corpus root data folder\n       {corpus_msg_root}\n>> [{path_root_default}] '
		path_root = attrs['path_root'] = do_path(args.path_root, 'path_root', msg, lltk.PATH_CORPUS, path_root_default, create=True)
		path_root_abs = os.path.join(lltk.PATH_CORPUS,path_root) if not os.path.isabs(path_root) else path_root

		corpus_msg=f'If a relative path is given and it does not point to an existing file,\n       it is assumed relative to {path_root_abs}'
		msg=f'\n----\n\n>> (4) Set path to metadata file\n       {corpus_msg}\n>> [{path_metadata_default}] '
		path_metadata = attrs['path_metadata'] = do_path(args.path_metadata, 'path_metadata', msg, path_root_abs, path_metadata_default, create=False)

		msg=f'\n----\n\n>> (5) Set path to txt folder (Optional, if xml folder)\n       {corpus_msg}\n>> [{path_txt_default}] '
		path_txt = attrs['path_txt'] = do_path(args.path_txt, 'path_txt', msg, path_root_abs, path_txt_default, create=False)

		msg=f'\n>> (6) Set path to xml folder (Optional, if txt folder)\n       {corpus_msg}\n>> [{path_xml_default}] '
		path_xml = attrs['path_xml'] = do_path(args.path_xml, 'path_xml', msg, path_root_abs, path_xml_default, create=False)

		msg=f'\n>> (7) Set path to a .py file defining corpus object (Optional)\n       {corpus_msg}\n>> [{path_code_default}] '
		path_python = attrs['path_python'] = do_path(args.path_python, 'path_python', msg, path_root_abs, path_code_default, create=False)

		# class name
		class_name=args.class_name
		if not class_name and not args.defaults: class_name=input('>> (8) Set name of corpus class within python code (Optional) [%s]: ' % class_name_default).strip()
		if not class_name: class_name=class_name_default
		attrs['class_name'] = class_name
		print('\n   [manifest] class_name =',class_name,'\n')

		# optional
		desc=args.desc
		if not desc and not args.defaults: desc=input('>> (9) Set description of corpus (Optional): ').strip()
		if not desc: desc='--'
		attrs['desc']=desc

		link=args.link
		if not link and not args.defaults: input('>> (10) Set web link to/about corpus (Optional): ').strip()
		if not link: link='--'
		attrs['link']=link
	except KeyboardInterrupt:
		print()
		exit()


	attrs['name']=name
	attrs['id']=idx
	attrs={'name':name,'id':idx,'desc':desc,'link':link,
	'path_root':path_root,'path_txt':path_txt,'path_xml':path_xml,'path_metadata':path_metadata,
	'path_python':path_python,'class_name':class_name}

	return start_new_corpus(attrs)







def start_new_corpus(attrs):
	from argparse import Namespace
	#ns = Bunch(**attrs)
	ns=Namespace(**attrs)

	manifeststr="""[{name}]
name = {name}
id = {id}
desc = {desc}
link = {link}
path_root = {path_root}
path_txt = {path_txt}
path_xml = {path_xml}
path_metadata = {path_metadata}
path_python = {path_python}
class_name = {class_name}
""".format(**attrs)

	print('-'*40)


	### WRITE MANIFEST
	path_manifest = PATH_MANIFEST_USER if os.path.exists(PATH_MANIFEST_USER) else PATH_MANIFEST
	with open(path_manifest) as f:
		global_manifest_txt = f.read()

	if not '[%s]' % ns.name in global_manifest_txt:
		print('>> Saving to corpus manifest [%s]' % path_manifest)
		with open(path_manifest,'a+') as f:
			f.write('\n\n'+manifeststr+'\n\n')
		#print(manifeststr)

	## create new data folders
	ns.path_root = os.path.join(PATH_CORPUS,ns.path_root) if not os.path.isabs(ns.path_root) else ns.path_root
	ns.path_txt = os.path.join(ns.path_root,ns.path_txt) if not os.path.isabs(ns.path_txt) else ns.path_txt
	ns.path_xml = os.path.join(ns.path_root,ns.path_xml) if not os.path.isabs(ns.path_xml) else ns.path_xml
	ns.path_metadata = os.path.join(ns.path_root,ns.path_metadata) if not os.path.isabs(ns.path_metadata) else ns.path_metadata
	ns.path_metadata_dir,ns.path_metadata_fn=os.path.split(ns.path_metadata)




	#check_make_dirs([ns.path_root,ns.path_txt,ns.path_xml,ns.path_metadata_dir],consent=True)


	### Create new code folder
	ns.path_python=os.path.join(ns.path_root,ns.path_python) if not os.path.isabs(ns.path_python) else ns.path_python
	path_python_dir,path_python_fn=os.path.split(ns.path_python)
	python_module=os.path.splitext(path_python_fn)[0]
	#if not path_python_dir: path_python_dir=os.path.join(PATH_TO_CORPUS_CODE,python_module)
	#if not path_python_dir: path_python_dir=os.path.abspath(os.path.join(ns.path_root,python_module))

	if not os.path.exists(path_python_dir):
		print('>> creating:',path_python_dir)
		os.makedirs(path_python_dir)

	python_fnfn=os.path.join(path_python_dir,path_python_fn)
	#python_fnfn2=os.path.join(path_python_dir,'__init__.py')
	python_ifnfn=os.path.join(PATH_TO_CORPUS_CODE,'default','new_corpus.py')
	ipython_ifnfn=os.path.join(PATH_TO_CORPUS_CODE,'default','notebook.ipynb')

	#if not os.path.exists(python_fnfn) and not os.path.exists(python_fnfn2) and os.path.exists(python_ifnfn):
	#if not os.path.exists(python_fnfn) and os.path.exists(python_ifnfn):
	# ofn=tools.iter_filename(python_fnfn)
	ofn=python_fnfn
	ofnipy = os.path.join(ns.path_root, 'notebook.ipynb')
	if os.path.exists(python_ifnfn):
		#with open(python_fnfn,'w') as of, open(python_fnfn2,'w') as of2, open(python_ifnfn) as f:
		with open(ofn,'w') as of, open(ofnipy,'w') as of2, open(python_ifnfn) as f, open(ipython_ifnfn) as f2:
			of.write(f.read().replace('NewCorpus',ns.class_name))
			of2.write(f2.read().replace('NewCorpus',ns.class_name))
			#of2.write('from .%s import *\n' % python_module)
			print('>> saved:',ofn)
			print('>> saved:',ofnipy)



		#print('>> creating:',ns.path_metadata)
		#from pathlib import Path
		#Path(ns.path_metadata).touch()

	print('\n>> Corpus finalized with the following manifest configuration:')
	print(manifeststr)




def get_python_path(path_python,path_root):
	if os.path.isabs(path_python): return path_python
	paths=[]
	paths+=[os.path.join(path_root,path_python)]
	module_name=os.path.splitext(os.path.basename(path_python))[0]
	paths+=[os.path.join(path_root,module_name,path_python)]  # if not path_python.startswith(os.path.sep) else path_python
	paths+=[os.path.join(PATH_TO_CORPUS_CODE,path_python)]
	paths+=[os.path.join(PATH_TO_CORPUS_CODE,module_name,path_python)]
	for ppath in paths:
		if os.path.exists(ppath):
			return os.path.abspath(ppath)
	return ''




#### LOAD CORPUS FROM MANIFEST

def load_corpus_manifest(name_or_id,manifestd={}):
	if not manifestd:
		manifest=load_manifest(name_or_id)
		if name_or_id in manifest:
			manifestd=manifest[name_or_id]
		else:
			for cname,cd in manifest.items():
				if cd['id']==name_or_id:
					manifestd=cd
					break
	if not manifestd: return {}

	if not manifestd.get('id'): manifestd['id']=name_or_id
	if not manifestd.get('path_root'): manifestd['path_root']=manifestd['id']
	if not os.path.isabs(manifestd.get('path_root')):
		manifestd['path_root']=os.path.join(PATH_CORPUS,manifestd['path_root'])

	# get id
	corpus_id=manifestd.get('id')
	if not corpus_id: return
	corpus_name=manifestd.get('name','').strip()
	if not corpus_name:
		corpus_name=manifestd['name']=corpus_id.replace('_',' ').title().replace(' ','')
	# get full python path
	path_python=manifestd.get('path_python','').strip()
	if not path_python: path_python=corpus_id+'.py'
	manifestd['path_python'] = path_python = get_python_path(path_python, manifestd['path_root'])
	
	if not manifestd.get('class_name'): manifestd['class_name']=manifestd['name']


	# abspath the paths
	for k,v in manifestd.items():
		if k.startswith('path_'):
			if type(v)==str and v and not os.path.isabs(v):
				manifestd[k]=os.path.join(manifestd['path_root'], v)
	
	return manifestd



def load_manifest(force=True,corpus_name=None):
	if MANIFEST and not force: return MANIFEST

	# read config
	#print('>> reading config files...')
	import configparser
	config = configparser.ConfigParser()
	config_d={}
	for path in PATH_MANIFESTS:
		if not os.path.exists(path): continue
		config.read(path)

	# convert config
	for corpus in list(config.keys()):
		if not corpus_name or corpus==corpus_name:
			if corpus=='DEFAULT': continue
			cd={}
			for k,v in MANIFEST_DEFAULTS.items(): cd[k]=v
			for k,v in list(config[corpus].items()): cd[k]=v

			## LAST MINUTE DEFAULTS!?
			try:
				if not cd.get('path_python'): cd['path_python']=cd['id']+'.py'
			except KeyError:
				continue

			MANIFEST[corpus]=cd

	return MANIFEST if not corpus_name else MANIFEST.get(corpus_name,{})




def divide_texts_historically(texts,yearbin=10,yearmin=None,yearmax=None,min_len=None,empty_group='all'):
	from collections import defaultdict
	grp=defaultdict(list)
	for t in texts:
		if yearbin:
			try:
				yearbin=int(yearbin)
				year=int(t.year)
				if yearmin and year<yearmin: continue
				if yearmax and year>=yearmax: continue
				ybin = year // yearbin * yearbin
				ybinstr = f'{ybin}-{ybin+yearbin}'
				grp[ybinstr]+=[t]
			except ValueError:
				continue
		else:
			grp[empty_group]+=[t]
	if min_len: grp = dict((gname,gtexts) for gname,gtexts in grp.items() if len(gtexts)>=min_len)
	return grp




def load_corpus(name_or_id,manifestd={},load_meta=True,**input_kwargs):
	if not manifestd: manifestd=load_corpus_manifest(name_or_id)
	module = imp.load_source(manifestd['id'], manifestd['path_python'])
	class_class = getattr(module,manifestd['class_name'])
	class_obj = class_class(load_meta=load_meta,**manifestd)
	return class_obj



def gen_manifest(order=['id','name','desc','link']):
	manifest = load_manifest()
	cstringl=[]
	for corpus,corpusd in sorted(manifest.items()):
		manifestdefault = dict(MANIFEST_DEFAULTS.items())
		# manifestdefault['name']=corpus
		# manifestdefault['id']=corpus.lower()
		manifestdefault['path_python']=corpusd['id']+'.py'
		manifestdefault['path_root']=corpusd['id']
		manifestdefault['class_name']=corpusd['name']
		corpusd = dict(
			(k,v)
			for k,v in corpusd.items()
			if manifestdefault.get(k)!=v
		)
		cstringl+=[f'[{corpus}]']
		for x in order:
			cstringl+=[f'{x} = {corpusd.get(x,"--")}']
		for x in sorted(corpusd):
			if x in set(order): continue
			if not corpusd.get(x): continue
			cstringl+=[f'{x} = {corpusd.get(x,"--")}']
		cstringl+=['']
	
	txt='\n'.join(cstringl)
	print(txt)
	return txt
		


# show stats

# compute number of words
def do_text(obj):
	idx,corpus_path=obj#corpus.path_freqs):
	try:
		path_freqs=os.path.join(corpus_path,idx+'.json')
		if not os.path.exists(path_freqs): return 0
		with open(path_freqs) as f:
			freqd=json.load(f)
			return sum(freqd.values())
	except ValueError:
		pass
	return 0

def show_stats(corpus_names=[],genre=None,title=None):
	# loop through corpus names

	if not corpus_names: corpus_names = [c for c,cd in corpora(load=False,incl_meta_corpora=False)]

	for corpus_name in corpus_names:
		# load corpus
		corpus=load_corpus(corpus_name)
		meta=corpus.metadata
		
		# filter for genre
		if genre and 'genre' in meta.columns:
			meta=meta.query(f'genre=="{genre}"')
		if title:
			meta=meta[meta.title.str.lower().str.contains(title)]# | meta.title.str.contains('Essay')]

		# get min/max year
		try:
			minyear=int(meta.year.dropna().min())
			maxyear=int(meta.year.dropna().max())
		except (KeyError,ValueError) as e:
			minyear='?'
			maxyear='?'
			
		# num texts
		numtexts=len(meta)
		
		
		# num words?
		if 'num_words' in meta.columns:
			num_words=sum(meta.num_words)
		else:
			
			
			import p_tqdm as pt
			objs=[(idx,corpus.path_freqs) for idx in meta.id]
			res=[int(x) for x in pmap(do_text, objs) if type(x)==int or type(x)==float]
			num_words=sum(res)
			
		# print desc
		print(f'* *{corpus_name}*: {corpus.desc} ({minyear}-{maxyear}, n={lltk.human_format(numtexts)} texts, {lltk.human_format(num_words)} words)')

def getfreqs(path_freqs,by_ntext=False,by_fpm=False):
	import ujson as json
	with open(path_freqs) as f: freqs=json.load(f)
	if by_ntext: freqs=dict((w,1) for w in freqs)
	if by_fpm:
		total=sum(freqs.values())
		freqs=dict((w,int(c/total*1000000)) for w,c in freqs.items())
	return freqs

def do_gen_mfw(paths_freqs,estimate=True,n=None,by_ntext=False,by_fpm=False,progress=False,desc='',num_proc=1):
	from bounter import bounter
	from collections import Counter
	from tqdm import tqdm
	countd = bounter(1024) if estimate else Counter()
	for freqs in pmap_iter(
		getfreqs,
		paths_freqs,
		desc=desc,
		kwargs=dict(by_ntext=by_ntext, by_fpm=by_fpm),
		progress=progress,
		num_proc=num_proc
	):
		countd.update(freqs)
	return countd

def do_gen_mfw_grp(group,*x,**y):
	import pandas as pd
	from scipy.stats import zscore
	countd = do_gen_mfw(group.path_freqs,*x,**y)
	df=pd.DataFrame([
		{'word':w, 'count':c}
		for w,c in countd.items()
	]).sort_values('count',ascending=False)
	total=df['count'].sum()
	# if y.get('by_fpm'):
		# df['count']=df['count'] / 1000000
	df['fpm']=df['count']/total*1000000
	df['rank']=[i+1 for i in range(len(df))]
	return df



# Add new name for function
load = load_corpus
#################################################################
