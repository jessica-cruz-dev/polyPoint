# -*- coding: utf-8 -*-
"""OVERLAP CLI

Usage:
    overlap_detect.py <codebook_name>
    overlap_detect.py <codebook_name> [--input_dir=<file_path>]
    overlap_detect.py [--runall] (--output_dir=<file_path>)
    overlap_detect.py (-h | --help)
    overlap_detect.py (-v | --version)

Options:
    <codebook_name>              Ex. ADB_DHS
    --input_dir=<file_path>      Specify a different input directory
    --output_dir=<file_path>     Specify a different output directory
    --runall                     Process all codebooks in J: drive
    -h --help                    Show Usage and Options
    -v --version                 Show Version
"""

import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
from shapely.geometry import MultiPoint, Point
import matplotlib.pyplot as plt
from collections import Counter
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
from docopt import docopt
from pathlib import Path
from PIL import Image
import glob
import re
import io
import os


def main(args):

    print(os.getcwd())
    
    # Assigning output data directory based on user input
    if args['--output_dir'] is None:  # Current working directory
        output_dir = os.getcwd() + '//'
    else:
        output_dir = args['--output_dir'] + '//'

    # Assigning input data directory based on user input
    if args['--input_dir'] is None:
        codebook_file_path = 'J:/WORK//11_geospatial//05_survey shape'\
            'file library/codebooks//'
        shapefile_file_path = 'J:/WORK//11_geospatial//05_survey shape'\
            'file library/Shapefile directory//'
    else:
        codebook_file_path = args['--input_dir'] + '//'
        shapefile_file_path = args['--input_dir'] + '//'

    # Initializing column values for input and output dataframe
    labels = ['nid', 'iso3', 'location_code', 'shapefile', 'point_count',
              'polygon_count', 'point_geospatial_ids',
              'polygon_geospatial_ids', 'percent_point']
    fields = ['nid', 'iso3', 'start_year', 'geospatial_id', 'end_year',
              'point', 'lat', 'long', 'location_code', 'shapefile']

    # Set of shapefiles won't be processed if encountered in codebook
    # shapefile column
    problem_shapefiles = ('buffered_points', 'geo1_pt2011_Y2017M06D29',
                          'IDN_DHS_1994')

    # Coordinate reference system used for projections
    crs = {'init': 'epsg:4326'}

    # Initilizing encoding
    encoding = 'latin-1'

    # Directory of entered codebook
    file_path = codebook_file_path + args['<codebook_name>'] + '.csv'

    # Validating codebook file path
    file = Path(file_path)
    try:
        file.resolve()
    except FileNotFoundError:
        print('\n\nCodebook: ' + args['<codebook_name>'] + '   not present'
              'in\n\n' + codebook_file_path + '\n\n')
        return
    else:
        df = pd.read_csv(file, usecols=fields, encoding=encoding,
                         low_memory=False)

    # Reading in metadata for each country - full name, iso3, stage
    # Needed for display output
    cx = pd.read_csv('crosswalk1.csv')

    # Isolate NIDs with both point and polygon values
    grouped_df = df.groupby('nid')['point'].nunique().reset_index()
    if len(grouped_df.point.unique()) < 2:
        print('\n\nCodebook: ' + args['<codebook_name>'] + '   countains no '
              'point/polygon overlap\n\n')
        return

    # Subset nids with both point and polygon data to be
    # tested for overlap
    points_df = (grouped_df.groupby('point')).get_group(2)
    subset_df = df[df['nid'].isin(points_df.nid)]

    # Drop all subnational strings included in iso3 column
    subset_df['iso3'].apply(lambda x: re.sub(r'_.*', '', x))

    print('\n\n*******  Processing codebook: ' + args['<codebook_name>'] +
          '  *******\n')

    # Loop through each nid to detect overlap
    frames = subset_df.groupby('nid')
    for f, frame in frames:

        # Isolate nid for later output of files and titles
        nid = str(frame.nid.iloc[0])

        # Get points and polygons for individual processing
        rows = frame.groupby(frame.point)
        points = rows.get_group(1)[['long', 'lat', 'geospatial_id']].dropna()

        polys = rows.get_group(0)[['location_code', 'geospatial_id']].dropna()

        # location_codes being set to numerals for GAUL_CODE comparison
        polys['location_code'] = pd.to_numeric(polys['location_code'])
        poly_list = list(polys['location_code'].dropna().unique())

        # Transform point values to type geometry for finding
        # intersection with polygon geometry from shapefiles
        geometry = [Point(xy) for xy in zip(points.long, points.lat)]
        point_geo_df = (GeoDataFrame(points, crs=crs, # noqa
                        geometry=geometry)).rename(
                        columns={'geospatial_id': 'pnt_geospatial_id'})

        # Loop through each iso3 for NID
        isos = frame.iso3.dropna().unique()
        for iso in isos:

            # Merge the current nid with metadata for current iso3
            # necessary for title displayed in infograph
            iso_df = frame.set_index('iso3').join(
                    cx.set_index('iso3')).drop_duplicates()
            iso3_metadata = iso_df.iloc[0].to_dict()

            # loop through all shapefiles for NID
            shapefiles = frame.shapefile.dropna().unique()
            for shapefile in shapefiles:

                # Cutting out of shapefile loop for all identified
                # discrepencies in codebook column
                if shapefile in problem_shapefiles:
                    continue
                elif shapefile.endswith('.shp'):
                    shapefile = shapefile[: -4]

                # Reads in shapefile, determines if world admin shapefile
                # and subsets size if applicable
                m_df = process_shapefile(shapefile, iso, iso3_metadata,
                                         shapefile_file_path)

                # Validating shapefile dataframe
                if type(m_df) is bool:
                    return
                elif len(m_df) == 0:
                    continue

                # Assuring no String values
                m_df['GAUL_CODE'] = pd.to_numeric(m_df.GAUL_CODE)

                # Subsets shapefile dataframe to only the location codes
                # referenced in codebooks
                map_df = m_df[m_df['GAUL_CODE'].isin(poly_list)]

                # Joins point and polygon geometry and returns
                # point metadata for each overlapping point
                point_join = gpd.sjoin(point_geo_df, map_df, # noqa
                                       op='intersects').rename(
                                       columns={'GAUL_CODE': 'location_code'})

                # Generates a dataframe that holds location code
                # and count of how many times a point overlaps that polygon
                # necessary for choropleth highlighting and output summary
                counter = pd.DataFrame.from_dict(Counter # noqa
                                                 (point_join.location_code),
                                                 orient='index').reset_index(
                                                 ).rename(columns={
                                                 'index': 'location_code',
                                                 0: 'pcount'})

                # Continues if there aren't any gaul codes affected when
                # an empty counter is returned
                if len(counter) == 0:
                    continue
                print('Overlap detected:  {:<8}| {:<5}| {}'.format(nid, iso,
                      shapefile))

                # Joins all polygons and generated overlapped polygons
                # and returns metadata for each of those polygons
                poly_join = pd.merge(counter, polys, how='inner',
                                     on=['location_code'])

                # Prepares only the geometry detected to have overlap to be
                # plotted
                final_points = MultiPoint([tuple(x) for x in
                                           point_join[['long', 'lat']].values])
                final_polys = m_df.set_index('GAUL_CODE').join(counter # noqa
                                            .set_index('location_code'))

                # Assures no no null count values to be outputted in infograph
                final_polys['pcount'] = final_polys.pcount.fillna(0)

                # Plots map and metadata for each nid and outputs
                # image file
                plot_figure(final_polys, nid, iso, iso3_metadata, final_points,
                            poly_join, counter, args['<codebook_name>'],
                            shapefile, output_dir)

                # Calculates all final stats to be outputted in summary
                overlap_summary(labels, point_join, poly_join, counter, nid,
                                iso, shapefile, output_dir)

    if args['--runall'] is False:
        print('\n\nInfograph(s) and Summary Report(s) outputted to  ' +
              output_dir)


