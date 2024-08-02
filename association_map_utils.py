#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import json
import ast

class ExcelProcessor:
    def __init__(self, file_path):
        self.workbook = pd.ExcelFile(file_path)

    def load_excel_workbook(self, file_path):
        return pd.ExcelFile(file_path)

    def read_excel_sheet(self, workbook, sheet_name):
        return pd.read_excel(workbook, sheet_name)

class NodeProcessor:
    def __init__(self, sample, map_feature, connection, d, dict1):
        self.sample = sample
        self.connection=connection
        self.merged=pd.merge(sample,connection,left_on='Node Id',right_on='from',how='outer')
        self.map_feature=map_feature
        self.d = d
        self.dict1 = dict1

    def process_node_data(self, sample, map_feature, connection, d, dict1):
      nodes = []
      x=pd.merge(self.sample,self.map_feature['Nodes'],left_on='SubType', right_on='Component')
      for index, row in x.iterrows():
          node = {
              "name": row['Name'].replace('("','(').replace('"',')').encode('ascii','ignore').decode(),
              "SubType": row['SubType'],
              "UID": row['Node Id'],
              "data_grid_properties": {
                  "data_grid_info1": " " if str(row['data_grid_info1']) == "nan" else row['data_grid_info1'],
                  "data_grid_info2": " " if str(row['data_grid_info2']) == "nan" else str(row['data_grid_info2']),
                  "data_grid_info3": " " if str(row['data_grid_info3']) == "nan" else row['data_grid_info3'],
                  "data_grid_title1": " " if str(row['data_grid_title1']) == "nan" else str(row['data_grid_title1']),
                  "data_grid_title2": " " if str(row['data_grid_title2']) == "nan" else row['data_grid_title2'],
                  "data_grid_title3": " " if str(row['data_grid_title3']) == "nan" else row['data_grid_title3'],
                  "data_grid_info4": " " if str(row['data_grid_info4']) == "nan" else row['data_grid_info4'],
                  "data_grid_title4": " " if str(row['data_grid_title4']) == "nan" else row['data_grid_title4'],
                  "data_grid_title5": " " if str(row['data_grid_title5']) == "nan" else row['data_grid_title5'],
                  "data_grid_info5": " " if str(row['data_grid_info5']) == "nan" else row['data_grid_info5'],
                  "data_grid_properties": " "
              },
              "node_properties": {
                  "node_size": int(row["node_size"]),
                  "node_shape": row["node_shape"],
                  "node_shadow": 'false' if row["node_shadow"]==0 else 'true',
                  "node_label_font_size": int(row["node_label_font_size"]),
                  "node_label_font_color": row["node_label_font_color"],
                  "node_label_font_background": row["node_label_font_background"],
                  "node_label_font_alignment": row["node_label_font_alignment"],
                  #"node_image": row["node_image"],
                  "node_image": dict1[d[row['SubType']]],
                  "node_color": row["node_color"]
              }
          }
          nodes.append(node)
      return nodes
    
class NodeProcessor1:
    def __init__(self, sample, map_feature, connection):
        self.sample = sample
        self.connection=connection
        self.merged=pd.merge(sample,connection,left_on='Node Id',right_on='from',how='outer')
        self.map_feature=map_feature

    def process_node_data(self, sample, map_feature, connection):
      nodes = []
      x=pd.merge(self.sample,self.map_feature['Nodes'],left_on='SubType', right_on='Component')
      for index, row in x.iterrows():
          node = {
              "name": row['Name'].replace('("','(').replace('"',')').encode('ascii','ignore').decode(),
              "SubType": row['SubType'],
              "UID": row['Node Id'],
              "data_grid_properties": {
                  "data_grid_info1": " " if str(row['data_grid_info1']) == "nan" else row['data_grid_info1'],
                  "data_grid_info2": " " if str(row['data_grid_info2']) == "nan" else str(row['data_grid_info2']),
                  "data_grid_info3": " " if str(row['data_grid_info3']) == "nan" else row['data_grid_info3'],
                  "data_grid_title1": " " if str(row['data_grid_title1']) == "nan" else str(row['data_grid_title1']),
                  "data_grid_title2": " " if str(row['data_grid_title2']) == "nan" else row['data_grid_title2'],
                  "data_grid_title3": " " if str(row['data_grid_title3']) == "nan" else row['data_grid_title3'],
                  "data_grid_info4": " " if str(row['data_grid_info4']) == "nan" else row['data_grid_info4'],
                  "data_grid_title4": " " if str(row['data_grid_title4']) == "nan" else row['data_grid_title4'],
                  "data_grid_title5": " " if str(row['data_grid_title5']) == "nan" else row['data_grid_title5'],
                  "data_grid_info5": " " if str(row['data_grid_info5']) == "nan" else row['data_grid_info5'],
                  "data_grid_properties": " "
              },
              "node_properties": {
                  "node_size": int(row["node_size"]),
                  "node_shape": row["node_shape"],
                  "node_shadow": 'false' if row["node_shadow"]==0 else 'true',
                  "node_label_font_size": int(row["node_label_font_size"]),
                  "node_label_font_color": row["node_label_font_color"],
                  "node_label_font_background": row["node_label_font_background"],
                  "node_label_font_alignment": row["node_label_font_alignment"],
                  "node_image": row["node_image"],
                  "node_color": row["node_color"]
              }
          }
          nodes.append(node)
      return nodes
    
