# Leveraged ETFs, Long and Short, Mapped to the Underlying

One pick per side per underlying: the fund with the highest average daily dollar volume over the last 20 sessions (as of Nov 19, 2026). Leverage 1.5x or more either way. 574 long funds, 120 short funds, 315 underlyings.

![Leveraged ETF map](map.png)

Data: [best_per_underlying.csv](data/best_per_underlying.csv) (one long + one short pick per underlying), [all_long_etfs.csv](data/all_long_etfs.csv), [all_inverse_etfs.csv](data/all_inverse_etfs.csv). Dark HTML version: [index.html](index.html).

## Broad index

| Underlying | Long | Avg $/day | Other longs | Short | Avg $/day | Other shorts |
|---|---|---|---|---|---|---|
| QQQ | **TQQQ** +3x | $5.3B | QLD, QQUP, EQQQ, QQXL | **SQQQ** -3x | $2.6B | QID, QQDN |
| SPY | **SPXL** +3x | $646M | UPRO, SSO, SPYU, SPUU, SPYQ, USLX | **SPXU** -3x | $453M | SPXS, SDS |
| IWM | **TNA** +3x | $302M | URTY, UWM, USSX | **TZA** -3x | $244M | SRTY, TWM |
| DIA | **UDOW** +3x | $148M | DDM | **SDOW** -3x | $119M | DXD |
| Innovation 100 | **MQQQ** +2x | $16M | QQQP | — |  |  |
| S&P 500 High Beta | **HIBL** +3x | $5.7M |  | **HIBS** -3x | $5.8M |  |
| Magnificent 7 | **MAGX** +2x | $2.5M | QQQU | — |  |  |
| Mid cap 400 | **MIDU** +3x | $1.6M | MVV, UMDD, USMX | **SMDD** -3x | <$0.1M | MZZ |
| Tech Top 5 | **TTXU** +2x | $0.3M |  | — |  |  |
| Small cap 600 | **SAA** +2x | $0.1M |  | **SDD** -2x | <$0.1M |  |
| World | **WLDU** +2x | <$0.1M | WX | — |  |  |
| Total US market | **USX** +2x | <$0.1M |  | — |  |  |
| Micro cap | **XIWC** +2x | <$0.1M |  | — |  |  |
| US growth | **USGX** +2x | <$0.1M | MEGX | — |  |  |
| Ex-US | **XW** +2x | <$0.1M |  | — |  |  |

## Sector