def process_shapefile(shapefile, iso, iso3_metadata, shapefile_file_path):

    # Read in shapefile to be processed
    file_path = shapefile_file_path + shapefile + '.shp'

    # Validating shapefile file path
    file = Path(file_path)
    try:
        file.resolve()
    except FileNotFoundError:
        print("\nShapefile: " + shapefile + "   not present in\n\n" +
              shapefile_file_path + '\n\n')
        return False
    else:
        m_df = gpd.read_file(file_path)

    # Subset shapefile to only the iso3 polygons if determined to be
    # a world admin shapefile
    if 'COUNTRY_ID' in m_df.columns:
        m_df = m_df[m_df.COUNTRY_ID == iso]
    elif 'ISO' in m_df.columns:
        m_df = m_df[m_df.ISO == iso]
    elif 'ADM0_NAME' in m_df.columns:
        name1 = iso3_metadata['location_name']
        m_df = m_df[m_df.ADM0_NAME == name1]

    m_df = m_df.dropna(subset=['GAUL_CODE'])

    return m_df


def plot_figure(final_polys, nid, iso, iso3_metadata, final_points, poly_join,
                counter, codebook_name, shapefile, output_dir):

    # Plot header that includes all metadata matched to this nid and iso3
    fig, ax = plt.subplots(1, figsize=(8, 5))
    title = 'NID - {:<12} {} - {:<16} {} - {:<11} Stage {}'.format(
            nid, iso, iso3_metadata['location_name'],
            iso3_metadata['start_year'], iso3_metadata['end_year'],
            iso3_metadata['Stage'])

    # Plot Footer that includes related stats and entered codebook
    polygon_total = str(len(counter))

    ax.annotate('{:^22} {:^40} from {}'.format(polygon_total + ' polygon(s)',
                shapefile + '.shp', codebook_name), xy=(0.025, 0.04),
                xycoords='figure fraction', horizontalalignment='left',
                verticalalignment='top', fontsize=12)

    # Plot points and polygons, prepares layout details of figure
    vmin = 0
    var = 'pcount'
    vmax = counter.pcount.max()
    final_polys.plot(column=var, cmap='Reds', linewidth=0.8,
                     edgecolor='0.8', ax=ax, vmin=vmin, vmax=vmax)
    POINT = '#0000ff'  # Blue
    point_patchs = [PolygonPatch(point.buffer(.03), fc=POINT) for point in
                    final_points]
    ax.add_collection(PatchCollection(point_patchs, match_original=True))
    ax.axis('off')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.title(title)
    plt.tight_layout()

    # Generates color bar for choropleth key
    sm = plt.cm.ScalarMappable(cmap='Reds', norm=plt.Normalize
                               (vmin=vmin, vmax=vmax))
    sm._A = []
    fig.colorbar(sm)

    # Generating in-memory formatted image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    im = Image.open(buf)

    # output figure as png infograph
    im.save(output_dir + iso + nid + shapefile + 'pic.png')

    # Closing all figure actions
    buf.close()
    plt.close(fig)


