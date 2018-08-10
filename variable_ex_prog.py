import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPoint
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
import re
import sys

# =============================================================================
import warnings
warnings.filterwarnings("ignore")
# =============================================================================

#Populate for output file
codebook_name = 'UNICEF_MICS'
fields =[ 'nid', 'iso3', 'start_year', 'geospatial_id',  'end_year', 'point',\
         'lat', 'long', 'location_code', 'shapefile']
df = pd.read_csv('CB_and_SF/' + codebook_name + '.csv', usecols = fields,\
                 encoding='latin-1', low_memory = False)

#Grab related ISO info
cx = pd.read_csv("CB_and_SF/crosswalk1.csv")
cx2 = pd.read_csv('nid_usage.csv') #for heuristic

#isolates NIDs with both point and polygon data
affected = []
wb2 = df.groupby('nid')['point'].nunique().reset_index()
if len(wb2.point.unique()) < 2:
    print("\n\nCodebook countains no point overlap\n\n")
    #sys.exit()

#Isolate affected NIDs, Drop all subnational strings
wb = list((wb2.groupby('point').get_group(2)[['nid']]).nid)
for k in wb:
    temp_df = df[df.nid == k]
    temp_df.iso3 = temp_df.iso3.apply(lambda x: re.sub(r'_.*', '', x))
    affected.append(temp_df)

#ouput columns for each NID
labels = ['nid', 'iso3', 'location_code', 'shapefile', 'point_count',\
           'polygon_count', 'point_geospatial_ids', 'polygon_geospatial_ids',\
           'percent_point'] 

#list33 = affected[1:]
#temp = []
#temp.append(affected[1])

