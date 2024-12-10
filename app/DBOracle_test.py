import os
from dotenv import load_dotenv
from utils import DBOracle  # Adjust import path as needed

def test_dboracle():
    # Load environment variables
    load_dotenv()

    # Get database credentials from environment
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_DSN = "UATGVPDB.ITRANS.INT/GVPUAT2"
    # print(DB_DSN)
     

    # Validate credentials
    if not all([DB_USER, DB_PASSWORD, DB_DSN]):
        print("Error: Missing database credentials")
        return

    # Initialize DBOracle
    db = DBOracle(DB_USER, DB_PASSWORD, DB_DSN)

    # Test database connection
    print("\n--- Testing Database Connection ---")
    connection = db.get_connection()
    if connection:
        print("✓ Database connection successful")
        connection.close()
    else:
        print("✗ Database connection failed")
        return

    # # Test template fetching
    # templates = db.fetch_templates()
    # print(templates)

    # Test logging
    print("\n--- Testing Log Entry ---")
    log_result = db.log_entry(
        event="Test Log",
        model="Test Model",
        input_message="Test input message",
        output_message="Test output message",
        input_tokens=100,
        output_tokens=50,
        duration=2.2,
        user_id=1,
        custom_prompt = "test prompt",
        session_id= 1
    )
    print("✓ Log entry result:", "Success" if log_result else "Failed")


    feedback_logged = db.log_feedback(  
        user_id = 1,
        user_feedback="The summary quality exceeded my expectations.",
        user_rating=5,
        session_id= 1
    )

    if feedback_logged:
        print("Feedback logged successfully!")
    else:
        print("Failed to log feedback.")




    # # # template_names = [template["NAME"] for template in templates]
    # template_names = [template['name'] for template in templates]
    # print(template_names)


    # selected_template = next((template for template in templates if template["name"] == 'Sales'), None)
    # if selected_template:
    #     prompt = selected_template["prompt"]
    #     print(prompt)
    # else:
    #     print("Template not found.")

if __name__ == "__main__":
    test_dboracle()