from IPython.display import display, Image, Markdown, HTML
from ipywidgets import interact, interactive
import pandas as pd
import ipywidgets as wg
import matplotlib.pyplot as plt
import enum

class Choices(enum.Enum):
    poly = '# of Polygons Affected'
    clusters = '# of Clusters Affected'
    usage = '# of Teams Using NID'

def ndrop(NID):
    if NID == ' ':
        print (" ")
    else:
        #grab infograph
        gb = df.groupby(df['nid']).get_group(NID)[['pic']]
        col = gb['pic'].iloc[0]
        images = []
        images.append('final_prob/' + col + '.png')
        for image in images:
            display(Image(image))
        
        #grab summary 
        gb = df.groupby(df['nid']).get_group(NID)[['problem_info']]
        col = gb['problem_info'].iloc[0]
        display(HTML('<a href=final_prob/' + col + '.csv target=_blank>Summary Report </a>'))
        
def sdrop(Stage):
    if Stage == ' ':
        print (" ")
    else:
        col(df.groupby(df['stage']).get_group(Stage)[['nid']])
        
def cdrop(Iso3):
    if Iso3 == ' ':
        print (" ")
    else:
        col(df.groupby(df['iso3']).get_group(iso3)[['nid']])

def bdrop(Codebook):
    if Codebook == ' ':
        print (" ")
    else:
        col(df.groupby(df['codebook']).get_group(Codebook)[['nid']])
        
def hdrop(Choose):
    if Choose == ' ':
        print(" ")
    else:
        if Choose == Choices.poly.value:
            x = 'total_polygons'
        elif Choose == Choices.clusters.value:
            x = 'row_count'
        elif Choose == Choices.usage.value:
            x = 'nid_usage'
        col(df.nlargest(5, x)[['nid']])


def col(gb):
    col1 = list(gb.nid.unique())
    bk(col1)
    interact(ndrop, NID = col1)

def bk(list1):
    return(list1.insert(0, ' '))


df = pd.read_csv('final_prob/master.csv')

print('\n')
display(Markdown('<strong>{}</strong>'.format("POINT POLYGON OVERLAP REPORT")))
print('\nCodebooks from:  J:\WORK\\11_geospatial\\05_survey shapefile library\codebooks\n\n\n')
display(Markdown('<strong>{}</strong>'.format("Search By")))

#Creating lists for drop down values
nid_list = list(df['nid'])
stage_list = list(set(df['stage']))
country_list = list(set(df['iso3']))
code_list = list(set(df['codebook']))
heuristic_list = ['# of Polygons Affected',
                  '# of Clusters Affected',
                  '# of Teams Using NID']

#Inserting blank option
bk(nid_list)
bk(stage_list)
bk(country_list)
bk(code_list)
bk(heuristic_list)

#Creating inner dropdowns
nid_sel = interactive(ndrop, NID = nid_list)
stage_sel = interactive(sdrop, Stage = stage_list)
country_sel = interactive(cdrop, Iso3 = country_list)
code_sel = interactive(bdrop, Codebook = code_list)
hueristic_select = interactive (hdrop, Choose = heuristic_list)

#Creating outer tabs
acc = wg.Accordion(children=[nid_sel, stage_sel, country_sel, code_sel, hueristic_select])
acc.set_title(0, 'NID')
acc.set_title(1, 'Stage')
acc.set_title(2, 'Iso3')
acc.set_title(3, 'Codebook')
acc.set_title(4, 'Top 5')

acc 
