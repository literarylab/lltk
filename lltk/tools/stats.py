from lltk.imports import *

def newpolyfit(X,Y):
    newdf=pd.DataFrame({'X':X, 'Y':Y})
    results = smf.ols('Y ~ X + I(X**2)', data=newdf).fit()
    return results.rsquared, results.f_pvalue

def regressions(df,resultdf=None):
    word2rp={}
    RRs=[]
    Ps=[]
    for word in df.index:
        Y=list(df.loc[word])
        X=list(range(len(Y)))
        r,p=newpolyfit(X,Y)
        RRs+=[r]
        Ps+=[p]

    if resultdf is None: resultdf=pd.DataFrame(index=df.index)
    resultdf['polyfit_r^2']=RRs
    resultdf['polyfit_p']=Ps
    return resultdf


def dist(df):
    from scipy.spatial.distance import squareform, pdist
    distmatrix=pdist(df,metric='correlation')
    return 1-pd.DataFrame(squareform(distmatrix), columns=df.index, index=df.index)

def kmeans(datadf,df_dist=None,n_kmeans=5,colname='kmeans_cluster',resultdf=None):
    if df_dist is None: df_dist=dist(datadf)
    m_dist=df_dist.values
    from sklearn.cluster import KMeans
    model_kclust = KMeans(n_clusters=n_kmeans)
    model_kclust.fit(m_dist)
    labels = model_kclust.labels_
    word2label = dict(list(zip(datadf.index, labels)))
    if resultdf is None: resultdf=pd.DataFrame(index=datadf.index)
    resultdf[colname]=[word2label[word] for word in datadf.index]
    return resultdf

def corr_with_cluster(df,colname_cluster='kmeans_cluster',resultdf=None):

    cluster_avg={}
    for clust,cluster in resultdf.groupby(by=colname_cluster):
        df_for_cluster = df.loc[cluster.index]
        cluster_avg[clust]=df_for_cluster.median(axis=0)

    word2clustcorr={}
    for word in df.index:
        clust=resultdf.loc[word][colname_cluster]
        word_avgs=list(df.loc[word])
        clust_avgs=list(cluster_avg[clust])
        word2clustcorr[word]=pearsonr(word_avgs,clust_avgs)
    if resultdf is None: resultdf=pd.DataFrame(index=df.index)
    resultdf['kmeans_cluster_corr_r']=[word2clustcorr[word][0] for word in df.index]
    resultdf['kmeans_cluster_corr_p']=[word2clustcorr[word][1] for word in df.index]
    return resultdf

def tsne(datadf,df_dist=None,n_components=2,resultdf=None):
    if df_dist is None: df_dist=dist(datadf)
    m_dist=df_dist.values
    from sklearn.manifold import TSNE
    model = TSNE(n_components=n_components, random_state=0)
    fit = model.fit_transform(m_dist)
    from collections import defaultdict
    newcols=defaultdict(list)
    for i,word in enumerate(datadf.index):
        for ii,xx in enumerate(fit[i]):
            newcols['tsne_V'+str(ii+1)] += [xx]

    if resultdf is None: resultdf=pd.DataFrame(index=datadf.index)
    for k,v in list(newcols.items()): resultdf[k]=v
    return resultdf

def analyze_as_dist(datadf,df_dist=None,n_kmeans=5, do_tsne=True):
    from .tools import now

    if df_dist is None:
        print('>> dist(datadf)',now())
        df_dist=dist(datadf)

    print('>> kmeans(datadf)',now())
    resultdf=kmeans(datadf,n_kmeans=n_kmeans)

    print('>> corr_with_cluster(datadf)',now())
    resultdf=corr_with_cluster(datadf,resultdf=resultdf)

    print('>> regressions(datadf)',now())
    resultdf=regressions(datadf,resultdf=resultdf)

    if do_tsne:
        print('>> tsne(datadf)',now())
        resultdf=tsne(datadf,df_dist=df_dist,resultdf=resultdf)

    return resultdf


