from jinja2 import Template
import glob
import pandas as pd

# Read in all summary reports
path1 = r'file_path...'
allFiles = glob.glob(path1)

# Isolate the image file names for infograph retrieval
file_names = [x[:-4] for x in glob.glob('*.png')]
file_names.insert(0, ' ')

# Creates a list of all data in outputted csvs
affected = [pd.read_csv(f, index_col=None, header=0) for f in allFiles]

# Creates a lit of values for histogram per NID
chart_values = [list(p.percent_point) for p in affected]
chart_values.insert(0, ' ')

# Creates a list of all affected NIDs
problem_nids = [n.nid.iloc[0] for n in affected]
problem_nids.insert(0, ' ')

# Creates a list of summaries per NID
affected_nid_reports = [y.to_dict('records') for y in affected]
affected_nid_reports.insert(0, [])

# Read in template
with open('file_path...') as f:
    tmpl = Template(f.read())

# Render template
output_template = tmpl.render(nid_list=problem_nids, file_list=file_names,
                              chart_list=chart_values,
                              summary_list=affected_nid_reports)[3:]
# Generate static webpage
with open('file_path...', 'w') as f:
    f.write(output_template)
