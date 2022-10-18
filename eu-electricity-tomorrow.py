#!/usr/bin/env python

from entsoe import EntsoePandasClient

import entsoe.geo
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import logging
import os

from datetime import date,timedelta
import time

from config import create_api

logger = logging.getLogger()

def prepare_data(start, end):
    zones = ["AT","CZ", "EE","GR","IT_CNOR","IT_NORD","NO_1","NO_5","RS","SE_4","BE","DE_LU","ES","HR","IT_SARD","LT","NO_2","PL","SE_1","SI","BG","DK_1","FI","HU","IT_CSUD","IT_SICI","LV","NO_3","PT","SE_2","SK","CH","DK_2","FR","IT_CALA","IT_SUD","NL","NO_4","RO","SE_3"]

    geo_df = entsoe.geo.load_zones(zones, pd.Timestamp(date.today()))


    client = EntsoePandasClient(api_key=os.getenv("ENTSOE_API_KEY"))

    file_name='entsoe.p'
    if os.path.exists(file_name):
        df = pd.read_pickle(file_name)
    else:
        df = pd.DataFrame()

    if len(df.columns)-1 != len(zones) or start != df.index[0] or end != df.index[-1]:
        df = pd.DataFrame()
        for zone in zones:
        
            print(zone)
            df[zone] = client.query_day_ahead_prices(zone, start=start, end=end)

            df['date'] = pd.to_datetime(df.index).date
            df.to_pickle(file_name)  # save it
            time.sleep(1)

    df2 = df.groupby('date').mean()
    df2.reset_index(drop=True, inplace=True)
    df2.set_index(pd.Index(["today", "tomorrow"]), inplace=True)
    df2 = df2.T
    df2.index.rename('zoneName', inplace=True)
    df2.dropna(inplace=True)
    df2.today = df2.today.round(0).astype(int)
    df2.tomorrow = df2.tomorrow.round(0).astype(int)
    df2["delta"] = df2.tomorrow - df2.today
    df2.delta = df2.delta.apply(lambda x: '+'+str(x) if x > 0 else str(x) )
    return geo_df.merge(df2, on='zoneName')



###
def create_image(geo_df, title_text, filename):
    fig = px.choropleth(geo_df,
                    geojson=geo_df.geometry,
                    locations=geo_df.index,
                    color="tomorrow",
                    color_discrete_sequence= px.colors.sequential.Plasma_r,
                    scope="europe",
                    width=1024,
                    height=1024,
                    featureidkey="id",
                    labels={'today':'today', 'tomorrow':'tomorrow'}
                    )
    fig.data[0].marker.line.color = "#cccccc"
    fig.update_layout(coloraxis_showscale=False)
    fig.update_layout(title_text=title_text, title_x=0.5, title_y=0.12)

    geo_df["delta_color"] = geo_df.delta.apply( lambda x: 'red' if '+' in x else 'green' if '-' in x else 'black' )
    xw=1.4
    xy=0.7
    geo_df3 = geo_df.to_crs("EPSG:4326")
    for i in range(len(geo_df)):
        fig.add_trace(
            go.Scattergeo(
                lon = [geo_df3.centroid.x[i]-xw, geo_df3.centroid.x[i]+xw, geo_df3.centroid.x[i]+xw, geo_df3.centroid.x[i]+xw, geo_df3.centroid.x[i]-xw, geo_df3.centroid.x[i]-xw],
                lat = [geo_df3.centroid.y[i]+xy, geo_df3.centroid.y[i]+xy, geo_df3.centroid.y[i]-xy, geo_df3.centroid.y[i]-xy, geo_df3.centroid.y[i]-xy, geo_df3.centroid.y[i]+xy],
                fillcolor="white",
                opacity = 0.8,
                fill="toself",
                mode = 'lines',
                line = dict(width = 1,color = '#cccccc'),
                showlegend=False
            )
        )
    fig.add_scattergeo(
        lat = geo_df3.centroid.y+0.2,
        lon = geo_df3.centroid.x,
        text = geo_df3["tomorrow"].astype(str),
        mode = 'text',
        textfont =dict(
            size=16,
            color="black"
        )
    )
    fig.add_scattergeo(
        lat = geo_df3.centroid.y-0.25,
        lon = geo_df3.centroid.x-0.2,
        text = geo_df3["delta"],
        mode = 'text',
        textfont =dict(
            size=10,
            color=geo_df3["delta_color"]
        )
    )
    fig.update_layout(showlegend=False)
    fig.update_geos(fitbounds="locations", visible=False)
    #fig.show()
    if not os.path.exists(filename):
        fig.write_image(filename, width=1024, height=1024)
    return filename



def status_update(api, filename, title_text):
    try:
        media = api.media_upload(filename=filename)
        api.update_status(status=title_text, media_ids=[media.media_id_string])
        logger.info("Status update OK")
    except Exception as e:
        logger.error("Error updating status", exc_info=True)
        raise e

def main():
    start = pd.Timestamp(date.today(), tz='Europe/Vienna')
    end = start+timedelta(days=2)+timedelta(hours=-1)

    geo_df = prepare_data(start, end)
    title_text = "EU electricity day-ahead prices EUR/MWh " + end.strftime("%d.%m.%Y")+". Data source ENTSEO-E."
    filename = "day-ahead-"+end.strftime("%d.%m.%Y")+".png"    
    filename = create_image(geo_df, title_text, filename)
    api = create_api()
    status_update(api, filename, title_text)  


if __name__ == "__main__":
    main()