from typing import Any, Dict, List
from pandas import DataFrame, concat, merge
from lib.time import datetime_isoformat
from .pipeline import EpidemiologyPipeline


class DatadistaPipeline(EpidemiologyPipeline):
    url_base = 'https://raw.github.com/datadista/datasets/master/COVID%2019'
    data_urls: List[str] = [
        '{}/ccaa_covid19_casos_long.csv'.format(url_base),
        '{}/ccaa_covid19_fallecidos_long.csv'.format(url_base),
        '{}/ccaa_covid19_hospitalizados_long.csv'.format(url_base),
    ]

    def parse_dataframes(self, dataframes: List[DataFrame], **parse_opts):
        join_keys = ['fecha', 'CCAA']
        join_opts = {'on': join_keys, 'how': 'outer'}
        data = dataframes[0]
        data = merge(data, dataframes[1], suffixes=('confirmed', 'deceased'), **join_opts)
        data = merge(data, dataframes[2], suffixes=('', ''), **join_opts)

        data['country_code'] = 'ES'
        data = data.rename(columns={
            'fecha': 'date',
            'CCAA': 'match_string',
            'totalconfirmed': 'confirmed',
            'totaldeceased': 'deceased',
            'total': 'hospitalised',
        }).sort_values(['match_string', 'date'])

        # Data is cumulative, compute the diff
        for column in ('confirmed', 'deceased', 'hospitalised'):
            data[column] = data.groupby(['date', 'match_string'])[column].fillna(0).diff()

        # Compute the country-level stats by adding all subregions
        data_country = data.groupby(['date', 'country_code']).sum().reset_index()
        data_country['match_string'] = 'total'
        data = concat([data, data_country])

        return data[['date', 'country_code', 'match_string', 'confirmed', 'deceased', 'hospitalised']]