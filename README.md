# Momentum, Breadth, and Correlation in Tactical Asset Allocation: A Rule-by-Rule Attribution

Replication materials for the paper *"Momentum, Breadth, and Correlation in
Tactical Asset Allocation: A Rule-by-Rule Attribution"* (Garcia Martin, Mases
Campos, Prior Sanz; IQS School of Engineering, Universitat Ramon Llull).

The paper designs and evaluates a fully automated, rule-based tactical asset
allocation strategy over a universe of 15 ETFs, and provides a transparent,
rule-by-rule attribution of its out-of-sample edge under a strict nested
train / validation / test protocol.

## Repository layout

```
main.tex              Manuscript (Elsevier elsarticle class)
sections/             Manuscript sections (01 introduction … 07 appendix)
paper.bib             Bibliography
COVER_LETTER.tex      Submission cover letter
figures/              Figures used in the manuscript
code/                 Reproduction pipeline
data/prices/          Input price series and risk-free rate
```

## Reproduction pipeline

The pipeline runs from the provided dataset (`data/prices/dataset_extended.csv`)
under the nested split defined in `code/config.py`
(TRAIN 2004–2015, VAL 2016–2020, TEST 2021–2025):

```
cd code
python 01_derive_train.py     # derive parameters on the training window
python 02_validate_val.py     # confirm out-of-sample on validation
python 02c_marc_confirm.py    # rule-by-rule confirmation
python 04_test.py             # evaluate the frozen strategy on the locked test block
```

`code/lib.py` is the shared backtest engine and `code/config.py` is the single
source of the split and parameters. The risk-free rate is fetched from FRED
(series TB3MS); set a free API key via the `FRED_API_KEY` environment variable
(if unset, the rate falls back to zero).

## Building the manuscript

```
pdflatex main
bibtex   main
pdflatex main
pdflatex main
```

For the final typeset version, change the document class option in `main.tex`
from `[review]` to `[final,5p]`.
