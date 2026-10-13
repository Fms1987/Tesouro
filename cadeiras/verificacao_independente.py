import pandas as pd,glob
from fractions import Fraction
fs=lambda p:[f for f in glob.glob(p) if not f.endswith('_BR.csv')]
P=pd.concat([pd.read_csv(f,sep=';',encoding='latin1',dtype=str,usecols=['SG_UF','CD_CARGO','SG_PARTIDO','TP_AGREMIACAO','SG_FEDERACAO','QT_TOTAL_VOTOS_LEG_VALIDOS','QT_VOTOS_NOMINAIS_VALIDOS']) for f in fs('raw/votacao_partido_munzona_2026_??.csv')])
P=P[P.CD_CARGO=='6'].copy()
for c in ['QT_TOTAL_VOTOS_LEG_VALIDOS','QT_VOTOS_NOMINAIS_VALIDOS']:P[c]=P[c].astype(int)
C=pd.concat([pd.read_csv(f,sep=';',encoding='latin1',dtype=str,usecols=['SG_UF','CD_CARGO','SQ_CANDIDATO','SG_PARTIDO','QT_VOTOS_NOMINAIS_VALIDOS']) for f in fs('raw_cand/votacao_candidato_munzona_2026_??.csv')])
C=C[C.CD_CARGO=='6'].copy();C['v']=C.QT_VOTOS_NOMINAIS_VALIDOS.astype(int)
C=C.groupby(['SG_UF','SQ_CANDIDATO','SG_PARTIDO'],as_index=False).v.sum()
a=P.groupby(['SG_UF','SG_PARTIDO']).QT_VOTOS_NOMINAIS_VALIDOS.sum();b=C.groupby(['SG_UF','SG_PARTIDO']).v.sum()
print('nominais divergentes partido x candidato:',int((a.sub(b,fill_value=0)!=0).sum()))
print('votos validos totais:',int(P.QT_TOTAL_VOTOS_LEG_VALIDOS.sum()+P.QT_VOTOS_NOMINAIS_VALIDOS.sum()))
CAD=dict(SP=70,MG=53,RJ=46,BA=39,RS=31,PR=30,PE=25,CE=22,MA=18,GO=17,PA=17,SC=16,PB=12,ES=10,PI=10,AL=9,AM=8,MT=8,MS=8,RN=8,RO=8,SE=8,AC=8,AP=8,DF=8,RR=8,TO=8)
B7={'PT','PCDOB','PV','PSB','PSOL','REDE','PDT'}
fm=P.drop_duplicates(['SG_UF','SG_PARTIDO'])
fm['ea']=fm.SG_FEDERACAO.where(fm.TP_AGREMIACAO=='Federação',fm.SG_PARTIDO)
fm['eb']=fm.ea.where(~fm.SG_PARTIDO.isin(B7),'B')
out=[]
for uf,N in CAD.items():
  for cen,col in (('A','ea'),('B','eb')):
    m=fm[fm.SG_UF==uf].set_index('SG_PARTIDO')[col]
    Pu=P[P.SG_UF==uf];Cu=C[C.SG_UF==uf].copy();Cu['e']=Cu.SG_PARTIDO.map(m)
    V=Pu.assign(e=Pu.SG_PARTIDO.map(m)).groupby('e').QT_TOTAL_VOTOS_LEG_VALIDOS.sum().add(Cu.groupby('e').v.sum(),fill_value=0).astype(int)
    q=Fraction(int(V.sum()),N);qe=int(q)+(1 if q-int(q)>Fraction(1,2) else 0)
    L={e:sorted(g.v[g.v>0],reverse=True) for e,g in Cu.groupby('e')}
    s={e:min(int(V[e]//qe),sum(1 for x in L.get(e,[]) if x*10>=qe)) for e in V.index}
    rem=N-sum(s.values())
    while rem:
        c=[(Fraction(int(V[e]),s[e]+1),e) for e in V.index if V[e]*5>=4*qe and len(L.get(e,[]))>s[e] and L[e][s[e]]*5>=qe]
        if not c:break
        _,e=max(c);s[e]+=1;rem-=1
    while rem:
        c=[(Fraction(int(V[e]),s[e]+1),e) for e in V.index if len(L.get(e,[]))>s[e]]
        _,e=max(c);s[e]+=1;rem-=1
    out+= [(cen,uf,e,n) for e,n in s.items() if V[e]]
ind=pd.DataFrame(out,columns=['cenario','uf','e','s'])
d=pd.read_csv('out/cadeiras_por_uf_entidade.csv');d['e']=d.entidade.where(~d.entidade.str.startswith('BLOCO'),'B')
m=d.merge(ind,on=['cenario','uf','e'],how='outer')
pd.set_option("display.width",250);mm=m[m.cadeiras!=m.s];print(len(m),len(mm));print(mm[["cenario","uf","e","votos","cadeiras","qp","sobras1","sobras2","qe","s"]].head(12).to_string())
# perdas B
p=d.pivot_table(index=['uf','e'],columns='cenario',values='cadeiras',fill_value=0);p['delta']=p.B-p.A
print(p[(p.delta<0)&(p.index.get_level_values(1)!='B')].to_string())