| Underlying | Long | Avg $/day | Other longs | Short | Avg $/day | Other shorts |
|---|---|---|---|---|---|---|
| Semiconductors | **SOXL** +3x | $12.5B | USD, SMHU, XSEM | **SOXS** -3x | $5.3B | SSG, SMHD |
| XBI | **LABU** +3x | $79M | XBIX, TBXU | **LABD** -3x | $191M |  |
| Energy | **ERX** +2x | $53M | NRGU, DIG, WTIU, TEXU, XLEX | **ERY** -2x | $200M | DUG, NRGD, WTID |
| Gold miners | **GDXU** +3x | $190M | NUGT | **GDXD** -3x | $40M | DUST |
| Technology | **TECL** +3x | $173M | ROM, XLKX | **TECS** -3x | $38M | REW |
| DRAM | **RAM** +2x | $123M | DRAL, RAML | **RAMZ** -2x | $11M |  |
| Financials | **FAS** +3x | $62M | UYG, XLFX | **FAZ** -3x | $63M | SKF |
| FANG+ | **FNGU** +3x | $72M | BULZ, FNGG, FNGO | **FNGD** -3x | $19M | BERZ |
| Oil & gas E&P | **GUSH** +2x | $22M | OILU | **DRIP** -2x | $49M | OILD |
| Gold miners (junior) | **JNUG** +2x | $41M |  | **JDST** -2x | $24M |  |
| Homebuilders | **NAIL** +3x | $52M |  | — |  |  |
| KRE | **DPST** +3x | $25M | XKRE | **SKRE** -2x | $0.7M |  |
| Real estate | **DRN** +3x | $14M | URE, XHOA | **DRV** -3x | $2.8M | SRS |
| Defense | **DFEN** +3x | $15M |  | — |  |  |
| Health care | **CURE** +3x | $12M | RXL, XLVX | **RXD** -2x | $0.3M |  |
| Utilities | **UTSL** +3x | $6.6M | UPW, XLUX | **SDP** -2x | $0.2M |  |
| Cannabis (MSOS) | **MSOX** +2x | $4.6M |  | — |  |  |
| Internet (FDN) | **WEBL** +3x | $3.1M |  | **WEBS** -3x | $0.9M |  |
| Retail | **RETL** +3x | $4.0M |  | — |  |  |
| Consumer staples | **UGE** +2x | $2.3M | XLPX | **SZK** -2x | $0.2M |  |
| Quantum computing | **QPUX** +2x | $1.6M | XQTM | — |  |  |
| Consumer discretionary | **WANT** +3x | $1.4M | UCC, XLYX | **SCC** -2x | $0.1M |  |
| AI & Big Data index | **AIBU** +2x | $0.4M |  | **AIBD** -2x | $0.9M |  |
| Industrials | **DUSL** +3x | $1.1M | UXI, XLIX | **SIJ** -2x | $0.1M |  |
| Pharma | **PILL** +3x | $1.1M |  | — |  |  |
| IBB | **BIB** +2x | $1.0M |  | **BIS** -2x | $0.1M |  |
| Uranium | **URAA** +2x | $1.1M |  | — |  |  |
| ARKK / Innovation | **TARK** +2x | $0.7M |  | — |  |  |
| Transportation | **TPOR** +3x | $0.6M |  | — |  |  |
| Space | **SPCL** +2x | $0.4M |  | — |  |  |
| Airlines (JETS) | **JETU** +3x | $0.2M |  | **JETD** -3x | $0.3M |  |
| Big US Banks | **BNKU** +3x | $0.3M |  | **BNKD** -3x | <$0.1M |  |
| Materials | **UYM** +2x | $0.2M | XLBX | **SMN** -2x | <$0.1M |  |
| Cloud computing | **SKYU** +2x | $0.2M |  | — |  |  |
| Communication services | **LTL** +2x | $0.2M | XLCU | **XLCD** -3x | <$0.1M |  |
| Copper miners | **COPZ** +2x | $0.1M |  | — |  |  |
| Travel | **FLYU** +3x | <$0.1M |  | **FLYD** -3x | <$0.1M |  |
| AI index | — |  |  | **AIQD** -3x | <$0.1M |  |
| Auto industry | **CARU** +3x | <$0.1M |  | **CARD** -3x | <$0.1M |  |
| Infrastructure | **XPAV** +2x | <$0.1M |  | — |  |  |

## Single stock

