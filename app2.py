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
data = pd.read_csv('VIProjectMassShoting-csv2.csv')
counties_df = pd.read_csv('co-est2023-alldata.csv', encoding='latin1')
school_df = pd.read_csv('school.csv')
poverty = pd.read_csv('poverty.csv')
mental = pd.read_csv('mental_ill.csv')
finalcounties = pd.read_csv('finalcounties.csv')
finalstates = pd.read_csv('Q2.1dataset.csv')

# Preprocesamiento de datos
counties_df = counties_df.rename(columns={'CTYNAME': 'County Names', 'STNAME': 'State'})
counties2_df = counties_df[counties_df['COUNTY'] != 0]
merged_df = pd.merge(data, counties2_df[['County Names', 'State', 'POPESTIMATE2023']], on=['County Names', 'State'], how='left')
data = merged_df

# Count per state
state_aggregates = data.groupby('State').agg(
    shooting_count=('id', 'count'),
    population=('Population', 'first')
).reset_index()
state_aggregates['per_100k'] = (state_aggregates['shooting_count'] / state_aggregates['population']) * 100000

## Mass Shootings per Capita by State (per 100k)
state_bar_chart2 = alt.Chart(state_aggregates).mark_bar().encode(
    x=alt.X('per_100k:Q', title='Shootings per 100,000 Residents'),
    y=alt.Y('State:N', title='State', sort='-x'),  
    color=alt.Color('per_100k:Q', 
                   scale=alt.Scale(scheme='reds'), 
                   legend=alt.Legend(title='Shootings per 100k', 
                                   orient='bottom',
                                   titleFontSize=10,
                                   labelFontSize=8,
    legendX=0,
    direction='horizontal',
    padding=5))
).properties(
    title=alt.TitleParams(
        text='Mass Shootings per Capita by State',
        fontSize=14,
        fontWeight='bold'
    ),
    width=300,
    height=400
)

# Mapa coroplético por estado

states = alt.topo_feature(vega_data.us_10m.url, 'states')
color_scale = alt.Scale(scheme="reds", domain=[0, finalstates['Shootings_Density'].max()], clamp=True)

## Gráfico choropleth para todos los Estados Unidos
choropleth = alt.Chart(states).mark_geoshape().encode(
    color=alt.Color('per_100k:Q', 
                   title='Shootings per 100k', 
                   scale=color_scale,
                   legend=alt.Legend(orient='bottom',
                                   titleFontSize=10,
                                   labelFontSize=8)),
    tooltip=['State:N', 'per_100k:Q']
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(finalstates, 'id', ['State', 'per_100k'])
).properties(
    width=300,
    height=400,
    title=alt.TitleParams(
        text="Mass Shootings Distribution by State",
        fontSize=14,
        fontWeight='bold'
    )
).project(
    type='albersUsa'
)

## Counties
# County geometry
counties = alt.topo_feature(vega_data.us_10m.url, 'counties')