for y, df1 in enumerate(affected):

        nid1 = str(df1.nid.iloc[0])
        
        #loop through each iso3 for NID
        nid_arr = df1.iso3.dropna().unique()
    
        for iso in nid_arr:

            #try catch if something other than NaN is present 

            #Look at home
            #testing_rows = rows.get_group(0)[['long', 'lat']]
            #np.isnan(np.nan):
                
            rows = df1.groupby(df1.point)
            point_seq = rows.get_group(1)[['long', 'lat']] #, 'location_code']]
            point_geo_spatial = list((rows.get_group(1)[['geospatial_id']])['geospatial_id'])
            points = MultiPoint([tuple(x) for x in point_seq.values])
            poly_rows = rows.get_group(0)[['location_code', 'geospatial_id']]

            #Dropping NaN values 
            poly_list = list(poly_rows.location_code.dropna())
 
            #May do something results
            #geolocated_polygons = poly_rows.location_code.drop_duplicates()
            
            combined_info = df1.set_index('iso3').join(cx.set_index('iso3'))
            #new = geolocated_polygons.location_code.dropna().unique()

            #loop through all shapefiles for NID
            fp = df1.shapefile.dropna().unique()
            for k in fp:        
                
                if k == 'buffered_points':
                    continue
                
                #special case where file doesn't exist in shapefile directory 
                if k == 'geo1_pt2011_Y2017M06D29':
                    continue
                
                #Try-catch when .shp is also in the name
                #case where shapefile value was populated with extension
                if k.endswith('.shp'):
                    k = k[:-4]
                
                
                m_df = gpd.read_file('CB_and_SF/' + k + '.shp')
               # m_df = gpd.read_file('J:\WORK\\11_geospatial\\05_survey shapefile library\Shapefile directory\\' + k + '.shp')
                
                #results = list(geolocated_polygons)
                #results = list(map(int, cleanedresults))
    
                #Still need to find a way to subset by location_code
                #m_df = m_df[m_df['GAUL_CODE'].isin(results)]
    
           
                if 'COUNTRY_ID' in m_df.columns:
                    m_df = m_df[m_df.COUNTRY_ID == iso]            
                if 'ISO' in m_df.columns:
                    test = m_df.groupby(m_df.ISO)
                    m_df = test.get_group(iso)
                if 'ADM0_NAME' in m_df.columns:
                    name1 = combined_info['location_name'].iloc[0]
                    m_df = m_df[m_df.ADM0_NAME == name1]
    
                data_tuples = []
                points_affected = []
                for p in range(len(points)):
                    for row in m_df.iterrows():    
                        flag = row[1].geometry.intersects(points[p])
                        flag2 = row[1].GAUL_CODE in poly_list
                        if flag and flag2:
                            data_tuples.append((row[1].GAUL_CODE, point_geo_spatial[p]))
                            points_affected.append(points[p])
                            break 

                dff = pd.DataFrame(data_tuples, columns=['polygon','point_geospatial'])
                counter = Counter([seq[0] for seq in data_tuples])
            
                #If all gaul_codes didn't have overlap
                if sum(counter.values()) == 0:
                    print('NID ' + nid1 + '   Shapefile ' + k + '    is good')
                    continue
                    
                #Might just keep as counter dictionary
                final_polys = pd.DataFrame(list(counter.items()), \
                                           columns=['location_code', 'count'])
                final_points = MultiPoint(points_affected) 
                
                poly_row_count = len(final_polys['location_code'])
            
                tm2 = (combined_info[['nid', 'location_name', 'Stage', 'start_year', 'end_year']]).drop_duplicates()
                tes = pd.Series(codebook_name)
                tm2['Codebook'] = tes[0]


                #Merge CB and SF files on location_code
                merged = m_df.set_index('GAUL_CODE').join \
                     (final_polys.set_index('location_code'))
        
                #Merge related info for NIDs
            
                #plot time
                var = 'count'
                vmin = 0
                real_vmax = final_polys['count'].max() 
                fig, ax = plt.subplots(1, figsize= (8, 5)) 
                ax.axis('off')
                merged.plot(column = var, cmap= 'Reds', linewidth=0.8,  edgecolor= '0.8', \
                            ax=ax, vmin = vmin, vmax = real_vmax)
                POINT = '#0000ff'  #Blue
                point_patchs = [PolygonPatch(point.buffer(.1), fc=POINT,  ec='#555555') \
                                             for point in final_points]
                ax.add_collection(PatchCollection(point_patchs, match_original=True))
                ax.set_xticks([])
                ax.set_yticks([])
                string1 = str('NID - ' +  nid1 + '        '+ iso + ' - ' + tm2['location_name'][0] \
                          + '        ' + str(tm2['start_year'][0]) + ' - ' \
                          + str(tm2['end_year'][0]) +  '         Stage ' + tm2['Stage'][0])
                plt.title(string1) 
                plt.tight_layout()


                cpc = ((pd.value_counts(final_polys['count'].values, sort=False)).reset_index())
                cpc2 = cpc[[0, 'index']].rename(index=str, columns={0: "# polygons", "index": "Point(s) "})
                          #string1 = "%.2f" % ((len(final_polys) /len(geolocated_polygons)) * 100)
                          #string2 = "%.2f" % ((len(point_list_affected) /len(point_seq)) * 100)
                points_count = len(final_points)
                data_effected_total = points_count + poly_row_count
                data_affected_count = str(data_effected_total)

                string2 = str(len(final_polys))

                ax.annotate('{0: <4}'.format(data_affected_count) + 'affected rows of data' + '{0: >11}'.format(string2) \
                            + '  polygon(s)           from ' + codebook_name , xy=(0.025, 0.04),\
                    xycoords='figure fraction', horizontalalignment='left', \
                    verticalalignment='top', fontsize=12 )
                #Color bar
                sm = plt.cm.ScalarMappable(cmap='Reds', \
                                           norm =plt.Normalize(vmin=vmin, vmax=real_vmax))
                sm._A = [] 
                cbar = fig.colorbar(sm)


                problem_df = pd.DataFrame(columns=labels)
                
                #creating problem NID summary
                first = list(dff['point_geospatial'])
                poly_rows['point_geospatial_id'] = pd.Series(first)
                toby_point = dff.groupby(dff.polygon)
                jim_harper = poly_rows.groupby(poly_rows.location_code)
                print('NID   ISO3  location_code   shapefile  point_count  polygon_count')
                for index, row in final_polys.iterrows(): #itertuples()?
                    #percent = points_count/data_effected_total
                    pam = jim_harper.get_group(row['location_code'])
                    toby = toby_point.get_group(row['location_code'])
                    pam2 = pam.location_code.count()
                    #pam2 =str( len(pam2['location_code']))
                    s1 = str(int(row['location_code']))
                    str0 = str(pam['location_code'])


                    str2 = ', '.join(map(str, list(pam['geospatial_id'])))
                
                    
                    str3 = str(int(row['count']))
                    str4 = list(toby['point_geospatial'])
                    #str5 = ', '.join(str4)
                    
                    str5 = ', '.join(map(str, str4))
                
                    total_data_affected = int(row['count']) + pam2
                    point_percent = int(row['count']) / total_data_affected
                    answer = format(point_percent, '.2f')
                
              
                    #Append each affected polygon information to dataframe           
                    poly_temp = [(nid1, iso, s1, k, str3, pam2, str5, str2, answer)]
                    new_entry = pd.DataFrame.from_records(poly_temp, columns=labels)
                    problem_df = pd.concat([problem_df, new_entry])

                #Change name to account for different iso3, need to test still
                #problem_df.to_csv('new_problem/' + nid1 + 'doc.csv', index = False)
                #fig.savefig('new_problem/' + nid1 + 'pic.png',alpha = True,  dpi=250, figsize = 2) 
        