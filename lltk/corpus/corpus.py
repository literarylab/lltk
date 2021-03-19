from lltk.imports import *

def fixpath(path):
	if type(path)==str and path and '~' in path:
		path=path.split('~')[-1]
		path=os.path.join(os.path.expanduser('~'), path[1:])
	return path




class Corpus(object):
	EXT_TXT='.txt'
	EXT_XML='.xml'
	EXT_FREQS='.json'
	COL_ID='id'
	COL_FN='fn'
	EXT_HDR='.hdr'
	ENCODING_TXT = 'utf-8'
	ENCODING_XML = 'utf-8'
	TYPE='Corpus'
	TEXT_CLASS=Text
	TOKENIZER=tokenize
	MODERNIZE=MODERNIZE_SPELLING
	LANG='en'
	XML2TXT = default_xml2txt

	def __init__(self,load_meta=False,**attrs):
		self._metadf=None
		self._texts=None
		self._textd=None
		self._dtmd={}
		self._mfwd={}
		for k,v in attrs.items():
			if k.startswith('path_'): v=fixpath(v)
			setattr(self,k,v)
		if load_meta:
			try:
				self.load_metadata()
			except Exception:
				pass
	#####
	# Metadata
	####
	@property
	def t(self):
		return random.choice(self.texts())

	@property
	def au(self): return self.authors

	@property
	def authors(self,authorkey='author',titlekey='title',idkey=COL_ID):
		if not hasattr(self,'_authors') or not self._authors:
			if self._metadf is None or self._textd is None: 
				self.load_metadata()
				return self.authors

			self._authors=au=Bunch()
			# for author,authordf in tqdm(list(self._metadf.reset_index().groupby(authorkey)),desc='Creating author/title shortcut attributes'):
			for author,authordf in self._metadf.reset_index().groupby(authorkey):
				if not author.strip(): continue
				akey=to_authorkey(author)
				aobj=AuthorBunch(corpus=self,name=author)
				setattr(self._authors,akey,aobj)
				for i,row in authordf.iterrows():
					title=row[titlekey]
					idx=row[idkey]
					tkey=to_titlekey(title)
					tobj=self._textd.get(idx)
					setattr(aobj,tkey,tobj)
		return self._authors

	def load_metadata(self,clean=True,add_text_col=False,text_col='_text'):
		if self._metadf is None:	
			# meta=read_df(self.path_metadata).set_index(self.col_id,drop=False).fillna('')
			if not os.path.exists(self.path_metadata):
				# print(f'!!! No metadata file exists at {self.path_metadata}')
				return pd.DataFrame() 
			meta=read_df(self.path_metadata, dtype={self.col_id:str}).fillna('')
			if not self.col_id in meta.columns:
				if self.col_fn in meta.columns:
					meta[self.col_id]=meta[self.col_fn].apply(lambda x: os.path.splitext(x)[0])
			if clean: meta=clean_meta(meta)
			if self.year_start is not None and str(self.year_start).isdigit() and 'year' in meta.columns:
				meta=meta.query(f'year>={self.year_start}')
			if self.year_end is not None and str(self.year_end).isdigit() and 'year' in meta.columns:
				meta=meta.query(f'year<={self.year_end}')
			self._metadf=meta.set_index(self.col_id,drop=True)

		# create text objects
		if not self._texts or not self._textd:
			self._texts,self._textd=[],{}
			for i,row in self._metadf.reset_index().iterrows():
				idx=row[self.col_id] if self.col_id in row else row.index
				t=self.TEXT_CLASS(idx,self,meta=dict(row))
				self._texts.append(t)
				self._textd[idx]=t
			if add_text_col:
				self._metadf[text_col]=self._texts
				


		# self.authors
		return self._metadf

	@property
	def meta(self):
		if self._metadf is None: self.load_metadata()
		return self._metadf if self._metadf is not None else pd.DataFrame()
	@property
	def metadf(self):
		return self.meta.reset_index() if len(self.meta) else self.meta
	
	@property
	def metadata(self,*x,**y): return self.meta

	# Get texts
	def texts(self,text_ids=None):
		if not self._texts: self.load_metadata()
		return [
			t
			for t in self._texts
			if text_ids is None
			or t.id in set(to_textids(text_ids))
		]
	
	# Convenience
	@property
	def num_texts(self): return len(self.meta)
	@property
	def textd(self): return self._textd if self._textd is not None else {}
	@property
	def text_ids(self): return list(self.meta.id)


	# # Groups?
	# def new_grouping(self):
	# 	return CorpusGroups(self)


	#################
	#### PROCESSING
	#################

	def preprocess_txt(self,force=False,num_proc=DEFAULT_NUM_PROC,verbose=True,**attrs): #force=False,slingshot=False,slingshot_n=1,slingshot_opts=''):
		if not self._texts: return
		paths = [(t.path_xml,t.path_txt) for t in self.texts() if t.path_xml and os.path.exists(t.path_xml)]
		if not paths:
			if verbose: self.log('No XML files to produce plain text files from')
			return
		objs = [
			(pxml,ptxt,self.XML2TXT.__func__)
			for pxml,ptxt in paths
			if force or not os.path.exists(ptxt)
		]
		if not objs:
			if verbose: self.log('Plain text files already saved')
			return
		tools.pmap(
			do_preprocess_txt,
			objs,
			num_proc=num_proc,
			desc=f'[{self.name}] Saving plain text versions of XML files',
			**attrs
		)

	def preprocess_freqs(self,force=False,kwargs={},verbose=True,**attrs): #force=False,slingshot=False,slingshot_n=1,slingshot_opts=''):
		objs = [
			(t.path_txt,t.path_freqs,self.TOKENIZER.__func__)
			for t in self.texts()
			if os.path.exists(t.path_txt) and (force or not os.path.exists(t.path_freqs))
		]
		if not objs:
			if verbose:
				self.log('Word freqs already saved')
			return
		# print('parallel',parallel)
		tools.pmap(
			save_freqs_json,
			objs,
			kwargs=kwargs,
			desc=f'[{self.name}] Saving word freqs as jsons',
			**attrs
		)
		

	



	


	def zip(self,savedir=PATH_CORPUS_ZIP,ask=False,parts=ZIP_PART_DEFAULTS):
		if not os.path.exists(savedir): os.makedirs(savedir)
		here=os.getcwd()
		## ask which parts
		if not parts and ask:
			part2ok=defaultdict(None)
			for part in sorted(parts):
				path_part=getattr(self,f'path_{part}')
				if not path_part or not os.path.exists(path_part): continue
				part2ok[part]=input('>> [%s] Zip %s file(s)?: ' % (self.name, part)).strip().lower().startswith('y') if ask else True
		elif parts:
			part2ok=dict((part,True) for part in parts)
		else:
			return

		def _paths(path,pathpart=''):
			# paths in folder
			paths = []
			for root, dirs, files in os.walk(path):
				for file in files:
					ofnfn=os.path.join(root, file)
					paths.append(ofnfn)
			if pathpart=='raw': return paths
			# do they belong to this corpus?
			try:
				acceptable_paths = {getattr(t,f'path_{pathpart}') for t in self.texts()}
				acceptable_paths = {
					p.replace(
						os.path.dirname(getattr(self,f'path_{pathpart}'))+os.path.sep,
						''
					) for p in acceptable_paths
				}
				# print('orig paths',list(paths)[:5])
				# print('ok paths',list(acceptable_paths)[:5])
				paths = list(set(paths) & acceptable_paths)
			except Exception:
				pass
			return paths
			

		def zipdir(path, ziph, pathpart='', paths=None):
			# ziph is zipfile handle
			if not paths: paths=_paths(paths,pathpart)
			for ofnfn in paths:
				ziph.write(ofnfn)
				yield ofnfn

		def do_zip(path,fname,msg='Zipping files',default=False, pathpart=''):
			if not os.path.exists(path): return
			#if ask and input('>> {msg}? [{path}]\n'.format(msg=msg,path=path)).strip()!='y': return
			if not default: return

			if not fname.endswith('.zip'): fname+='.zip'
			opath=os.path.join(savedir,fname)

			path1,path2=os.path.split(path)

			with zipfile.ZipFile(opath,'w',zipfile.ZIP_DEFLATED) as zipf:
				os.chdir(path1)
				paths=list(_paths(path2,pathpart)) if os.path.isdir(path2) else [path2]
				#print(type(paths),paths[:3])
				zipper = zipdir(path2, zipf, pathpart=pathpart, paths=paths)
				for ofnfn in tqdm(zipper, total=len(paths), desc=f'[{self.name}] Compressing {fname}'):
					pass

		for part in part2ok:
			if not part2ok[part]: continue
			do_zip(getattr(self,f'path_{part}'), f'{self.id}_{part}.zip', f'Zip {part} files',part in parts,pathpart=part)
		os.chdir(here)
		# do_zip(self.path_txt, self.id+'_txt.zip','Zip txt files','txt' in parts)
		# do_zip(self.path_freqs, self.id+'_freqs.zip','Zip freqs files','freqs' in parts)
		# do_zip(self.path_metadata, self.id+'_metadata.zip','Zip metadata file','metadata' in parts)
		# do_zip(self.path_xml, self.id+'_xml.zip','Zip xml files','xml' in parts)
		# do_zip(self.path_data, self.id+'_data.zip','Zip data files (mfw/dtm)','xml' in parts)


	def uninstall(self):
		# Start from scratch
		pass


	def upload(self,ask=False,uploader='dbu upload',dest=DEST_LLTK_CORPORA,zipdir=None,overwrite=False,parts=ZIP_PART_DEFAULTS):
		#if not overwrite: uploader+=' -s'
		if not zipdir: zipdir=os.path.join(PATH_CORPUS,'lltk_corpora')
		here=os.getcwd()
		os.chdir(zipdir)
		#print('?',zipdir,os.listdir('.'))
			

		cmds=[]
		for fn in os.listdir('.'):
			if not fn.endswith('.zip'): continue
			if not fn.startswith(self.id): continue
			if not parts:
				if ask:
					if not input(f'>> [{self.name}] Upload {fn}? ').strip().lower().startswith('y'): continue
			else:
				part=fn.replace('.zip','').split('_')[-1]
				if part not in set(parts): continue
			
			cmd='{upload} {file} {dest}'.format(upload=uploader,file=fn,dest=dest)
			cmds.append(cmd)
		# cmdstr="\n".join(cmds)
		# print(f'Executing:\n{cmdstr}')

		for cmd in tqdm(cmds,desc=f'[{self.name}] Uploading zip files'):
			os.system(cmd)
		
		os.chdir(here)

	def share(self,cmd_share='dbu share',dest=DEST_LLTK_CORPORA):
		ol=[]
		import subprocess
		ln='['+self.name+']'
		print(ln)
		ol+=[ln]
		for part in ZIP_PART_DEFAULTS:
			fnzip = self.id+'_'+part+'.zip'
			cmd=cmd_share+' '+os.path.join(dest,fnzip)
			try:
				out=str(subprocess.check_output(cmd.split()))
			except (subprocess.CalledProcessError,ValueError,TypeError) as e:
				#print('!!',e)
				continue
			link=out.strip().replace('\n','').split('http')[-1].split('?')[0]
			if link: link='http'+link+'?dl=1'

			url='url_'+part+' = '+link
			print(url)
			ol+=[url]
		print()
		return '\n'.join(ol)


	def mkdir_root(self):
		if not os.path.exists(self.path_root): os.makedirs(self.path_root)

	
	def urls(self):
		urls=[(x[4:], getattr(self,x)) for x in dir(self) if x.startswith('url_') and getattr(self,x)]
		return urls

	def compile(self, **attrs):
		## THIS NEEDS TO BE OVERWRITTEN BY CHILD CLASS
		return

	def info(self):
		ol = []
		ol += [f'[{self.name}]']
		for x in ['id','desc','link','public']:
			xstr=x
			v=getattr(self,x)
			if v: ol+=[f'{xstr}: {v}']
		print('\n'.join(ol))

	def install(self, ask=True, urls={}, force=False, part=None, flatten=False, parts=None, unzip=True, **attrs):
		if not parts: parts=DOWNLOAD_PART_DEFAULTS
		if type(parts)==str: parts=[p.strip().lower() for p in parts.split(',')]
		if not part and parts:
			for part in parts: self.install(ask=ask, urls=urls, part=part, parts=[], force=force, **attrs)
			return self
		if not part: return
		opath=getattr(self,f'path_{part}')
		tmpfnfn=self.path_zip(part)
		tmpfn=os.path.basename(tmpfnfn)
		if not os.path.exists(tmpfnfn):
			if not urls: urls=dict(self.urls())
			url=urls.get(part)
			if not url: return
			# self.mkdir_root()
			tmpfnfndir=os.path.dirname(tmpfnfn)
			if not os.path.exists(tmpfnfndir): os.makedirs(tmpfnfndir)
			tools.download(url,tmpfnfn,desc=f'[{self.name}] Downloading {tmpfn}',force=force)
		if unzip:
			opath=self.path_raw if part=='raw' else self.path_root
			tools.unzip(tmpfnfn,opath,desc=f'[{self.name}] Unzipping {tmpfn}',flatten=flatten)
			#if os.path.exists(self.path_raw) and os.listdir(self.path_raw)==['raw']:
			#	os.rename(os.path.join(self.path_raw,'raw'), self.path_raw)
		return self

	def path_zip(self,part):
		return os.path.join(PATH_CORPUS_ZIP,f'{self.id}_{part}.zip')
	

	def compile_download(self,unzip=True):
		return self.install(part='raw',unzip=unzip)

	def preprocess(self,parts=PREPROC_CMDS,verbose=True,force=False,num_proc=DEFAULT_NUM_PROC,**attrs):
		if not parts: parts=PREPROC_CMDS
		if type(parts)==str: parts=[p.strip().lower() for p in parts.split(',')]
		for part in parts:
			fname='preprocess_'+part
			if not hasattr(self,fname): continue
			func=getattr(self,fname)
			x=func(verbose=verbose,num_proc=int(num_proc),force=force, **attrs)

	def preprocess_misc(self): pass

	def has_data(self,part):

		ppart=f'path_{part}'
		if not hasattr(self,ppart): return
		path=getattr(self,ppart)
		if not os.path.exists(path): return False
		if os.path.isdir(path) and not os.listdir(path): return False
		# print(part,ppart,path,os.path.exists(path))
		
		return path



	def has_url(self,part):
		ppart=f'url_{part}'
		if not hasattr(self,ppart): return False
		if not getattr(self,ppart): return False
		return getattr(self,ppart)


	@property
	def df(self): return self.metadf

	@property
	def addr2meta(self):
		if not hasattr(self,'_addr2meta'):
			self._addr2meta=a2m={}
			for t in self.texts():
				meta=t.meta
				a2m[t.addr]=meta
		return self._addr2meta

	@property
	def metad(self):
		if not hasattr(self,'_metad'):
			#if not hasattr(self,'_meta'): self.meta
			self._metad=dict(list(zip(self.text_ids,self.meta)))
		return self._metad

	def export(self,folder,meta_fn=None,txt_folder=None,compress=False):
		"""
		Exports everything to a folder.
		"""
		if not os.path.exists(folder): os.makedirs(folder)
		if not meta_fn: meta_fn='corpus-metadata.%s.txt' % self.name
		if not txt_folder: txt_folder='texts'

		# save metadata
		meta_fnfn=os.path.join(folder,meta_fn)
		self.save_metadata(meta_fnfn)

		# save texts
		txt_path=os.path.join(folder,txt_folder)
		if not os.path.exists(txt_path): os.makedirs(txt_path)
		import shutil
		for t in self.texts():
			ifnfn=t.path_txt
			if not os.path.exists(ifnfn): continue
			ofnfn=os.path.join(txt_path, t.id+t.ext_txt)
			ofnfn_path=os.path.split(ofnfn)[0]
			if not os.path.exists(ofnfn_path): os.makedirs(ofnfn_path)
			shutil.copyfile(ifnfn,ofnfn)
			#break






	### FREQS


	def dtm(self,words=[],texts=None,n=DEFAULT_MFW_N,tf=False,tfidf=False,meta=False,na=0.0,**mfw_attrs):
		dtm=self.preprocess_dtm(texts=texts, words=words,n=n,**mfw_attrs)
		dtm=dtm.set_index(self.col_id) if self.col_id in set(dtm.columns) else dtm
		if texts is not None:
			dtm=dtm.loc[[w for w in to_textids(texts) if w in set(dtm.index)]]

		if tf: dtm=to_tf(dtm)
		if tfidf: dtm=to_tfidf(dtm)
		if meta:
			if type(meta) in {list,set}:
				if not self.col_id in meta: meta=[self.col_id]+list(meta)
			mdf=self.metadf[meta] if type(meta) in {list,set} else self.metadf
			mdtm=mdf.merge(dtm,on=self.col_id,suffixes=('','_w'),how='right')
			micols = mdf.columns
			dtm=mdtm.set_index(list(micols))
		return dtm.fillna(na) 

	def mdw(self,groupby,words=[],texts=None,tfidf=True,keep_null_cols=False,remove_zeros=True,agg='median',**mfw_attrs):
		texts=self.metadf[self.metadf.id.isin(to_textids(texts))] if texts is not None else self.metadf
		if not keep_null_cols: 
			texts=texts.loc[[bool(x) for x in texts[groupby]]]
		
		df=self.dtm(words=words,texts=texts,tfidf=tfidf, meta=[groupby],**mfw_attrs).groupby(groupby)
		df=to_mdw(df,agg=agg)
		# for col in df.columns:
		# 	if not col:
		# 		df=df.drop(col,axis=1)
		df=df.sort_values(list(df.columns)[0],ascending=False)
		if remove_zeros: df=df[df.sum(axis=1)>0]
		return df

	# @property
	# def path_mfw(self):
	# 	if not os.path.exists(self.path_data): os.makedirs(self.path_data)
	# 	return os.path.join(self.path_data, 'mfw.h5')
	# @property
	# def path_dtm(self):
	# 	if not os.path.exists(self.path_data): os.makedirs(self.path_data)
	# 	return os.path.join(self.path_data, 'dtm.h5')
	@property
	def path_mfw(self):
		path_mfw=os.path.join(self.path_data,'mfw')
		if not os.path.exists(path_mfw): os.makedirs(path_mfw)
		return path_mfw
	@property
	def path_dtm(self):
		path_dtm=os.path.join(self.path_data,'dtm')
		if not os.path.exists(path_dtm): os.makedirs(path_dtm)
		return path_dtm
	@property
	def path_home(self):
		return os.path.join(PATH_CORPUS,self.id)
	@property
	def path_texts(self):
		return os.path.join(self.path_home,'texts')



	#########
	# MFW
	#########

	# pos?
	


	def mfw_df(self,
			n=None,
			words=None,
			texts=None,
			yearbin=None,
			by_ntext=False,
			n_by_period=None,
			keep_periods=True,
			n_agg='median',
			min_count=None,
			col_group='period',
			excl_stopwords=False,
			excl_top=0,
			valtype='fpm',
			min_periods=None,
			by_fpm=False,
			only_pos=set(),
			force=False,
			keep_pos=None,
			**attrs):
		
		# gen if not there?
		if yearbin is None: yearbin=self.mfw_yearbin
		if n is None: n=self.mfw_n
		if type(yearbin)==str: yearbin=int(yearbin)
		df = self.preprocess_mfw(
			n=n,
			words=words,
			texts=texts,
			yearbin=yearbin,
			by_ntext=by_ntext,
			by_fpm=by_fpm,
			col_group=col_group,
			force=False,
			try_create_freqs=True,
			**attrs
		)
		if df is None:
			self.log('Could not load or generate MFW')
			return
		df=df.fillna(0)

		if words is not None: df=df[df.word.isin(words)]

		if excl_top:
			df=df[df['rank']>=excl_top]

		if excl_stopwords:
			stopwords=get_stopwords()
			df=df[~df.word.isin(stopwords)]

		if min_count: df = df[df['count']>=min_count]

		if min_periods and min_periods>1:
			num_periods_per_word = df[df['count']>0].groupby('word').size()
			if num_periods_per_word.max()>1:
				ok_words=set(num_periods_per_word[num_periods_per_word>=min_periods].index)
				df=df[df.word.isin(ok_words)]
		if only_pos:
			w2p=get_word2pos(lang=self.lang)
			def word_ok(w):
				wpos=w2p.get(w.lower())
				if not wpos: return False
				for posx in only_pos:
					# print(posx,wpos,only_pos)
					if posx==wpos: return True
					if posx.endswith('*') and wpos.startswith(posx[:-1]): return True
				return False
			df=df[df.word.apply(word_ok)]
			# df['pos']=df.word.replace(w2p)
			# df['pos0']=df.pos.apply(lambda x: x[0] if x else '')

		## now pivot
		dfi=df.reset_index()
		has_period = col_group in dfi.columns
		if n: # limit to overall
			if not n_by_period:
				if has_period:
					dfpiv = dfi.pivot(col_group,'word',valtype).fillna(0)
					# print(dfpiv.median().sort_values(ascending=False))
					topNwords=list(dfpiv.median().sort_values(ascending=False).iloc[:int(n)].index) #iloc[excl_top:excl_top+n]
				else:
					topNwords=dfi.sort_values(valtype,ascending=False).iloc[:int(n)].word
				df=df[df.word.isin(set(topNwords))]
			elif has_period:
				df = df.dropna().sort_values('rank').groupby(col_group).head(n)

		if not keep_periods or not has_period:
			# agg by word
			df=df.groupby('word').agg(n_agg)
			df['ranks_avg']=df['rank']
			df=df.sort_values(valtype,ascending=False)
			df['rank']=[i+1 for i in range(len(df))]
		
		# dfr=df.reset_index()
		# odf = odf[odf.columns[1:] if set(odf.columns) and odf.columns[0]=='index' else odf.columns]
		dfr=df#.reset_index() if not 'id' in df

		## add back pos?
		if keep_pos is not False:
			w2pdf=get_word2pos_df(lang=self.lang)
			w2pdf['pos0']=w2pdf['pos'].apply(lambda x: x[0] if type(x)==str and x else '')
			# w2pdf['pos'],w2pdf['pos0']=w2pdf['pos0'],w2pdf['pos']
			dfr=dfr.merge(w2pdf,on='word')
			

		return dfr



	def mfw(self,*x,**y):
		y['keep_periods']=False
		df=self.mfw_df(*x,**y)
		try:
			return list(df.reset_index().word)
		except Exception:
			return []



	def to_texts(self,texts):
		if issubclass(texts.__class__, pd.DataFrame) and self.col_id in set(texts.reset_index().columns):
			return [self.textd[idx] for idx in texts.reset_index()[self.col_id]]
		# print(type(texts), texts)
		return [
			x if (Text in x.__class__.mro()) else self.textd[x]
			for x in texts
		]

	def preprocess_mfw(self,
			texts=None,
			words=None,
			yearbin=None,
			year_min=None,
			year_max=None,
			by_ntext=False,
			by_fpm=False,
			num_proc=DEFAULT_NUM_PROC,
			col_group='period',
			estimate=True,
			force=False,
			verbose=True,
			try_create_freqs=True,
			pos=set(),
			**attrs
		):
		"""
		From tokenize_texts()
		"""
		if yearbin is None: yearbin=self.mfw_yearbin
		if type(yearbin)==str: yearbin=int(yearbin)
		texts=self.texts() if texts is None else texts
		texts=self.to_texts(texts)
		texts=[t for t in texts if (not year_min or t.year>=year_min) and (not year_max or t.year<year_max)]
		
		key=self.mfwkey(yearbin,by_ntext,by_fpm,texts)
		keyfn=os.path.join(self.path_mfw,key+'.ft')
		
		if key in self._mfwd: return self._mfwd[key]
		
		if not force and os.path.exists(keyfn):
			# if verbose: self.log(f'MFW is cached for key {key}')
			if verbose: self.log(f'Loading MFW from {ppath(keyfn)}')
			df=read_df(keyfn)
			self._mfwd[key]=df
			# return df
		else:
			period2texts = divide_texts_historically(yearbin=yearbin,texts=texts)
			old=[]
			paths_freqs=[]
			for period,texts in sorted(period2texts.items()):
				period_paths_freqs=[]
				for i,t in enumerate(texts):
					if not os.path.exists(t.path_freqs): continue
					ptdx={col_group:period, 'path_freqs':t.path_freqs}
					paths_freqs.append(ptdx)
			if not len(paths_freqs):
				if verbose: self.log('No freqs files found to generate MFW')
				if try_create_freqs:
					self.preprocess_freqs()
					return self.preprocess_mfw(
						yearbin=yearbin,
						year_min=year_min,
						year_max=year_max,
						by_ntext=by_ntext,
						by_fpm=by_fpm,
						num_proc=num_proc,
						col_group=col_group,
						# n=n,
						estimate=estimate,
						force=force,
						verbose=verbose,
						try_create_freqs=False
					)
				return pd.DataFrame()

			pathdf=pd.DataFrame(paths_freqs)
			# run
			odf = pmap_groups(
				do_gen_mfw_grp,
				pathdf.groupby(col_group),
				num_proc=num_proc,
				kwargs={
					'by_ntext':by_ntext,
					'estimate':estimate,
					'by_fpm':by_fpm,
					'progress':yearbin is False,
					'desc':f'[{self.name}] Counting overall most frequent words (MFW)',
					'num_proc':num_proc if yearbin is False else 1
				},
				desc=f'[{self.name}] Counting most frequent words across {yearbin}-year periods',
				progress=yearbin is not False
			)
			if odf is None or not len(odf): return pd.DataFrame()
			
			if yearbin is not False:
				odf=odf.reset_index().sort_values(['period','rank'])
			else:
				odf=odf.reset_index().sort_values('rank')
			#odf.to_csv(self.path_mfw.replace('.txt','.csv'))
			odf = odf[odf.columns[1:] if set(odf.columns) and odf.columns[0]=='index' else odf.columns]
			if verbose: self.log(f'Saving MFW to {ppath(keyfn)}')
			save_df(odf, keyfn)
			self._mfwd[key]=odf
		return self._mfwd[key]


	def log(self,*x,**y):
		print(f'[{self.name}]',*x,**y)


	###################################
	# DTM
	###################################

	def mfwkey(self,yearbin,by_ntext,by_fpm,texts):
		if type(yearbin)==str: yearbin=int(yearbin)
		tids=tuple(sorted(to_textids(texts)))
		return hashstr(str((yearbin, int(by_ntext), int(by_fpm), tids)))[:12]

	def wordkey(self,words):
		return hashstr('|'.join(sorted(list(words))))[:12]
	def preprocess_dtm(
			self,
			texts=None,
			words=[],
			n=DEFAULT_MFW_N,
			num_proc=DEFAULT_NUM_PROC,
			wordkey=None,
			sort_cols_by='sum',
			force=False,
			verbose=True,
			**attrs
		):
		
		
		if not words: words=self.mfw(texts=texts,n=n,num_proc=num_proc,force=force,**attrs)
		wordset = set(words)
		# print(len(wordset))
		if not wordkey: wordkey=self.wordkey(words)
		if wordkey in self._dtmd: return self._dtmd[wordkey]
		keyfn=os.path.join(self.path_dtm,wordkey+'.ft')
		if not force:
			if os.path.exists(keyfn):
				# if verbose: self.log(f'DTM already saved for key {key}')
				if verbose: self.log(f'Loading DTM from {ppath(keyfn)}')
				df=read_df(keyfn)
				self._dtmd[wordkey]=df
				return df

		# get
		objs = [
			(t.path_freqs,wordset,{self.col_id:t.id})
			for t in self.texts()
			if os.path.exists(t.path_freqs) and len(wordset) and t.id
		]
		
		if not objs:
			if verbose: self.log(f'No frequency files found to generate DTM. Run preprocess_freqs()?')
			return

		ld = pmap(
			get_dtm_freqs,
			objs,
			num_proc=num_proc,
			desc=f'[{self.name}] Assembling document-term matrix (DTM)'
		)

		# return
		dtm = pd.DataFrame(ld).set_index(self.col_id,drop=True).fillna(0)
		dtm = dtm.reindex(dtm.agg(sort_cols_by).sort_values(ascending=False).index, axis=1)

		# df.to_csv(self.path_dtm)
		# df.reset_index().to_feather(self.path_dtm)
		if verbose: self.log(f'Saving DTM to {ppath(keyfn)}')
		save_df(dtm.reset_index(), keyfn)
		self._dtmd[wordkey]=dtm
		return dtm
















	### WORD2VEC
	@property
	def model(self):
		if not hasattr(self,'_model'):
			self._model=gensim.models.Word2Vec.load(self.fnfn_model)
		return self._model

	@property
	def fnfn_skipgrams(self):
		return os.path.join(self.path_skipgrams,'skipgrams.'+self.name+'.txt.gz')

	def word2vec(self,skipgram_n=10,name=None,skipgram_fn=None):
		if not name: name=self.name
		from lltk.model.word2vec import Word2Vec
		if skipgram_fn and not type(skipgram_fn) in [six.text_type,str]:
			skipgram_fn=self.fnfn_skipgrams

		return Word2Vec(corpus=self, skipgram_n=skipgram_n, name=name, skipgram_fn=skipgram_fn)

	def doc2vec(self,skipgram_n=5,name=None,skipgram_fn=None):
		if not name: name=self.name
		from lltk.model.word2vec import Doc2Vec
		if not skipgram_fn or not type(skipgram_fn) in [six.text_type,str]:
			skipgram_fn=os.path.join(self.path_skipgrams,'sentences.'+self.name+'.txt.gz')

		return Doc2Vec(corpus=self, skipgram_n=skipgram_n, name=name, skipgram_fn=skipgram_fn)

	def word2vec_by_period(self,bin_years_by=None,word_size=None,skipgram_n=10, year_min=None, year_max=None):
		"""NEW word2vec_by_period using skipgram txt files
		DOES NOT YET IMPLEMENT word_size!!!
		"""
		from lltk.model.word2vec import Word2Vec
		from lltk.model.word2vecs import Word2Vecs

		if not year_min: year_min=self.year_start
		if not year_max: year_max=self.year_end

		path_model = self.path_model
		model_fns = os.listdir(path_model)
		model_fns2=[]
		periods=[]

		for mfn in model_fns:
			if not (mfn.endswith('.txt') or mfn.endswith('.txt.gz')) or '.vocab.' in mfn: continue
			mfn_l = mfn.split('.')
			period_l = [mfn_x for mfn_x in mfn_l if mfn_x.split('-')[0].isdigit()]
			if not period_l: continue

			period = period_l[0]
			period_start,period_end=period.split('-') if '-' in period else (period_l[0],period_l[0])
			period_start=int(period_start)
			period_end=int(period_end)+1
			if period_start<year_min: continue
			if period_end>year_max: continue
			if bin_years_by and period_end-period_start!=bin_years_by: continue
			model_fns2+=[mfn]
			periods+=[period]

		#print '>> loading:', sorted(model_fns2)
		#return

		name_l=[self.name, 'by_period', str(bin_years_by)+'years']
		if word_size: name_l+=[str(word_size / 1000000)+'Mwords']
		w2vs_name = '.'.join(name_l)
		W2Vs=Word2Vecs(corpus=self, fns=model_fns2, periods=periods, skipgram_n=skipgram_n, name=w2vs_name)
		return W2Vs






