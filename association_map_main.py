import streamlit as st
import firebase_admin

from firebase_admin import credentials
from firebase_admin import auth

import pandas as pd
import json
from io import BytesIO

import psycopg2

from association_map_utils import NodeProcessor1, NodeProcessor, ConnectionProcessor, GlobalProcessor, GlobalProcessor1, JsonGenerator, write_json_to_file

# @st.cache_resource
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()


# Perform query.
# Uses st.experimental_memo to only rerun when the query change
@st.cache_data(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()

        st.success("Data inserted successfully!")


# Validation function
def validate_excel(file_path1, file_path2):
    # Load Excel file
    try:
        xls_AM = pd.ExcelFile(file_path1)
        xls_RM = pd.ExcelFile(file_path2)
    except pd.errors.ExcelFileNotFound:
        st.error("File not found. Please upload a valid Excel file.")
        return None

    # Check for number of sheets
    sheets_AM = xls_AM.sheet_names
    if "Node" not in sheets_AM or "Connections" not in sheets_AM:
        st.error("Missing required sheets. Please include 'Node' and 'Connections' in Association Map Excel File.")
        return None
    
    sheets_RM = xls_RM.sheet_names
    if "Nodes" not in sheets_RM or "Edge" not in sheets_RM or "Global" not in sheets_RM or "Global" not in sheets_RM:
        st.error("Missing required sheets. Please include 'Nodes', 'Edge' and 'Global' in Relationshipmap Features Excel File.")
        return None

    # Load data from sheets
    nodes_df = pd.read_excel(xls_AM, "Node")
    connections_df = pd.read_excel(xls_AM, "Connections")
    node_com_df = pd.read_excel(xls_RM, "Nodes")
    edge_df = pd.read_excel(xls_RM, "Edge")
    global_df = pd.read_excel(xls_RM, "Global")

    # Validate columns in sheets
    node_columns = ['Node Id', 'Name', 'Type', 'Relationship', 'SubType',
                    'data_grid_title1', 'data_grid_info1', 'data_grid_title2', 'data_grid_info2',
                    'data_grid_title3', 'data_grid_info3', 'data_grid_title4', 'data_grid_info4',
                    'data_grid_title5', 'data_grid_info5']

    connections_columns = ['UId', 'from', 'to', 'Level']

    node_com_columns = ['Component', 'node_image', 'node_color', 'node_label_font_alignment', 'node_label_font_color', 'node_label_font_background', 'node_label_font_size', 'node_shape', 'node_size', 'node_shadow']
    edge_columns = ['L2', 'edge_width', 'edge_color', 'edge_length', 'edge_dashes', 'connection_type']
    global_columns = ['client_name', 'logo_url', 'sidebar_short_logo', 'background_mode', 'legend_Target Entity', 'legend_Organisation', 'legend_Individual', 'legend_Observations']

    if not all(col in nodes_df.columns for col in node_columns):
        st.error("Missing columns in 'Node' sheet Association Map.")
        return None

    if not all(col in connections_df.columns for col in connections_columns):
        st.error("Missing columns in 'Connections' sheet Association Map.")
        return None
    
    if not all(col in node_com_df.columns for col in node_com_columns):
        st.error("Missing columns in 'Nodes' sheet of Relationshipmap Features.")
        return None

    if not all(col in edge_df.columns for col in edge_columns):
        st.error("Missing columns in 'Edge' sheet of Relationshipmap Features.")
        return None
    
    if not all(col in global_df.columns for col in global_columns):
        st.error("Missing columns in 'Global' sheet of Relationshipmap Features.")
        return None

    # Check for blank rows in both sheets
    empty_rows = nodes_df[nodes_df.isnull().all(axis=1) | (nodes_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in node sheet of Association Map")
        return None

    empty_rows = connections_df[connections_df.isnull().all(axis=1) | (connections_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in Connection sheet of Association Map")
        return None

    empty_rows = node_com_df[node_com_df.isnull().all(axis=1) | (node_com_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in nodes sheet of Relationshipmap Features")
        return None
    
    empty_rows = edge_df[edge_df.isnull().all(axis=1) | (edge_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in edge sheet of Relationshipmap Features")
        return None
    
    empty_rows = global_df[global_df.isnull().all(axis=1) | (global_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in global sheet of Relationshipmap Features")
        return None
    

    # Validate datatypes using pd.to_numeric and pd.to_datetime
    node_datatypes = {'Node Id': 'int', 'Name': 'string', 'Type': 'string', 'Relationship': 'string',
                      'SubType': 'string', 'data_grid_title1': 'string', 'data_grid_info1': 'string',
                      'data_grid_title2': 'string', 'data_grid_info2': 'string',
                      'data_grid_title3': 'string', 'data_grid_info3': 'string',
                      'data_grid_title4': 'string', 'data_grid_info4': 'string',
                      'data_grid_title5': 'string', 'data_grid_info5': 'string'}

    connections_datatypes = {'UId': 'string', 'from': 'int', 'to': 'int', 'Level': 'string'}

    node_com_datatypes = {'Component': 'string', 'node_image': 'string', 'node_color': 'string', 'node_label_font_alignment': 'string', 'node_label_font_color': 'string', 'node_label_font_background': 'string', 'node_label_font_size': 'int', 'node_shape': 'string', 'node_size': 'int', 'node_shadow':'int'}
    edge_datatypes = {'L2': 'string', 'edge_width': 'int', 'edge_color': 'string', 'edge_length': 'int', 'edge_dashes': 'int', 'connection_type': 'string'}
    global_datatypes = {'client_name': 'string', 'logo_url': 'string', 'sidebar_short_logo': 'string', 'background_mode': 'string', 'legend_Target Entity': 'string', 'legend_Organisation': 'string', 'legend_Individual': 'string', 'legend_Observations': 'string'}
    
    try:
        nodes_df = nodes_df.astype(node_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Node' sheet: {e}")
        return None

    try:
        connections_df = connections_df.astype(connections_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Connections' sheet: {e}")
        return None

    try:
        node_com_df = node_com_df.astype(node_com_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Nodes' sheet: {e}")
        return None

    try:
        edge_df = edge_df.astype(edge_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Edge' sheet: {e}")
        return None

    try:
        global_df = global_df.astype(global_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Global' sheet: {e}")
        return None
  

    # Logical validation rules
    # Rule 1: Subtype of the node should be present in the component column in sheet Nodes
    # of another excel file named relationshipmap Features
    relationshipmap_features = pd.read_excel(xls_RM, 'Nodes')
    if not nodes_df['SubType'].isin(relationshipmap_features['Component']).all():
        st.error("Subtype of the node should be present in the component column in sheet Nodes")
        return None

    # Rule 2: Node ID should be distinct in Node sheet
    if not nodes_df['Node Id'].is_unique:
        st.error("Duplicate Node IDs found in Node sheet.")
        return None

    # Rule 3: Node Id should exist in Node sheet for all the ids present in 'From' and 'To' of Connections sheet
    connection_node_ids = set(connections_df['from'].tolist() + connections_df['to'].tolist())
    if not set(nodes_df['Node Id']).issuperset(connection_node_ids):
        st.error("Node IDs in Connections not found in Node.")
        return None

    # Rule 4: Level in Sample Format – Connections should be present in the L2 column of Edge - Default
    # sheet in relationshipmapfeatures excel file
    edge_default_sheet = pd.read_excel(xls_RM, 'Edge')
    if not connections_df['Level'].isin(edge_default_sheet['L2']).all():
        st.error("Level in Sample Format - Connections should be present in the L2 column of Edge - Default sheet.")
        return None

    # Rule 5: Check if it has More than 1 Target Entity in SubType column of Node
    target_value = 'Target Entity'
    target_entity_count = nodes_df['SubType'].eq(target_value).sum()
    if (target_entity_count > 1).any():
        st.error("More than 1 Target Entity found in SubType column of Node.")
        return None

    # Rule 6: In Connections for all values in 'From' column, there should be a value in 'To' column
    missing_to_values = connections_df[connections_df['from'].isin(nodes_df['Node Id']) & connections_df['to'].isna()]
    if not missing_to_values.empty:
        st.error("In Sample Format - Connections, missing 'To' values for some 'From' values.")
        return None

    # If all logical validations pass, return the validated dataframes
    return nodes_df, connections_df, node_com_df, edge_df, global_df

# Validation function for choose from UI part
def validate_excel1(file_path1, file_path2):
    # Load Excel file
    try:
        xls_AM = pd.ExcelFile(file_path1)
        xls_RM = pd.ExcelFile(file_path2)
    except pd.errors.ExcelFileNotFound:
        st.error("File not found. Please upload a valid Excel file.")
        return None

    # Check for number of sheets
    sheets_AM = xls_AM.sheet_names
    if "Node" not in sheets_AM or "Connections" not in sheets_AM:
        st.error("Missing required sheets. Please include 'Node' and 'Connections' in Association Map Excel File.")
        return None
    
    sheets_RM = xls_RM.sheet_names
    if "Nodes" not in sheets_RM or "Edge" not in sheets_RM or "Global" not in sheets_RM or "Global" not in sheets_RM:
        st.error("Missing required sheets. Please include 'Nodes', 'Edge' and 'Global' in Relationshipmap Features Excel File.")
        return None

    # Load data from sheets
    nodes_df = pd.read_excel(xls_AM, "Node")
    connections_df = pd.read_excel(xls_AM, "Connections")
    node_com_df = pd.read_excel(xls_RM, "Nodes")
    edge_df = pd.read_excel(xls_RM, "Edge")
    global_df = pd.read_excel(xls_RM, "Global")

    # Validate columns in sheets
    node_columns = ['Node Id', 'Name', 'Type', 'Relationship', 'SubType',
                    'data_grid_title1', 'data_grid_info1', 'data_grid_title2', 'data_grid_info2',
                    'data_grid_title3', 'data_grid_info3', 'data_grid_title4', 'data_grid_info4',
                    'data_grid_title5', 'data_grid_info5']

    connections_columns = ['UId', 'from', 'to', 'Level']

    node_com_columns = ['Component', 'node_image', 'node_color', 'node_label_font_alignment', 'node_label_font_color', 'node_label_font_background', 'node_label_font_size', 'node_shape', 'node_size', 'node_shadow']
    edge_columns = ['L2', 'edge_width', 'edge_color', 'edge_length', 'edge_dashes', 'connection_type']
    global_columns = ['client_name', 'logo_url', 'sidebar_short_logo', 'background_mode', 'legend_Target Entity', 'legend_Organisation', 'legend_Individual', 'legend_Observations']

    if not all(col in nodes_df.columns for col in node_columns):
        st.error("Missing columns in 'Node' sheet Association Map.")
        return None

    if not all(col in connections_df.columns for col in connections_columns):
        st.error("Missing columns in 'Connections' sheet Association Map.")
        return None
    
    if not all(col in node_com_df.columns for col in node_com_columns):
        st.error("Missing columns in 'Nodes' sheet of Relationshipmap Features.")
        return None

    if not all(col in edge_df.columns for col in edge_columns):
        st.error("Missing columns in 'Edge' sheet of Relationshipmap Features.")
        return None
    
    if not all(col in global_df.columns for col in global_columns):
        st.error("Missing columns in 'Global' sheet of Relationshipmap Features.")
        return None

    # Check for blank rows in both sheets
    empty_rows = nodes_df[nodes_df.isnull().all(axis=1) | (nodes_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in node sheet of Association Map")
        return None

    empty_rows = connections_df[connections_df.isnull().all(axis=1) | (connections_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in Connection sheet of Association Map")
        return None

    empty_rows = node_com_df[node_com_df.isnull().all(axis=1) | (node_com_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in nodes sheet of Relationshipmap Features")
        return None
    
    empty_rows = edge_df[edge_df.isnull().all(axis=1) | (edge_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in edge sheet of Relationshipmap Features")
        return None
    
    empty_rows = global_df[global_df.isnull().all(axis=1) | (global_df == '').all(axis=1)]
    # Check if there are any empty rows
    if len(empty_rows) > 0:
        st.error("Empty rows in global sheet of Relationshipmap Features")
        return None
    

    # Validate datatypes using pd.to_numeric and pd.to_datetime
    node_datatypes = {'Node Id': 'int', 'Name': 'string', 'Type': 'string', 'Relationship': 'string',
                      'SubType': 'string', 'data_grid_title1': 'string', 'data_grid_info1': 'string',
                      'data_grid_title2': 'string', 'data_grid_info2': 'string',
                      'data_grid_title3': 'string', 'data_grid_info3': 'string',
                      'data_grid_title4': 'string', 'data_grid_info4': 'string',
                      'data_grid_title5': 'string', 'data_grid_info5': 'string'}

    connections_datatypes = {'UId': 'string', 'from': 'int', 'to': 'int', 'Level': 'string'}

    node_com_datatypes = {'Component': 'string', 'node_image': 'string', 'node_color': 'string', 'node_label_font_alignment': 'string', 'node_label_font_color': 'string', 'node_label_font_background': 'string', 'node_label_font_size': 'int', 'node_shape': 'string', 'node_size': 'int', 'node_shadow':'int'}
    edge_datatypes = {'L2': 'string', 'edge_width': 'int', 'edge_color': 'string', 'edge_length': 'int', 'edge_dashes': 'int', 'connection_type': 'string'}
    global_datatypes = {'client_name': 'string', 'logo_url': 'string', 'sidebar_short_logo': 'string', 'background_mode': 'string', 'legend_Target Entity': 'string', 'legend_Organisation': 'string', 'legend_Individual': 'string', 'legend_Observations': 'string'}
    
    try:
        nodes_df = nodes_df.astype(node_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Node' sheet: {e}")
        return None

    try:
        connections_df = connections_df.astype(connections_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Connections' sheet: {e}")
        return None

    try:
        node_com_df = node_com_df.astype(node_com_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Nodes' sheet: {e}")
        return None

    try:
        edge_df = edge_df.astype(edge_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Edge' sheet: {e}")
        return None

    try:
        global_df = global_df.astype(global_datatypes)
    except ValueError as e:
        st.error(f"Invalid datatypes in 'Global' sheet: {e}")
        return None
  

    # Logical validation rules
    # Rule 1: Node ID should be distinct in Node sheet
    if not nodes_df['Node Id'].is_unique:
        st.error("Duplicate Node IDs found in Node sheet.")
        return None

    # Rule 2: Node Id should exist in Node sheet for all the ids present in 'From' and 'To' of Connections sheet
    connection_node_ids = set(connections_df['from'].tolist() + connections_df['to'].tolist())
    if not set(nodes_df['Node Id']).issuperset(connection_node_ids):
        st.error("Node IDs in Connections not found in Node.")
        return None

    # Rule 3: Level in Connections should be present in the L2 column of Edge
    # sheet in relationshipmapfeatures excel file
    edge_default_sheet = pd.read_excel(xls_RM, 'Edge')
    if not connections_df['Level'].isin(edge_default_sheet['L2']).all():
        st.error("Level in Sample Format - Connections should be present in the L2 column of Edge - Default sheet.")
        return None


    # Rule 4: In Connections for all values in 'From' column, there should be a value in 'To' column
    missing_to_values = connections_df[connections_df['from'].isin(nodes_df['Node Id']) & connections_df['to'].isna()]
    if not missing_to_values.empty:
        st.error("In Sample Format - Connections, missing 'To' values for some 'From' values.")
        return None

    # If all logical validations pass, return the validated dataframes
    return nodes_df, connections_df, node_com_df, edge_df, global_df


# function to validate and upload excel sheet and generate JSON output 
def code(project):
    st.title("Excel Validation App")

    uploaded_file_AM = st.file_uploader("Upload Association Map Excel File", type=["xlsx", "xls"])
    all_filled = False

    if uploaded_file_AM is not None:

        choice1 = st.selectbox('Default/Upload excelfile/fill through UI', [''] + ['Default', 'Upload excelfile', 'Fill from UI'])  
        if choice1 == 'Default':
            uploaded_file_RM = 'Relationshipmap Features Template.xlsx'
            all_filled = True
            xls_AM = pd.ExcelFile(uploaded_file_AM)
            nodes_df = pd.read_excel(xls_AM, "Node")
            distinct_values = nodes_df['SubType'].unique().tolist()
        elif choice1 == 'Upload excelfile':
            uploaded_file_RM = st.file_uploader("Upload Relationshipmap Features Excel file", type=["xlsx", "xls"])
            if uploaded_file_RM is not None:
                all_filled = True
                xls_AM = pd.ExcelFile(uploaded_file_AM)
                nodes_df = pd.read_excel(xls_AM, "Node")
                distinct_values = nodes_df['SubType'].unique().tolist()
        elif choice1 == 'Fill from UI':
            uploaded_file_RM = 'Relationshipmap Features Template.xlsx'  
            dict1 = {'White Hexagon': 'https://association-map-cdn-public.s3.us-west-1.amazonaws.com/DragnetAlpha/AssociationMap/Stories2.png', 'Pink Hexagon': 'https://association-map-cdn-public.s3-us-west-1.amazonaws.com/DragnetAlpha/AssociationMap/Stories1.png', 'Blue Hexagon':'https://association-map-cdn-public.s3.us-west-1.amazonaws.com/DragnetAlpha/AssociationMap/Target+Entity+1.png', 'Sky Blue Circle':'https://association-map-cdn-public.s3-us-west-1.amazonaws.com/DragnetAlpha/AssociationMap/Entity.png', 'Violet Hexagon': 'https://association-map-cdn-public.s3.us-west-1.amazonaws.com/DragnetAlpha/AssociationMap/Target+Entity+3.png'}
            xls_AM = pd.ExcelFile(uploaded_file_AM)
            nodes_df = pd.read_excel(xls_AM, "Node")
            distinct_values = nodes_df['SubType'].unique().tolist()
            d = {}
            distinct_values2 = nodes_df['SubType'].unique().tolist()
            original_options = ['White Hexagon', 'Pink Hexagon', 'Blue Hexagon', 'Sky Blue Circle', 'Violet Hexagon']
            options_len = original_options.copy()

            lsize = len(distinct_values)

            for i in range(lsize): 
                distinct_values2[i] = st.selectbox(distinct_values[i], [''] + options_len if distinct_values2[i] else [])
                d[distinct_values[i]] = distinct_values2[i]
            
            all_filled = all(value for value in d.values())

    
   



    if uploaded_file_AM is not None and all_filled:
        st.markdown("### Validating Excel File...")
        if choice1 == 'Fill from UI':
            validated_data = validate_excel(uploaded_file_AM, uploaded_file_RM)
        else:
            validated_data = validate_excel1(uploaded_file_AM, uploaded_file_RM)

        if validated_data is not None:
            st.success("Validation successful!")

            st.write("Nodes DataFrame:")
            st.write(validated_data[0])

            st.write("Connections DataFrame:")
            st.write(validated_data[1])

            st.write("Nodes DataFrame:")
            st.write(validated_data[2])

            st.write("Edge DataFrame:")
            st.write(validated_data[3])

            st.write("Global DataFrame:")
            st.write(validated_data[4])
                
            node_df = pd.read_excel(uploaded_file_AM, 'Node')
            connection_df = pd.read_excel(uploaded_file_AM, 'Connections')
            map_feature = pd.read_excel(uploaded_file_RM, sheet_name=None)


            if choice1 == 'Fill from UI':
                node_processor = NodeProcessor(node_df, map_feature, connection_df, d, dict1)
                nodes = node_processor.process_node_data(node_df, map_feature, connection_df, d, dict1)
            else:
                node_processor = NodeProcessor1(node_df, map_feature, connection_df)
                nodes = node_processor.process_node_data(node_df, map_feature, connection_df)

            connection_processor = ConnectionProcessor(node_df, map_feature, connection_df)
            connections = connection_processor.process_connection_data()

        
            global_df_ = map_feature['Global']
            nodes_df_ = map_feature['Nodes']
            if choice1 == 'Fill from UI':
                legend_data = GlobalProcessor.process_global_data(dict1, distinct_values, d)
            else:
                legend_data = GlobalProcessor1.process_global_data(nodes_df_, distinct_values)

            
            nodes_data_ = nodes_df_.to_dict(orient='records')

            edges_df_ = map_feature['Edge']
            edges_data_ = edges_df_.to_dict(orient='records')

            json_generator = JsonGenerator(legend_data, global_df_['client_name'].values[0], global_df_['logo_url'].values[0], global_df_['sidebar_short_logo'].values[0], nodes, connections, nodes_df_, global_df_, map_feature, node_df)
            json_output = json_generator.create_json_output(legend_data, global_df_['client_name'].values[0], global_df_['logo_url'].values[0], global_df_['sidebar_short_logo'].values[0], nodes, connections, nodes_df_, global_df_, map_feature, node_df)

            json_output_str = json.dumps(json_output, indent=2)

            st.subheader("Generated JSON:")
            st.json(json_output)
            st.download_button(
                "Download JSON",
                json_output_str,  
                key="download_button",
                file_name="output.json" 
            )

            json_string = json.dumps(json_output)

            # inserting JSON into the database
            var = f"INSERT INTO json_store (AssociationMapJSON, AppName) VALUES ('{json_string}', '{project}')"
            run_query(var)
            


#function for downloading excel template
def download():
    st.title("Download the Template")
    button_text_AM = "Click to download Association Map Template"
    link_url_AM = "https://drive.google.com/uc?export=download&id=12AKAvrsJeD4gnAmQQFOFOYnfBPYNk-Yo"
    if st.button(button_text_AM):
        st.markdown(f"[{button_text_AM}]({link_url_AM})")

    button_text_RM = "Click to download Relationshipmap Features Template"
    link_url_RM = "https://drive.google.com/uc?export=download&id=14FQVcdH4zciEeodaSF88DTaTymeYPIAl"
    if st.button(button_text_RM):
        st.markdown(f"[{button_text_RM}]({link_url_RM})")

if not firebase_admin._apps:
    cred = credentials.Certificate('login-f7584-3a8c6c70f3a2.json')
    firebase_admin.initialize_app(cred)

st.set_page_config(page_title="Association Map", layout="wide")


# main function to create the UI of streamlit
def main():    
    st.title('Association Map Creator')
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'useremail' not in st.session_state:
        st.session_state.username = ''

    def f():
        try:
            user = auth.get_user_by_email(email)
            st.write('Login Successful')
            st.session_state.username = user.uid
            st.session_state.useremail = user.email

            st.session_state.signedout = True
            st.session_state.signout = True

        except:
            st.warning('Login Failed')
    
    def t():
        st.session_state.signout = False
        st.session_state.signedout = False
        st.session_state.username = ''

    if 'signedout' not in st.session_state:
        st.session_state.signedout = False
    if 'signout' not in st.session_state:
        st.session_state.signout = False

    if not st.session_state['signedout']:
        choice = st.selectbox('Login/Signup', ['Login', 'Sign Up'])  

        if choice == 'Login':
            email = st.text_input('Email Address')
            password = st.text_input('Password', type='password')

            st.button('Login', on_click = f)

        else:
            email = st.text_input('Email Address')
            password = st.text_input('Password', type='password')
            username = st.text_input('Enter your unique username')

            if st.button('Create my account'):
                user = auth.create_user(email=email, password=password, uid=username)

                st.success('Account created successfully!')
                st.markdown('Please Login using your email and password')

    if st.session_state.signout:
        st.text('Name'+": "+st.session_state.username)
        st.text('Email id'+": "+st.session_state.useremail)
        st.button('sign out', on_click=t)

        #selecting the project part
        st.title("Choose a project")
        projects = pd.read_excel('Project names.xlsx', "Project")
        selected_option = projects['Project Names'].unique().tolist()
        project = st.selectbox('Choose a project', [''] + selected_option)
        st.write(f"You selected: {project}")
        download()
        code(project)
        
if __name__ == "__main__":
    main()