def linreg(X, Y):
	from math import sqrt
	from numpy import nan, isnan
	from numpy import array, mean, std, random

	if len(X)<2 or len(Y)<2:
		return 0,0,0
	"""
	Summary
	    Linear regression of y = ax + b
	Usage
	    real, real, real = linreg(list, list)
	Returns coefficients to the regression line "y=ax+b" from x[] and y[], and R^2 Value
	"""
	if len(X) != len(Y):  raise ValueError#, 'unequal length'
	N = len(X)
	Sx = Sy = Sxx = Syy = Sxy = 0.0
	for x, y in map(None, X, Y):
	    Sx = Sx + x
	    Sy = Sy + y
	    Sxx = Sxx + x*x
	    Syy = Syy + y*y
	    Sxy = Sxy + x*y
	det = Sxx * N - Sx * Sx
	a, b = (Sxy * N - Sy * Sx)/det, (Sxx * Sy - Sx * Sxy)/det
	meanerror = residual = 0.0
	for x, y in map(None, X, Y):
	    meanerror = meanerror + (y - Sy/N)**2
	    residual = residual + (y - a * x - b)**2

	RR = 1 - residual/meanerror if meanerror else 1
	ss = residual / (N-2) if (N-2) else 0
	Var_a, Var_b = ss * N / det, ss * Sxx / det
	#print "y=ax+b"
	#print "N= %d" % N
	#print "a= %g \\pm t_{%d;\\alpha/2} %g" % (a, N-2, sqrt(Var_a))
	#print "b= %g \\pm t_{%d;\\alpha/2} %g" % (b, N-2, sqrt(Var_b))
	#print "R^2= %g" % RR
	#print "s^2= %g" % ss
	return a, b, RR

def reset_index(df):
	'''Returns DataFrame with index as columns'''
	index_df = df.index.to_frame(index=False)
	df = df.reset_index(drop=True)
	#  In merge is important the order in which you pass the dataframes
	# if the index contains a Categorical. 
	# pd.merge(df, index_df, left_index=True, right_index=True) does not work
	return pd.merge(index_df, df, left_index=True, right_index=True)


def to_tf(dtm):
    dfq=dtm.select_dtypes('number')
    rowsums = dfq.sum(axis=1)
    return dfq.div(rowsums,axis=0)


def to_tfidf(dtm):
    import numpy as np,pandas as pd
    dtm_tf = to_tf(dtm)

    # idf
    num_docs = len(dtm_tf)
    num_docs_per_word = dtm_tf[dtm_tf>0].count()
    idf=np.log10(num_docs / num_docs_per_word)

    return dtm_tf.apply(lambda x: x * idf,axis='columns')

def to_mdw(dtm,groupby,agg='median'):
    df = dtm.groupby(groupby).agg(agg).T
    df=reset_index(df).rename({0:'word'},axis=1)#.set_index('word')
    return df.set_index('word')

def to_counts(dtm,scale_by=1000000,**y):
    return pmap_apply_cols(
        rescale_col,
        dtm,
        kwargs=dict(scale_by=scale_by),
        **y
    )



def pmap_apply_cols(func, df, lim=None, **y):
    from yapmap import pmap
    cols=list(df.columns)[:lim]
    new_seriess = pmap(
        func,
        [df[col].values for col in cols],
        **y
    )
    odf=pd.DataFrame(dict(zip(cols,new_seriess)), index=df.index)
    return odf



def rescale_col(colvals,scale_by=1000000,as_int=True):
    maxval=max(colvals)
    minval=min(colvals)
    if minval>=1: return colvals
    if minval<0: 
        print(f'!! Negative values in column {col}')
        return colvals
    return [
        x*scale_by if not as_int else int(x*scale_by)
        for x in colvals
    ]


def do_mannwhitney(obj):
    x,y,meta=obj
    from scipy.stats import mannwhitneyu,zscore
    try:
        xz=zscore(x)
        yz=zscore(y)
        mwU, pvalue = mannwhitneyu(x,y)
        result_dict=dict(meta.items())
        result_dict['U']=mwU
        result_dict['pvalue']=pvalue
        result_dict['is_signif']=issign=pvalue<=0.05
        result_dict['group1_mean']=xm=x.mean()
        result_dict['group2_mean']=ym=y.mean()
        result_dict['distinctive_of']=None if not issign else (
            meta.get('group1') if xm>ym else meta.get('group2')
        )
        return result_dict
    except ValueError as e:
        # print('!!',e,meta)
        return meta


def to_mdw_mannwhitney(dtm,groupby,words=set(),group_names=None,progress=False,**pmap_kwargs):
    from yapmap import pmap_iter
    from scipy.stats import zscore
    
    # get words
    groups = dtm.groupby(groupby)
    if not words:
        for gname,gdf in groups:
            words = set(gdf.columns) if not words else words&set(gdf.columns)

    objs=[]
    for group1name,group1df in groups:
        for group2name,group2df in groups:
            if group1name>=group2name: continue
            for word in words:
                x=group1df[word]
                y=group2df[word]
                meta={
                    'group1':group1name,
                    'group2':group2name,
                    'word':word,
                }
                objs+=[(x,y,meta)]
    odf = pd.DataFrame(
        pmap_iter(
            do_mannwhitney,
            objs,
            progress=progress,
            **pmap_kwargs
        )
    ).sort_values('U')
    
    odf=odf.sort_values(['distinctive_of','U'],ascending=[True,False])
    odf=odf.set_index(['distinctive_of','group1','group2','word'])
    odf['U_z']=zscore(odf['U'])
    return odf