county_choropleth = alt.Chart(counties).mark_geoshape().encode(
   color=alt.condition(
        "datum.Shootings_Density > 0",
        alt.Color('Shootings_Density:Q', scale=color_scale, title='Shootings per 100k'),
        alt.value('#F5F5F5')  # Grey for zero shootings
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
)


# Gráfico de dispersión de incidentes escolares y tiroteos
state_aggregates_incidents = school_df.groupby('State').agg(
    incident_count=('Incident ID', 'count'),
    population=('State Population', 'first')
).reset_index()
state_aggregates_incidents['incidents_per_100k'] = (state_aggregates_incidents['incident_count'] / state_aggregates_incidents['population']) * 100000
state_aggregates_global = pd.merge(state_aggregates, state_aggregates_incidents[['State', 'incidents_per_100k']], on='State')

scatter_plot = alt.Chart(state_aggregates_global).mark_point(filled=True).encode(
    x=alt.X('incidents_per_100k:Q', title='School Incidents per 100k'),
    y=alt.Y('per_100k:Q', title='School Shootings per 100k'),
    tooltip=['State:N', 'incidents_per_100k:Q', 'per_100k:Q'],
    size='population:Q'
)
regression_line = alt.Chart(state_aggregates_global).transform_regression(
    'incidents_per_100k', 'per_100k'
).mark_line(color='red').encode(
    x='incidents_per_100k:Q',
    y='per_100k:Q'
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
data['Incident Date'] = pd.to_datetime(data['Incident Date'])
data['Years'] = data['Incident Date'].dt.year
data['Year_Month'] = data['Incident Date'].dt.to_period('M').astype(str)

monthly_counts = data.groupby('Year_Month').size().reset_index(name='count')

yearly_median = monthly_counts.copy()
yearly_median['Years'] = pd.to_datetime(yearly_median['Year_Month']).dt.year
median_per_year = yearly_median.groupby('Years')['count'].median().reset_index(name='yearly_median')

monthly_counts = monthly_counts.merge(
    median_per_year,
    left_on=pd.to_datetime(monthly_counts['Year_Month']).dt.year,
    right_on='Years',
    how='left'
)
# Monthly
trend_chart = alt.Chart(monthly_counts).mark_line().encode(
    x=alt.X('Year_Month:T', title='Year-Month'),
    y=alt.Y('count:Q', title='Number of incidents & Median per year'),
    tooltip=['Year_Month:T', 'count:Q']
)

# Línea de mediana anual en color rojo
median_rule = alt.Chart(monthly_counts).mark_line(color='red').encode(
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
poverty = pd.read_csv('poverty.csv')
poverty = poverty.rename(columns={'state': 'State'})

#Merge with data, adding rate
poverty = pd.merge(data, poverty[['State', 'PovertyRatesPercentOfPopulationBelowPovertyLevel']], on='State', how='left')
# Add state aggregates
merged_poverty = pd.merge(poverty, state_aggregates, on='State')

# Graph
scatter_plot2 = alt.Chart(merged_poverty).mark_point(filled=True).encode(
    x=alt.X('PovertyRatesPercentOfPopulationBelowPovertyLevel:Q', title='Poverty Rate (%)',scale=alt.Scale(zero=False)),
    y=alt.Y('per_100k:Q', title='School Shootings per 100k'),
    tooltip=['State:N', 'PovertyRatesPercentOfPopulationBelowPovertyLevel:Q', 'per_100k:Q'],
    size='population:Q'
)
# Regression line
regression_line2 = alt.Chart(merged_poverty).transform_regression(
    'PovertyRatesPercentOfPopulationBelowPovertyLevel', 'per_100k'
).mark_line(color='red').encode(
    x='PovertyRatesPercentOfPopulationBelowPovertyLevel:Q',
    y='per_100k:Q'
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
mental = pd.read_csv('mental_ill.csv')
mental = mental.rename(columns={'state': 'State'})
# Fusionar los datos de enfermedades mentales con el dataset principal data
mental = pd.merge(data, mental[['State', 'MentalHealthStatisticsRatesOfMentalIllness']], on='State', how='left')
# Add state aggregate
merged_mental = pd.merge(mental, state_aggregates, on='State')

# Crear el gráfico de dispersión
scatter_plot3 = alt.Chart(merged_mental).mark_point(filled=True).encode(
    x=alt.X('MentalHealthStatisticsRatesOfMentalIllness:Q', title='Mental Illness (%)',scale=alt.Scale(zero=False)),
    y=alt.Y('per_100k:Q', title='Mass Shootings per 100k'),
    tooltip=['State:N', 'MentalHealthStatisticsRatesOfMentalIllness:Q', 'per_100k:Q'],
    size='population:Q'
)
# Regression line
regression_line3 = alt.Chart(merged_mental).transform_regression(
    'MentalHealthStatisticsRatesOfMentalIllness', 'per_100k'
).mark_line(color='red').encode(
    x='MentalHealthStatisticsRatesOfMentalIllness:Q',
    y='per_100k:Q'
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

# Display layout
st.markdown("<h1 style='text-align: center;'>Mass Shootings in the US</h1>", unsafe_allow_html=True)


col1, col2, col3 = st.columns(3)

with col1:
    st.altair_chart(state_bar_chart2, use_container_width=True)

with col2:
    st.altair_chart(choropleth, use_container_width=True)

with col3:
    st.altair_chart(county_choropleth, use_container_width=True)

# Add space between rows
st.markdown("<div style='padding-top: 30px;'></div>", unsafe_allow_html=True)

# Second row - 4 graphs
col4, col5, col6, col7 = st.columns(4)

with col4:
    st.altair_chart(final_plot, use_container_width=True)

with col5:
    st.altair_chart(final_chart, use_container_width=True)

with col6:
    st.altair_chart(final_plot2, use_container_width=True)

with col7:
    st.altair_chart(final_plot3, use_container_width=True)
