import streamlit as st
import requests
import time
import datetime
import pandas as pd
import plotly.express as px

st.set_page_config(
	layout="wide",
	page_title="yields Visualizer",
	page_icon="🦙",
	initial_sidebar_state="collapsed",
)



@st.cache_data(ttl=60*10)
def get_pools():
	def get(i=0):
		if i > 15:
			raise Exception('Too many retries')
		url = 'https://yields.llama.fi/pools'
		response = requests.get(url)
		if response.status_code == 200:
			return pd.DataFrame(response.json()['data'])
		else:
			time.sleep(5)
			return get(i=i+1)
	return get()

@st.cache_data(ttl=60*10)
def get_pool_detail(id):
	def get(id, i=0):
		if i > 15:
			raise Exception('Too many retries')
		url = f'https://yields.llama.fi/chart/{id}'
		response = requests.get(url)
		if response.status_code == 200:
			return pd.DataFrame(response.json()['data'])
		else:
			time.sleep(5)
			return get(id, i=i+1)
	return get(id)

st.write('# Yields visualizer')
st.write('built by [notawizard.eth](https://twitter.com/0xDoing/)')
st.write('## Pools')
st.write('you can also use https://defillama.com/yields')
pools = get_pools()
st.write(pools)
st.write('## Pool details')
pool_ids_str = st.text_input('Pool IDs (comma separated)', 
	value='f2726d05-1f8d-4b9c-80e3-43d03d85d117,23ad3581-f009-4b95-98ca-2a5f7fa8b0f2')

pool_ids = [x.strip() for x in pool_ids_str.split(',')]

pool_details = []
for id in pool_ids:
	tmp_df = get_pool_detail(id)
	tmp_df['pool_id'] = id
	tmp = pools[pools['pool'] == id].iloc[0]
	name = f"{tmp['chain']}-{tmp['project']}-{tmp['symbol']}-{tmp['pool'][0:5]}"
	tmp_df['name'] = name
	pool_details.append(tmp_df)

pool_details = pd.concat(pool_details)
pool_details['timestamp'] = pd.to_datetime(pool_details['timestamp'])
pool_details = pool_details[[
	'name',
	'timestamp',
	'tvlUsd',
	'apy',
	'apyBase',
	'apyReward',
	'il7d',
	'apyBase7d',
	'pool_id'
]]

with st.expander('pool details table'):
	st.write(pool_details)

column_selected = st.selectbox('Column to plot', ['tvlUsd', 'apy', 'apyBase', 'apyReward', 'il7d', 'apyBase7d'], index=1)

days_to_show = st.number_input('Days to show', min_value=1, max_value=300, value=180, step=1)

# timestamp is datetime64[ns, UTC]
pool_details = pool_details[pool_details.set_index('timestamp').tz_localize(None).index > datetime.datetime.now() - datetime.timedelta(days=days_to_show)]

plot_pools_separately = st.checkbox('Plot pools separately', value=False)
fig = px.line(
	pool_details, 
	x='timestamp', 
	y=column_selected, 
	color='name',
	facet_row='name' if plot_pools_separately else None,
	title = f'{column_selected} over time',
	height=700
)

# rangeslider
fig.update_xaxes(rangeslider_visible=True, )

for a in fig.layout.annotations:
    a.text = ''

st.plotly_chart(fig, use_container_width=True)