class GlobalProcessor1:
    def __init__(self, node_df, distinct_values):
        self.node_df = node_df
        self.distinct_values = distinct_values

    def process_global_data(node_df, distinct_values):
      lsize = len(distinct_values) 
      legend_data = {}
      for i in range(lsize):
        url = node_df[node_df['Component'] == distinct_values[i]]['node_image'].iloc[0]
        legend_data[distinct_values[i]] = url
      return legend_data

class ConnectionProcessor:
    def __init__(self, sample, map_feature, connection):
        self.connection=connection
        self.merged=pd.merge(sample,connection,left_on='Node Id',right_on='from',how='outer')
        self.map_feature=map_feature

    def process_connection_data(self):
      sample=self.merged
      sample['to']=sample['to'].fillna(-1)
      sample["to"]=sample["to"].astype('int')
      l=[]
      node=sample['Node Id'].unique()
      for index, row in sample.iterrows():
          if row['to'] != -1 and row['to'] in node :
              con=sample[sample['Node Id']==row['to']].iloc[0]
              l.append([int(row['Node Id']),int(row['to']),row['Level']])
      df=pd.DataFrame(columns=['from','to','L2'],data=l)
      df=df.merge(self.map_feature['Edge'],on='L2').drop(['L2'],axis=1)
      df['edge_dashes']=df['edge_dashes'].astype('bool')
      df['edge_dashes']=df['edge_dashes'].replace([True,False],['true','false'])
      df.sort_values(by='from',inplace=True)
      df['UID']=[i for i in range(1,df.shape[0]+1)]

      return df.to_dict('records')

class GlobalProcessor:
    def __init__(self, dict1, distinct_values, d):
        self.dict1 = dict1
        self.distinct_values = distinct_values
        self.d = d


    def process_global_data(dict1, distinct_values, d):
      lsize = len(distinct_values) 
      legend_data = {}
      for i in range(lsize):
        legend_data[distinct_values[i]] = dict1[d[distinct_values[i]]]
      return legend_data

class JsonGenerator:
    def __init__(self, legend_data, client_name, logo_url, sidebar_short_logo, nodes, connections, nodes_df_, global_df, map_feature, node_df):
        self.legend_data = legend_data
        self.client_name = client_name
        self.logo_url = logo_url
        self.sidebar_short_logo = sidebar_short_logo
        self.nodes = nodes
        self.connections = connections
        self.map_feature=map_feature
        self.nodes_df_ = nodes_df_
        self.node_df = node_df
        self.global_df=global_df
        self.excel_dict=dict()

    def create_json_output(self, legend_data, client_name, logo_url, sidebar_short_logo, nodes, connections, nodes_df_, global_df, map_feature, node_df):
      json_list = json.loads(global_df['background_mode'][0])
      json_output = {
          'legend': legend_data,
          'client_name': client_name,
          'logo_url': logo_url,
          'sidebar_short_logo': sidebar_short_logo,
          'background_mode': json_list,
          'search_case_name': 'beacon',
          'filters': {
              'type': list(node_df['Type'].unique())
          },
          "default": {
              "node": nodes,
              "node_connections": connections
          }
      }
      return json_output

class JSONFile:
    def __init__(self, json_output, output_file_path='output.json'):
        self.json_output = json_output
        self.output_file_path = output_file_path

    def write_json_to_file(json_output, output_file_path='output.json'):
        with open(output_file_path, 'w') as json_file:
            json.dump(json_output, json_file, indent=2)
        print(f"JSON output file '{output_file_path}' generated successfully.")


def write_json_to_file(json_output, output_file_path='output.json'):
    with open(output_file_path, 'w') as json_file:
        json.dump(json_output, json_file, indent=2)
    print(f"JSON output file '{output_file_path}' generated successfully.")




