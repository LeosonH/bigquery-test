import streamlit as st
from openai import OpenAI
from google.cloud import bigquery
from google.oauth2 import service_account

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-3.5 model to query a BigQuery database using natural language. "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("Get me the first 10 rows of the table."):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate a response using the OpenAI API.
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": f"You are a BigQuery SQL generator. Based on the table schema, respond only with the SQL query needed \
                      to answer the user's question. It includes the following columns:\
                         order_id, customer_id, order_date, product_category, product_name, quantity, unit_price, order_status, country. The name of table is \
                      monica-test-466516.ecommerce.orders."}] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        # Stream the response to the chat using `st.write_stream`, then store it in 
        # session state.
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )

        bigquery_client = bigquery.Client(credentials=credentials)

        QUERY = "SELECT * FROM `monica-test-466516.ecommerce.orders` LIMIT 10"

        Query_Results = bigquery_client.query(QUERY)
        data = Query_Results.to_dataframe()

        st.dataframe(data, use_container_width=True)
