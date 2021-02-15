import os
import lltk
from lltk.text import Text
from lltk.corpus import Corpus



class TextFanFic(Text):
	pass



class FanFic(Corpus):
	TEXT_CLASS=TextFanFic

	def compile(self,**attrs):
		"""
		This is a custom installation function. By default, it will simply try to download itself,
		unless a custom function is written here which either installs or provides installation instructions.
		"""
		return self.download(**attrs)

	@property
	def metadata(self):
		"""
		Magic attribute loading metadata, and doing any last minute customizing
		"""
		meta=super().metadata
		meta['genre']='FanFiction'
		meta['year']=meta['published'].apply(lambda x: x.split('/')[-1])
		meta['year']=meta['year'].apply(lambda y: int('20'+str(y)) if int(str(y)[0])<5 else int('19'+str(y)))
		meta['author']=meta['username']
		return meta

