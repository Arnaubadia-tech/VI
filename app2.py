import streamlit as st
import pandas as pd
import altair as alt
from vega_datasets import data as vega_data

st.set_page_config(
    page_title="VI Project", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# Cargar datos
barchart = pd.read_csv('Q1dataset (3).csv')
finalstates = pd.read_csv('Q2.1dataset.csv')
finalcounties = pd.read_csv('finalcounties.csv')
scatterplot = pd.read_csv('Q3.2dataset.csv')
comparison = pd.read_csv('Q4dataset.csv')
povertydata = pd.read_csv('Q5.1dataset (1).csv')
mentaldata = pd.read_csv('Q5.2dataset (2).csv')

## Mass Shootings per Capita by State (per 100k)
state_bar_chart2 = alt.Chart(barchart).mark_bar().encode(
    x=alt.X('Shootings_Density:Q', title='Shootings per 100,000 Residents'),
    y=alt.Y('State:N', title='State', sort='-x'),
    color=alt.Color('Shootings_Density:Q', scale=alt.Scale(scheme='reds'), legend=alt.Legend(title='Shootings per 100k'))
).properties(
    title=alt.TitleParams(
        text='Mass Shootings per Capita by State',
        fontSize=16,
        fontWeight='bold'
    ),
    width=300,
    height=400
)

## Mapa coroplético por estado
states = alt.topo_feature(vega_data.us_10m.url, 'states')
color_scale = alt.Scale(scheme="reds", domain=[0, finalstates['Shootings_Density'].max()], clamp=True)

## Gráfico choropleth para todos los Estados Unidos
choropleth = alt.Chart(states).mark_geoshape().encode(
    color=alt.Color(
        'Shootings_Density:Q', 
        title='Shootings per 100k', 
        scale=color_scale
    ),
    tooltip=['State:N', 'Shootings_Density:Q']
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(finalstates, 'FIPS', ['State', 'Shootings_Density'])
).properties(
    width=300,
    height=400,
    title=alt.TitleParams(
        text="Mass Shootings per 100,000 Residents by State in the US",
        fontSize=14,
        fontWeight='bold'
    )
).project(
    type='albersUsa'
).configure_legend(
    orient='bottom',
    titleFontSize=10,
    labelFontSize=8
)


## Counties
# County geometry
counties = alt.topo_feature(vega_data.us_10m.url, 'counties')

county_choropleth = alt.Chart(counties).mark_geoshape().encode(
   color=alt.condition(
        "datum.Shootings_Density > 0",
        alt.Color('Shootings_Density:Q', scale=color_scale, title='Shootings per 100k'),
        alt.value('#F5F5F5')  
    ),
    tooltip=['county_name:N', 'state_name:N', 'Shootings_Density:Q']
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(finalcounties, 'FIPS', ['county_name', 'state_name', 'Shootings_Density'])
).properties(
    width=300,
    height=400,
    title=alt.TitleParams(
        text="Mass Shootings per 100,000 Residents by County in the US",
        fontSize=14,
        fontWeight='bold'
    )
).project(
    type='albersUsa'
).configure_legend(
    orient='bottom',
    titleFontSize=10,
    labelFontSize=8
)



# Gráfico de dispersión de incidentes escolares y tiroteos

scatter_plot = alt.Chart(scatterplot).mark_point(filled=True,opacity=0.6).encode(
    x=alt.X('Incidents_Density:Q', title='School Incidents per 100k'),
    y=alt.Y('Shootings_Density:Q', title='Mass Shootings per 100k'),
    tooltip=['State:N', 'Incidents_Density:Q', 'Shootings_Density:Q'],
    size='population:Q'
).properties(
    title="School Incidents vs. School Shootings per 100,000 Residents by State",
    width=800,
    height=600
)

regression_line = alt.Chart(scatterplot).transform_regression(
    'Incidents_Density', 'Shootings_Density'
).mark_line(color='red').encode(
    x='Incidents_Density:Q',
    y='Shootings_Density:Q'
)

final_plot = (scatter_plot + regression_line).properties(
    width=300,
    height=400,
    title=alt.TitleParams(
        text="School Incidents vs Mass Shootings",
        fontSize=14,
        fontWeight='bold'
    )
).configure_legend(
    titleFontSize=10,
    labelFontSize=8,
    orient='bottom'
)


## Line chart evolución
trend_chart = alt.Chart(comparison).mark_line().encode(
    x=alt.X('Year_Month:T', title='Year-Month'),
    y=alt.Y('count:Q', title='Number of incidents & Median per year'),
    tooltip=['Year_Month:T', 'count:Q']
)

# Línea de mediana anual en color rojo
median_rule = alt.Chart(comparison).mark_line(color='red').encode(
    x=alt.X('Year_Month:T'),
    y=alt.Y('yearly_median:Q'),
    detail='Years:N' 
)

# Leyenda para la línea de mediana debajo del gráfico
legend_text = alt.Chart().mark_text(
    align='left',
    baseline='top',
    fontSize=10,
    font='Arial',
    color='red',
    dx=5, dy=-10  # Ajuste de posición
).encode(
    x=alt.value(10),  # Posición fija en el eje X
    y=alt.value(380),  # Posición fija en el eje Y
    text=alt.value("Red line: Yearly median of shootings")  # Texto de la leyenda
)

final_chart = (trend_chart + median_rule ).properties(
    width=300,
    height=400,
    title=alt.TitleParams(
        text="Mass Shootings Timeline",
        fontSize=14,
        fontWeight='bold'
    )
).configure_legend(
    titleFontSize=10,
    labelFontSize=8,
    orient='bottom'
)

##Extra graphs
#Poverty
scatter_plot2 = alt.Chart(povertydata).mark_point(filled=True, opacity=0.7).encode(
    x=alt.X('PovertyRatesPercentOfPopulationBelowPovertyLevel:Q', title='Poverty Rate (%)',scale=alt.Scale(zero=False)),
    y=alt.Y('Shootings_Density:Q', title='Mass Shootings per 100k'),
    tooltip=['State:N', 'PovertyRatesPercentOfPopulationBelowPovertyLevel:Q', 'Shootings_Density:Q'],
    size='population:Q'
)

regression_line2 = alt.Chart(povertydata).transform_regression(
    'PovertyRatesPercentOfPopulationBelowPovertyLevel', 'Shootings_Density'
).mark_line(color='red').encode(
    x='PovertyRatesPercentOfPopulationBelowPovertyLevel:Q',
    y='Shootings_Density:Q'
)

final_plot2 = (scatter_plot2 + regression_line2).properties(
    width=300,
    height=400,
    title=alt.TitleParams(
        text="Poverty Rate vs Mass Shootings",
        fontSize=14,
        fontWeight='bold'
    )
).configure_legend(
    titleFontSize=10,
    labelFontSize=8,
    orient='bottom'
)

## Mental illness
scatter_plot3 = alt.Chart(mentaldata).mark_point(filled=True, opacity=0.7).encode(
    x=alt.X('MentalHealthStatisticsRatesOfMentalIllness:Q', title='Mental Illness(%)',scale=alt.Scale(zero=False)),
    y=alt.Y('Shootings_Density:Q', title='Mass Shootings per 100k'),
    tooltip=['State:N', 'MentalHealthStatisticsRatesOfMentalIllness:Q', 'Shootings_Density:Q'],
    size='population:Q'
)

regression_line3 = alt.Chart(mentaldata).transform_regression(
    'MentalHealthStatisticsRatesOfMentalIllness', 'Shootings_Density'
).mark_line(color='red').encode(
    x='MentalHealthStatisticsRatesOfMentalIllness:Q',
    y='Shootings_Density:Q'
)

final_plot3 = (scatter_plot3 + regression_line3).properties(
    width=300,
    height=400,
    title=alt.TitleParams(
        text="Mental Health vs Mass Shootings",
        fontSize=14,
        fontWeight='bold'
    )
).configure_legend(
    titleFontSize=10,
    labelFontSize=8,
    orient='bottom'
)


## Display layout
st.markdown("<h1 style='text-align: center;'>Mass Shootings in the US</h1>", unsafe_allow_html=True)

st.altair_chart(state_bar_chart2, use_container_width=True)

# Añadir espacio entre filas
st.markdown("<div style='padding-top: 30px;'></div>", unsafe_allow_html=True)

# Segunda fila - 2 gráficos
col1, col2 = st.columns(2)

with col1:
    st.altair_chart(choropleth, use_container_width=True)

with col2:
    st.altair_chart(county_choropleth, use_container_width=True)

# Añadir espacio entre filas
st.markdown("<div style='padding-top: 30px;'></div>", unsafe_allow_html=True)

# Tercera fila - 1 gráfico
st.altair_chart(final_chart, use_container_width=True)

# Añadir espacio entre filas
st.markdown("<div style='padding-top: 30px;'></div>", unsafe_allow_html=True)

# Cuarta fila - 3 gráficos
col3, col4, col5 = st.columns(3)

with col3:
    st.altair_chart(final_plot, use_container_width=True)

with col4:
    st.altair_chart(final_plot2, use_container_width=True)

with col5:
    st.altair_chart(final_plot3, use_container_width=True)
