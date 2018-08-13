
from IPython.display import display, Image, Markdown, HTML
from ipywidgets import interact, interactive
import pandas as pd
import ipywidgets as wg
import matplotlib.pyplot as plt


def ndrop(NID):
    if NID == ' ':
        print (" ")
    else:
        #grab infograph
        gb = (df.groupby(df['nid'])).get_group(NID)[['pic']]
        col = gb['pic'].iloc[0]
        images = []
        images.append('final_prob/' + col + '.png')
        for image in images:
            display(Image(image))
        
        #grab summary 
        gb = (df.groupby(df['nid'])).get_group(NID)[['problem_info']]
        col = gb['problem_info'].iloc[0]
        display(HTML('<a href=final_prob/' + col + '.csv target=_blank>Summary'
                     'Report </a>'))
        
def sdrop(Stage):
    if Stage == ' ':
        print (" ")
    else:
        col((df.groupby(df['Stage']).get_group(Stage)[['nid']]))
        
def cdrop(Iso3):
    if Iso3 == ' ':
        print (" ")
    else:
        col((df.groupby(df['iso3']).get_group(Iso3)[['nid']]))

def bdrop(Codebook):
    if Codebook == ' ':
        print (" ")
    else:
        col((df.groupby(df['Codebook'])).get_group(Codebook)[['nid']])

def col(gb):
    col1 = list(gb.nid.unique())
    bk(col1)
    interact(ndrop, NID = col1)

def bk(list1):
    return(list1.insert(0, ' '))


df = pd.read_csv('master1.csv')

print('\n')
display(Markdown('<strong>{}</strong>'.format("POINT POLYGON OVERLAP REPORT")))
print('\nCodebooks from:  C:codebooks\n\n\n')
display(Markdown('<strong>{}</strong>'.format("Search By")))

#Creating lists for drop down values
nid_list = list(df['nid'])
stage_list = list(set(df['Stage']))
country_list = list(set(df['iso3']))
code_list = list(set(df['Codebook']))

#Inserting blank option
bk(nid_list)
bk(stage_list)
bk(country_list)
bk(code_list)

#Creating inner dropdowns
nid_sel = interactive(ndrop, NID = nid_list)
stage_sel = interactive(sdrop, Stage = stage_list)
country_sel = interactive(cdrop, Iso3 = country_list)
code_sel = interactive(bdrop, Codebook = code_list)

#Creating outer tabs
acc = wg.Accordion(children=[nid_sel, stage_sel, country_sel, code_sel])
acc.set_title(0, 'NID')
acc.set_title(1, 'Stage')
acc.set_title(2, 'Iso3')
acc.set_title(3, 'Codebook')
#Add hueristic option here
acc 
