"""OVERLAP CLI

Usage: 
    overlap_detect.py <codebook_name>
    overlap_detect.py --help
    overlap_detect.py --version
    
Options:
    <codebook_name>     Codebook to be processed
    -help               Show Usage and Options
    -version            Show Version
"""

import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
from shapely.geometry import MultiPoint, Point
import matplotlib.pyplot as plt
from collections import Counter
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
import re
from docopt import docopt



def process_shapefile(shapefile, iso, iso_details):
    
    #Read in shapefile
    m_df = gpd.read_file('C:' + shapefile + '.shp')

    #Subset shapefile to only the iso3 polygons
    if 'COUNTRY_ID' in m_df.columns:
        m_df = m_df[m_df.COUNTRY_ID == iso]            
    elif 'ISO' in m_df.columns:
        m_df = m_df[m_df.ISO == iso]
    elif 'ADM0_NAME' in m_df.columns:
        name1 = iso_details['location_name'].iloc[0]
        m_df = m_df[m_df.ADM0_NAME == name1]
    #else:
      
    return m_df

    
    

def plot_figure(final_polys, nid, iso, iso_details, final_points, poly_join,
                counter, codebook_name):
                  
    #Plot header
    fig, ax = plt.subplots(1, figsize = (8, 5)) 
    title = 'NID - {:<12} {} - {:<16} {} - {:<11} Stage {}'.format(
            nid, iso, iso_details['location_name'].iloc[0], 
            iso_details['start_year'].iloc[0], iso_details['end_year'].iloc[0], 
            iso_details['Stage'].iloc[0])
    
    #Plot Footer
    data_affected_total = str(len(final_points) + len(poly_join))
    polygon_total = str(len(counter))
    ax.annotate('{:<4} affected rows of data {:>13}  polygon(s) {:>22}'.format
                (data_affected_total, polygon_total, 'from  ' + codebook_name), 
                xy = (0.025, 0.04), xycoords ='figure fraction', 
                horizontalalignment ='left', verticalalignment ='top',
                fontsize = 12 )
            
    #Plot specs
    vmin = 0
    var = 'pcount'
    vmax = counter.pcount.max() 
    final_polys.plot(column = var, cmap = 'Reds', linewidth = 0.8, 
                edgecolor = '0.8', ax = ax, vmin = vmin, vmax = vmax)
    POINT = '#0000ff'  #Blue
    point_patchs = [PolygonPatch(point.buffer(.05), fc=POINT, ec='#555555')
                   for point in final_points]
    ax.add_collection(PatchCollection(point_patchs, match_original=True))
    ax.axis('off')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.title(title) 
    plt.tight_layout()
    
    #Color bar
    sm = plt.cm.ScalarMappable(cmap ='Reds', norm = plt.Normalize
                               (vmin = vmin, vmax = vmax))
    sm._A = [] 
    cbar = fig.colorbar(sm)
    
    #Output figure
    fig.savefig(iso + nid + 'pic.png',alpha = True, dpi=250, figsize = 2) 



def new_summary(labels, point_join, poly_join, counter, nid, iso, shapefile):

    #Get all codebook info
    problem_df = pd.DataFrame(columns = labels)
    geo_points = point_join.groupby('location_code')
    geo_polys = poly_join.groupby('location_code')
    
    #Calculates values to be outputted 
    for loc_code in counter.location_code:
        point_ids = geo_points.get_group(loc_code) 
        poly_ids = geo_polys.get_group(loc_code)   
        point_list = ', '.join(map(str, list(point_ids['pnt_geospatial_id'])))
        location_list = ', '.join(map(str, list(poly_ids['geospatial_id'])))                    
        cnt1 = len(point_ids)
        cnt2 = len(poly_ids)                    
        point_percent = format(cnt1 / (cnt1 + cnt2), '.2f')
        
        #Appends each polygon to output file        
        values = [(nid, iso, loc_code, shapefile, cnt1, cnt2, point_list,
                location_list, point_percent)]
        new_entry = pd.DataFrame.from_records(values, columns = labels)
        problem_df = pd.concat([problem_df, new_entry])
    
    #Outputs summary
    problem_df.to_csv(iso + nid + 'doc.csv', index = False)



