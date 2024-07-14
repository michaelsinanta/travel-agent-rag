# Travel Agent Chatbot

This project is part of the pre-employment test for Bahasa.ai Product Engineer AI Backend.

## Installation

Follow these steps to set up the project:

1. Clone the repository:
    ```sh
    git clone https://github.com/michaelsinanta/travel-agent-rag.git
    ```

2. Navigate to the project directory:
    ```sh
    cd travel-agent-rag
    ```

3. Create a virtual environment:
    ```sh
    python3 -m venv env
    ```

4. Activate the virtual environment:
    - On Windows:
      ```sh
      .\env\Scripts\activate
      ```
    - On macOS and Linux:
      ```sh
      source env/bin/activate
      ```

5. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

1. Create a `.env` file in the project root and add the following:
    ```sh
    TOGETHER_API_KEY=your_together_api_key
    DATABASE_URI=your_database_uri
    ```

## Usage

1. Run the application:
    ```sh
    streamlit run main.py
    ```
