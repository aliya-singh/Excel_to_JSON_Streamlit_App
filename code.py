import streamlit as st
import pandas as pd
import replicate

# Streamlit app title
st.set_page_config(page_title="LLaMA 2 Chatbot")

# Get API token from user
replicate_api_token = st.text_input("Enter your Replicate API token:", type="password")

# Check if API token is provided
if replicate_api_token:
    try:
        # Initialize Replicate client
        client = replicate.Client(api_token=replicate_api_token)

        # Load the Excel file
        data = pd.read_excel("LLM_data.xlsx")

        # Function to generate a response from the model
        def generate_response(prompt):
            model = client.models.get("decaphr-research/llama-2-7b")
            output = model.predict(prompt=prompt, context=data.to_string())
            return output

        # Chatbot interface
        user_input = st.text_area("Ask a question:")
        if st.button("Submit"):
            prompt = f"Based on the following data:\n\n{data.to_string()}\n\nQuestion: {user_input}\nAnswer:"
            response = generate_response(prompt)
            st.write(response)

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.warning("Please enter your Replicate API token to use the chatbot.")