# Roman Urdu Streamlit App

This project is a simple Streamlit application that allows users to input Urdu text and generates its Roman Urdu equivalent. The application is designed to provide an easy-to-use interface for transliterating Urdu text into Roman Urdu.

## Project Structure

```
roman-urdu-streamlit-app
├── src
│   ├── app.py
│   └── utils
│       └── romanizer.py
├── requirements.txt
└── README.md
```

## Setup Instructions

To set up and run the application, follow these steps:

1. **Navigate to the project directory:**
   ```bash
   cd roman-urdu-streamlit-app
   ```

2. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit app:**
   ```bash
   streamlit run src/app.py
   ```

## Usage

Once the application is running, you will be able to input Urdu text into the provided text box. After submitting the text, the application will display the Roman Urdu equivalent.

## Dependencies

This project requires the following Python packages:

- Streamlit
- Any additional libraries required for Urdu to Roman Urdu conversion (to be specified in `requirements.txt`).