| Underlying | Long | Avg $/day | Other longs | Short | Avg $/day | Other shorts |
|---|---|---|---|---|---|---|
| NVDA | **NVDL** +2x | $672M | NVDX, NVDU, NVDG, NVC | **NVD** -2x | $616M | NVDQ, NVDS |
| SNDK | **SNXX** +2x | $496M | SNDU, SNDG, SNDC | **SNDQ** -2x | $436M |  |
| MU | **MUU** +2x | $554M | MULL, MUG, MIC | **MUZ** -2x | $81M |  |
| TSLA | **TSLL** +2x | $445M | TSLG, TSLT, TSLR, TESC | **TSLQ** -2x | $119M | TSDD, TSLZ |
| AMD | **AMDL** +2x | $245M | AMUU, AMDG, AMDC | **DAMD** -2x | $88M |  |
| SPCX (SpaceX) | **SPCH** +2x | $204M | LOFF, SPCU, SPCF, SPAX, SPAL, SPCM | **SSPC** -2x | $123M | SNK, SPCQ, SPCG, LOFD |
| MSTR | **MSTU** +2x | $97M | MSTX, MSTP, MSTC | **MSTZ** -2x | $197M | SMST |
| CRWV | **CRWG** +2x | $85M | CWVX, CRWU, CRWX | **CORD** -2x | $121M |  |
| GOOGL | **GGLL** +2x | $192M | GOOX, GOU, GOOL, GOGL | — |  |  |
| NBIS | **NBIL** +2x | $108M | NBIG, NEBX, NBIC | **NBIZ** -2x | $58M |  |
| BE | **BEX** +2x | $84M | BEG, BEC | **BEZ** -2x | $46M |  |
| INTC | **INTW** +2x | $116M | LINT, INT | — |  |  |
| AAOI | **AAOX** +2x | $75M | AAOG | **AAOZ** -2x | $26M |  |
| MSFT | **MSFU** +2x | $101M | MSFL, MSFX, MSFC | — |  |  |
| LITE | **LITX** +2x | $76M | LITU, LITG, LITC | **LITZ** -2x | $24M |  |
| AXTI | **AXTX** +2x | $82M | AXTL, AXTU, AXTC | **AXTQ** -2x | $17M |  |
| IREN | **IRE** +2x | $58M | IREX, IREG, IREC | **IREZ** -2x | $29M |  |
| META | **METU** +2x | $84M | FBL, METG, FBX | **METQ** -2x | $2.9M |  |
| SK Hynix | **SKUU** +2x | $47M | SKHX, SKHL, SK, HYNX | **SKDD** -2x | $33M | SKHQ |
| BMNR | **BMNU** +2x | $56M | BMNG, BNMC | **BMNZ** -2x | $23M |  |
| AMZN | **AMZU** +2x | $66M | AMZZ, AMZG, AMAA | **AMZO** -2x | $1.5M |  |
| PLTR | **PTIR** +2x | $35M | PLTU, PLTG, PLTL | **PLTZ** -2x | $27M |  |
| MRVL | **MVLL** +2x | $62M | MRVU, MRVX | — |  |  |
| COIN | **CONL** +2x | $55M | CONX, COIG, COIX | **CONI** -2x | $4.7M |  |
| SMCI | **SMCX** +2x | $48M | SMCL, SMCC | **SMCZ** -2x | $10M |  |
| NOW | **NOWL** +2x | $38M | NOWX | — |  |  |
| ORCL | **ORCX** +2x | $34M | ORCU, ORAC | **ORCZ** -2x | $4.1M |  |
| TSM | **TSMX** +2x | $38M | TSMU, TSMG, TWSC | — |  |  |
| RKLB | **RKLX** +2x | $33M | RKX | — |  |  |
| AVGO | **AVL** +2x | $29M | AVGX, AVGG, AVGU, AVGC | — |  |  |
| ASTS | **ASTX** +2x | $28M | ASTY, ASTG, ASTT | — |  |  |
| COHR | **COHX** +2x | $25M | COHH, COHC | **COHQ** -2x | $2.6M |  |
| AAPL | **AAPU** +2x | $27M | AAPX, AAPB, AAPE, IOSX | — |  |  |
| DELL | **DLLL** +2x | $25M |  | — |  |  |
| CRDO | **CRDU** +2x | $25M | CRD | — |  |  |
| MRNA | **MRNX** +2x | $24M |  | — |  |  |
| IONQ | **IONX** +2x | $16M | IONL, IONC | **IONZ** -2x | $7.9M |  |
| APP | **APPX** +2x | $23M | APPC | — |  |  |
| WDC | **WDCX** +2x | $23M | WDCC | — |  |  |
| CRCL | **CRCG** +2x | $15M | CCUP, CIR | **CRCD** -2x | $7.4M |  |
| APLD | **APLX** +2x | $17M |  | **APLZ** -2x | $2.1M |  |
| UNH | **UNHG** +2x | $16M | UNHU, UN | — |  |  |
| NFLX | **NFXL** +2x | $16M | NFLU, NFX | — |  |  |
| RGTI | **RGTX** +2x | $9.0M | RGTU, RGTC | **RGTZ** -2x | $5.4M |  |
| CBRS | **CBRG** +2x | $10M | CBRX | **CBRZ** -2x | $4.0M |  |
| HOOD | **ROBN** +2x | $14M | HOOG, HODU, HOOX, HOOC | — |  |  |
| OKLO | **OKLL** +2x | $12M | OKLC | — |  |  |
| BABA | **BABX** +2x | $12M | BABU, BABC | — |  |  |
| ALAB | **LABX** +2x | $12M | ALA | — |  |  |
| SOFI | **SOFX** +2x | $12M | SOFA, SOFC | — |  |  |
| AEHR | **AEHG** +2x | $11M |  | — |  |  |
| CRWD | **CRWL** +2x | $9.2M | CRWC | — |  |  |
| LLY | **LLYX** +2x | $8.9M | ELIL | — |  |  |
| CIFR | **CIFU** +2x | $8.4M | CIFG, CIFC | — |  |  |
| ARM | **ARMG** +2x | $8.1M | ARMA | — |  |  |
| QBTS | **QBTX** +2x | $4.0M | QUA | **QBTZ** -2x | $4.1M |  |
| HIMS | **HIMZ** +2x | $8.1M | HIMC | — |  |  |
| RDDT | **RDTL** +2x | $7.9M | RDDC | — |  |  |
| ADBE | **ADBG** +2x | $7.3M | ADBU | — |  |  |
| GLW | **GLWG** +2x | $7.0M |  | — |  |  |
| ONDS | **ONDL** +2x | $6.9M | ONDG, ONDU, ONDC | — |  |  |
| STX | **STXL** +2x | $6.7M | STXU, STXX | — |  |  |
| CIEN | **CIEG** +2x | $6.2M | CIEX | — |  |  |
| VRT | **VRTL** +2x | $6.1M | VRC | — |  |  |
| QCOM | **QCML** +2x | $6.1M | QCMU | — |  |  |
| GME | **GMEU** +2x | $5.8M | GMEC | — |  |  |
| CRM | **CRMG** +2x | $5.7M |  | — |  |  |
| TEM | **TEMT** +2x | $5.4M | TEMC | — |  |  |
| WULF | **WULX** +2x | $5.3M |  | — |  |  |
| PANW | **PALU** +2x | $5.0M | PANG | — |  |  |
| LUNR | **LUNL** +2x | $4.8M |  | — |  |  |
| RIOT | **RIOX** +2x | $3.8M |  | — |  |  |
| ASST | **ASSX** +2x | $3.4M |  | — |  |  |
| GEV | **GEVX** +2x | $3.4M | GEVG, GEVC | — |  |  |
| NVTS | **NVTX** +2x | $2.9M | NVTC | — |  |  |
| LRCX | **LRCU** +2x | $2.8M | LRCC | — |  |  |
| CLS | **CSEX** +2x | $2.7M |  | — |  |  |
| BRKB | **BRKU** +2x | $2.7M | BRKL | — |  |  |
| IBM | **IBX** +2x | $2.5M |  | — |  |  |
| OKTA | **OKTG** +2x | $2.3M |  | — |  |  |
| VST | **VSTL** +2x | $2.3M |  | — |  |  |
| NVO | **NVOX** +2x | $2.3M | NVOC | — |  |  |
| PURR | **PUR** +2x | $2.2M | KATT | — |  |  |
| CLSK | **CLSX** +2x | $2.1M |  | — |  |  |
| MARA | **MRAL** +2x | $2.1M | MHX | — |  |  |
| BA | **BOEU** +2x | $2.0M | BOEG | — |  |  |
| AMAT | **AMAU** +2x | $2.0M | AMA, APMI | — |  |  |
| HPE | **HPEL** +2x | $1.9M |  | — |  |  |
| UBER | **UBRL** +2x | $1.8M |  | — |  |  |
| RIVN | **RVNL** +2x | $1.7M | RIVC | — |  |  |
| NET | **NETG** +2x | $1.5M |  | — |  |  |
| HUT | **HUTG** +2x | $1.5M |  | — |  |  |
| FUTU | **FUTG** +2x | $1.5M |  | — |  |  |
| ANET | **ANEL** +2x | $1.5M |  | — |  |  |
| FPS | **FPSX** +2x | $1.4M |  | — |  |  |
| KTOS | **KTUP** +2x | $1.4M |  | — |  |  |
| RDW | **RDWU** +2x | $1.4M |  | — |  |  |
| USAR | **USGG** +2x | $1.3M | USAX | — |  |  |
| EOSE | **EOSU** +2x | $1.3M | EO | — |  |  |
| SHOP | **SHPU** +2x | $1.3M |  | — |  |  |
| SMR | **SMU** +2x | $1.3M | SMUP, SMRX | — |  |  |
| RBLX | **RBLU** +2x | $1.3M |  | — |  |  |
| TTD | **TTDU** +2x | $1.2M |  | — |  |  |
| FLY | **FLYT** +2x | $1.2M |  | — |  |  |
| CSCO | **CSCL** +2x | $1.1M |  | — |  |  |
| CAT | **CATG** +2x | $1.1M |  | — |  |  |
| CEG | **CEGX** +2x | $1.1M |  | — |  |  |
| GLXY | **GLXU** +2x | $1.1M | GLX | — |  |  |
| COST | **COTG** +2x | $1.0M |  | — |  |  |
| LMT | **LMTL** +2x | $1.0M |  | — |  |  |
| POET | **POEL** +2x | $1.0M |  | — |  |  |
| ASML | **ASMG** +2x | $1.0M | ASMU, ASMZ | — |  |  |
| SNOW | **SNOU** +2x | $0.9M |  | — |  |  |
| XOM | **XOMX** +2x | $0.8M |  | — |  |  |
| TER | **TERG** +2x | $0.8M | TERC | — |  |  |
| UPST | **UPSX** +2x | $0.8M | UPSC | — |  |  |
| QNT | **QNTU** +2x | $0.8M |  | — |  |  |
| LULU | **LULG** +2x | $0.8M |  | — |  |  |
| KLAC | **KLAG** +2x | $0.8M |  | — |  |  |
| AMKR | **AMKL** +2x | $0.8M | AMKX | — |  |  |
| CRML | **CRMX** +2x | $0.8M |  | — |  |  |
| AVAV | **AVXX** +2x | $0.8M |  | — |  |  |
| TTMI | **TTMX** +2x | $0.8M |  | — |  |  |
| FIG | **FIGG** +2x | $0.7M |  | — |  |  |
| MP | **MPG** +2x | $0.7M |  | — |  |  |
| OUST | **OUSL** +2x | $0.7M |  | — |  |  |
| NOK | **LNOK** +2x | $0.7M |  | — |  |  |
| JOBY | **JOBX** +2x | $0.6M | JOBC | — |  |  |
| BIDU | **BIDG** +2x | $0.6M |  | — |  |  |
| TXN | **TXNU** +2x | $0.6M |  | — |  |  |
| STRL | **STLL** +2x | $0.6M |  | — |  |  |
| SOUN | **SOUX** +2x | $0.6M |  | — |  |  |
| OPEN | **OPEX** +2x | $0.6M |  | — |  |  |
| UUUU | **UUUG** +2x | $0.5M | UUUC | — |  |  |
| MXL | **MXLL** +2x | $0.5M |  | — |  |  |
| INFQ | **INFH** +2x | $0.5M |  | — |  |  |
| FIGR | **FGRU** +2x | $0.5M |  | — |  |  |
| KEEL | **KEEX** +2x | $0.5M |  | — |  |  |
| ISRG | **ISUL** +2x | $0.5M |  | — |  |  |
| PDD | **PDDL** +2x | $0.5M |  | — |  |  |
| LEU | **LEUX** +2x | $0.5M |  | — |  |  |
| BTDR | **BTDL** +2x | $0.5M |  | — |  |  |
| RCAT | **RCAX** +2x | $0.5M |  | — |  |  |
| ECHO | **ECHX** +2x | $0.5M |  | — |  |  |
| PENG | **PENU** +2x | $0.4M |  | — |  |  |
| SMTC | **SMTG** +2x | $0.4M |  | — |  |  |
| QUBT | **QUBX** +2x | $0.4M |  | — |  |  |
| FN | **FNG** +2x | $0.4M |  | — |  |  |
| CORZ | **COZX** +2x | $0.4M |  | — |  |  |
| UMAC | **UMAL** +2x | $0.4M |  | — |  |  |
| BBAI | **BAIG** +2x | $0.4M |  | — |  |  |
| PYPL | **PYPG** +2x | $0.4M | PYPU | — |  |  |
| ACHR | **ARCX** +2x | $0.4M | ACHX | — |  |  |
| OSCR | **OSCX** +2x | $0.3M |  | — |  |  |
| SITM | **SITX** +2x | $0.3M |  | — |  |  |
| TSEM | **TSEG** +2x | $0.3M |  | — |  |  |
| PLUG | **PLUL** +2x | $0.3M |  | — |  |  |
| SPOT | **SPOG** +2x | $0.3M |  | — |  |  |
| RTX | **RTXG** +2x | $0.3M |  | — |  |  |
| PL | **PLU** +2x | $0.3M |  | — |  |  |
| AAL | **AALG** +2x | $0.3M |  | — |  |  |
| DUOL | **DUOG** +2x | $0.3M |  | — |  |  |
| DJT | **DJTU** +2x | $0.3M |  | — |  |  |
| AKAM | **AKAL** +2x | $0.3M |  | — |  |  |
| MPWR | **MPWX** +2x | $0.3M | MPWC | — |  |  |
| GFS | **GFSG** +2x | $0.3M |  | — |  |  |
| P | **PUL** +2x | $0.3M |  | — |  |  |
| QS | **QSU** +2x | $0.3M |  | — |  |  |
| XNDU | **XNDX** +2x | $0.3M |  | — |  |  |
| ONTO | **ONTX** +2x | $0.3M |  | — |  |  |
| NIO | **NIOG** +2x | $0.2M |  | — |  |  |
| SNAP | **SNAG** +2x | $0.2M |  | — |  |  |
| U | **UNX** +2x | $0.2M |  | — |  |  |
| SIMO | **SIMX** +2x | $0.2M |  | — |  |  |
| ON | **ONG** +2x | $0.2M | ONX | — |  |  |
| GRAB | **GRAG** +2x | $0.2M |  | — |  |  |
| UCTT | **UCTX** +2x | $0.2M |  | — |  |  |
| XPEV | **XPEG** +2x | $0.2M |  | — |  |  |
| WYFI | **WYFL** +2x | $0.2M |  | — |  |  |
| FORM | **FOMG** +2x | $0.2M |  | — |  |  |
| DOCN | **OCNL** +2x | $0.1M |  | — |  |  |
| APH | **APHU** +2x | $0.1M | APHG | — |  |  |
| PATH | **PATX** +2x | $0.1M |  | — |  |  |
| VIAV | **VIAG** +2x | $0.1M |  | — |  |  |
| RMBS | **RMBX** +2x | $0.1M | RMBC | — |  |  |
| FIX | **FIXX** +2x | $0.1M |  | — |  |  |
| XYZ | **XYZG** +2x | $0.1M |  | — |  |  |
| MTSI | **MTSG** +2x | $0.1M |  | — |  |  |
| BULL | **BULG** +2x | <$0.1M |  | — |  |  |
| CDNS | **CDNG** +2x | <$0.1M |  | — |  |  |
| NXPI | **NXPG** +2x | <$0.1M |  | — |  |  |
| NTAP | **NTAL** +2x | <$0.1M |  | — |  |  |
| VELO | **VELL** +2x | <$0.1M |  | — |  |  |
| ADI | **ADIU** +2x | <$0.1M |  | — |  |  |
| ETN | **ETNG** +2x | <$0.1M |  | — |  |  |
| BB | **BBUL** +2x | <$0.1M |  | — |  |  |
| ENTG | **ENTL** +2x | <$0.1M |  | — |  |  |
| MCHP | **MCHG** +2x | <$0.1M | MCHU | — |  |  |
| STM | **STMX** +2x | <$0.1M |  | — |  |  |
| MRAM | **MRAX** +2x | <$0.1M |  | — |  |  |
| LWLG | **LWLX** +2x | <$0.1M |  | — |  |  |
| XOVR | **XOVL** +2x | <$0.1M |  | — |  |  |
| FLEX | **FLEL** +2x | <$0.1M |  | — |  |  |
| ACMR | **ACMM** +2x | <$0.1M |  | — |  |  |
| OSS | **OSSL** +2x | <$0.1M |  | — |  |  |
| MSI | **MSIX** +2x | <$0.1M |  | — |  |  |
| LASR | **LASC** +2x | <$0.1M |  | — |  |  |
| JBL | **JBLG** +2x | <$0.1M |  | — |  |  |
| UMC | **UMCX** +2x | <$0.1M | UMCU | — |  |  |
| MNST | **MNSX** +2x | <$0.1M |  | — |  |  |
| TDC | **TDCL** +2x | <$0.1M |  | — |  |  |
| CART | **CARX** +2x | <$0.1M |  | — |  |  |
| AGIX | **XAGI** +2x | <$0.1M |  | — |  |  |
| KEYS | **KEYG** +2x | <$0.1M | KEYX | — |  |  |
| TPL | **TPLX** +2x | <$0.1M |  | — |  |  |
| ACLS | **ACLZ** +2x | <$0.1M |  | — |  |  |
| TEL | **TELG** +2x | <$0.1M |  | — |  |  |
| CAMT | **CAMC** +2x | <$0.1M |  | — |  |  |
| CRUS | **CRUC** +2x | <$0.1M |  | — |  |  |
| LRN | **LRNX** +2x | <$0.1M |  | — |  |  |