def main(codebook_name):

    #Initializing column values  
    labels = ['nid', 'iso3', 'location_code', 'shapefile', 'point_count',
             'polygon_count', 'point_geospatial_ids', 'polygon_geospatial_ids',
             'percent_point'] 
    fields = ['nid', 'iso3', 'start_year', 'geospatial_id', 'end_year', 
              'point', 'lat', 'long', 'location_code', 'shapefile']
    
    #Get data
    df = pd.read_csv('C:/' + codebook_name +
                     '.csv', usecols = fields, encoding ='latin-1')
    cx = pd.read_csv("C:/crosswalk1.csv")
    
    #Isolate NIDs with both point and polygon values
    grouped_df = df.groupby('nid')['point'].nunique().reset_index()
    if len(grouped_df.point.unique()) < 2:
        print("\n\nCodebook countains no point overlap\n\n")
        return

    #Subset affected NIDs
    points_df = (grouped_df.groupby('point')).get_group(2)
    subset_df = df[df['nid'].isin(points_df.nid)]
    
    #Drop all subnational strings 
    subset_df.loc[:,'iso3'] = subset_df.iso3.apply(
                              lambda x: re.sub(r'_.*', '', x))

    #Loop through each nid
    frames = subset_df.groupby('nid')
    for f, frame in frames:

        nid = str(frame.nid.iloc[0])

        #Get points and polygons
        rows = frame.groupby(frame.point)
        points = rows.get_group(1)[['long', 'lat', 'geospatial_id']]
        polys = rows.get_group(0)[['location_code', 'geospatial_id']]
        poly_list = list(polys['location_code'].dropna().unique())   
        
        #Generate geodataframe for points
        crs = {'init': 'epsg:4326'}
        geometry = [Point(xy) for xy in zip(points.long, points.lat)]
        point_geo_df = (GeoDataFrame(points, crs = crs,
                        geometry = geometry)).rename(columns = 
                        {'geospatial_id':'pnt_geospatial_id'})
        
        #Loop through each iso3 for NID
        isos = frame.iso3.dropna().unique()
        for iso in isos:

            iso_details = frame.set_index('iso3').join(cx.set_index('iso3')
                          ).drop_duplicates()

            #loop through all shapefiles for NID
            shapefiles = frame.shapefile.dropna().unique()
            for shapefile in shapefiles:        

                if shapefile == 'buffered_points':
                    continue
                elif shapefile == 'geo1_pt2011_Y2017M06D29':
                    continue
                elif shapefile.endswith('.shp'):
                    shapefile = shapefile[:-4]
                #else:
                
                m_df = process_shapefile(shapefile, iso, iso_details)                

                #Detects overlap and generates joined dataframes
                map_df = m_df[m_df['GAUL_CODE'].isin(poly_list)] 
                point_join = (gpd.sjoin(point_geo_df, map_df,
                             op ='intersects')).rename(columns =
                             {'GAUL_CODE':'location_code'})
                counter = pd.DataFrame.from_dict(Counter 
                          (point_join.location_code), 
                          orient = 'index').reset_index().rename(columns = 
                          {'index':'location_code', 0:'pcount'})
             
                #Continues if no gaul codes affected
                if len(counter.index) == 0:
                    continue

                #Matches gaul codes to ids
                poly_join = pd.merge(counter, polys, how = 'inner',
                            on = ['location_code'])

                #Geometry to be plotted
                final_points = MultiPoint([tuple(x) for x in 
                               point_join[['long', 'lat']].values])
                final_polys = m_df.set_index('GAUL_CODE').join(counter
                              .set_index('location_code'))
                
                plot_figure(final_polys, nid, iso, iso_details, final_points,
                            poly_join, counter, codebook_name)
                
                new_summary(labels, point_join, poly_join, counter, nid, iso,
                            shapefile)
                
    
if __name__ == '__main__':
    arguments = docopt( __doc__, version = 'Overlap 1.0.1')
    if arguments['<codebook_name>']:
        main(arguments['<codebook_name>'])  
    else:
        print(arguments)
    
