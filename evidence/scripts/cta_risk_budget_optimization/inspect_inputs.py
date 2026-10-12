# Run inside the pinned judge image: dumps policy text on overseas/currency and data schema/FX levels.
import zipfile, re, pandas as pd
def docx_text(p):
    x = zipfile.ZipFile(p).read('word/document.xml').decode()
    paras = re.findall(r'<w:p[ >].*?</w:p>', x, flags=re.S)
    return [re.sub(r'<[^>]+>', '', q) for q in paras]
for doc in ['risk_policy_doc.docx', 'strategy_research_notes.docx']:
    print('=====', doc)
    for t in docx_text('/home/workspace/input/' + doc):
        if re.search(r'overseas|currency|CNY|RMB|USD|FX|exchange|notional|40%|exposure', t, re.I):
            print('  |', t)
I='/home/workspace/input/'
for f in ['futures_price_data.xlsx','futures_contract_specs.xlsx','macro_factors_data.xlsx']:
    x = pd.ExcelFile(I+f); print('=====', f, x.sheet_names)
    for s in x.sheet_names:
        d = pd.read_excel(I+f, sheet_name=s); print('--', s, d.shape, list(d.columns)[:20])
specs = pd.read_excel(I+'futures_contract_specs.xlsx', sheet_name=0)
print(specs.to_string())
fx = pd.read_excel(I+'macro_factors_data.xlsx', sheet_name='fx_rates_daily')
print(fx.describe().to_string())
ov = pd.read_excel(I+'futures_price_data.xlsx', sheet_name='overseas_futures')
print(ov.groupby('ticker')['close'].describe().to_string())
if 'currency' in ov.columns: print(ov.groupby('ticker')['currency'].unique())