## Commodity

| Underlying | Long | Avg $/day | Other longs | Short | Avg $/day | Other shorts |
|---|---|---|---|---|---|---|
| Silver | **AGQ** +2x | $165M | USLV | **ZSL** -2x | $86M |  |
| Crude oil | **UCO** +2x | $105M |  | **SCO** -2x | $114M |  |
| Natural gas | **BOIL** +2x | $112M |  | **KOLD** -2x | $70M |  |
| Gold | **UGL** +2x | $103M | GLLD, UGLD | **GLL** -2x | $74M | DULL, DZZ |
| Copper | **CPXR** +2x | $0.3M | UCOP | — |  |  |
| Wheat | **WXET** +2x | $0.3M |  | — |  |  |
| Corn | **CXRN** +2x | <$0.1M |  | — |  |  |
| Palladium | **UPAL** +2x | <$0.1M |  | — |  |  |
| Platinum | **UPLT** +2x | <$0.1M |  | — |  |  |
| Broad commodities | **XCOM** +2x | <$0.1M |  | — |  |  |

## Crypto

| Underlying | Long | Avg $/day | Other longs | Short | Avg $/day | Other shorts |
|---|---|---|---|---|---|---|
| BTC | **BITX** +2x | $91M | BITU, BTCL, BTCU | **BTCZ** -2x | $96M | SBIT |
| ETH | **ETHU** +2x | $86M | ETHT, ETU, EVMU | **ETHD** -2x | $19M |  |
| SOL | **SOLT** +2x | $15M | SLON | — |  |  |
| XRP | **XXRP** +2x | $6.7M | XRPT, UXRP | — |  |  |
| HYPE | **TXXH** +2x | $0.5M |  | — |  |  |
| SUI | **SUIL** +2x | $0.3M | TXXS | — |  |  |
| DOGE | **TXXD** +2x | $0.2M |  | — |  |  |
| XLM | **STLU** +2x | $0.1M |  | — |  |  |
| LINK | **CHNU** +2x | $0.1M |  | — |  |  |
| AVAX | **AVAZ** +2x | $0.1M |  | — |  |  |
| ADA | **CRDX** +2x | <$0.1M |  | — |  |  |