def overlap_summary(labels, point_join, poly_join, counter, nid, iso,
                    shapefile, output_dir):

    # Prepares values to be called
    problem_df = pd.DataFrame(columns=labels)
    geo_points = point_join.groupby('location_code')
    geo_polys = poly_join.groupby('location_code')

    # Calculates all stats for output file
    for loc_code in counter.location_code:
        point_ids = geo_points.get_group(loc_code)
        poly_ids = geo_polys.get_group(loc_code)
        point_list = ', '.join(map(str, point_ids['pnt_geospatial_id']))
        location_list = ', '.join(map(str, poly_ids['geospatial_id']))
        cnt1 = len(point_ids)
        cnt2 = len(poly_ids)
        point_percent = format(cnt1 / (cnt1 + cnt2), '.2f')

        # Appends each polygon data to output file
        values = [(nid, iso, loc_code, shapefile, cnt1, cnt2, point_list,
                   location_list, point_percent)]
        new_entry = pd.DataFrame.from_records(values, columns=labels)
        problem_df = pd.concat([problem_df, new_entry])

    # Outputs summary as csv
    problem_df.to_csv(output_dir + iso + nid + shapefile + 'doc.csv',
                      index=False)


if __name__ == '__main__':
    # Receive command line arguments
    arguments = docopt(__doc__, version='Overlap 1.0.1')

    if arguments['--runall']:
        # Grab all codebook names from J Drive
        os.chdir('J:/WORK//11_geospatial//05_survey shapefile'
                 'library/codebooks//')
        file_names = [x[:-4] for x in glob.glob('*.csv')]

        # Loop through and process all codebooks
        for codebook_name in file_names:
            arguments['<codebook_name>'] = codebook_name
            main(arguments)

        print('\n\nInfograph(s) and Summary Report(s) outputted to  '
              + arguments['--output_dir'])
        
    elif arguments['<codebook_name>']:
        main(arguments)
    else:
        print(arguments)