## Bonds

| Underlying | Long | Avg $/day | Other longs | Short | Avg $/day | Other shorts |
|---|---|---|---|---|---|---|
| 20+yr Treasury | **TMF** +3x | $128M | UBT | **TMV** -3x | $74M | TBT, TTT |
| High yield | **UJB** +2x | $1.8M | HYGU | — |  |  |
| 7-10yr Treasury | **UST** +2x | $0.7M | TYD | **TYO** -3x | $0.3M | PST |
| LQD | **LQDU** +3x | <$0.1M |  | **LQDD** -3x | <$0.1M |  |

## Country / region

| Underlying | Long | Avg $/day | Other longs | Short | Avg $/day | Other shorts |
|---|---|---|---|---|---|---|
| South Korea | **KORU** +3x | $446M | KRWX | — |  |  |
| China | **YINN** +3x | $47M | XPP, CCPX | **YANG** -3x | $26M | FXP |
| Brazil | **BRZU** +2x | $18M | BRZL, UBR, BRZX | **BZQ** -2x | $0.3M | BRZD |
| China internet | **CWEB** +2x | $15M | WEBX | — |  |  |
| EEM | **EDC** +3x | $4.5M | EET, EMXX | **EDZ** -3x | $4.2M | EEV |
| India | **INDL** +2x | $1.0M | TAJX | — |  |  |
| China A-shares | **CHAU** +2x | $0.9M |  | — |  |  |
| Europe (VGK) | **EURL** +3x | $0.5M | UPV, XEUR | **EPV** -2x | $0.3M |  |
| EFA | **EFO** +2x | $0.4M |  | **EFU** -2x | <$0.1M |  |
| Japan | **EZJ** +2x | $0.1M | JPNU | **EWV** -2x | $0.4M | JPND |
| Mexico | **MEXX** +3x | $0.2M |  | — |  |  |
| Taiwan | **TAWN** +3x | <$0.1M | XTAI | **TPEI** -3x | <$0.1M |  |

## Currency

| Underlying | Long | Avg $/day | Other longs | Short | Avg $/day | Other shorts |
|---|---|---|---|---|---|---|
| EUR/USD | **ULE** +2x | <$0.1M |  | **EUO** -2x | $0.9M |  |
| JPY/USD | **YCL** +2x | $0.4M |  | **YCS** -2x | $0.4M |  |

## Volatility

| Underlying | Long | Avg $/day | Other longs | Short | Avg $/day | Other shorts |
|---|---|---|---|---|---|---|
| VIX futures | **UVIX** +2x | $180M |  | — |  |  |

Under ~$5M a day, spreads get wide. Treat those as watch-only.

Source: Nasdaq ETF list, fund names verified against Yahoo, volume from daily bars. Not advice; leveraged and inverse funds reset daily and decay when held.

Built by [mphinance](https://mphinance.substack.com). Market data and tools: [TraderMatrix](https://tradermatrix.pro).
