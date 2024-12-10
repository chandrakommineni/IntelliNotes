import os
from dotenv import load_dotenv
import tiktoken
import oracledb
import logging
import datetime
import traceback

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class DBOracle:
    def __init__(self, user: str, password: str, dsn: str):
        self.user = user
        self.password = password
        self.dsn = dsn
        self.logger = logging.getLogger(__name__)

    def get_connection(self):
        """Establishes and returns a connection to the Oracle database."""
        try:
            connection = oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)
            self.logger.info("Successfully connected to the database.")
            return connection
        except oracledb.DatabaseError as e:
            self.logger.error("Database connection error", exc_info=True)
            traceback.print_exc()
            logging.error(e, exc_info=True)
            return None
        
    def log_entry(self, event, model, input_message, output_message=None, 
              input_tokens=None, output_tokens=None, duration=None, 
              error_message=None, user_id=None, session_id=None, 
              user_rating=None, user_feedback=None, created_date=None, 
              custom_prompt=None):
        """
        Logs an event into the INTELLINOTES_LOG table with CLOB support.
        """
        connection = self.get_connection()
        if not connection:
            self.logger.error("Failed to log event: Database connection error.")
            return False
        
        try:
            with connection.cursor() as cursor:
                # Prepare CLOB for input_message
                input_clob = connection.createlob(oracledb.DB_TYPE_CLOB)
                if input_message:
                    input_clob.write(input_message)

                # Prepare CLOB for output_message
                output_clob = connection.createlob(oracledb.DB_TYPE_CLOB)
                if output_message:
                    output_clob.write(output_message)

                # Prepare CLOB for custom_prompt
                custom_prompt_clob = connection.createlob(oracledb.DB_TYPE_CLOB)
                if custom_prompt:
                    custom_prompt_clob.write(custom_prompt)

                # Execute the INSERT statement
                cursor.execute("""
                    INSERT INTO INTELLINOTES_LOG (
                        LOGID, EVENT, MODEL, INPUT_MESSAGE, OUTPUT_MESSAGE,
                        INPUT_TOKENS, OUTPUT_TOKENS, DURATION, ERRORMESSAGE,
                        USERID, SESSIONID, USER_RATING, USER_FEEDBACK, CREATEDATE, CUSTOM_PROMPT
                    ) VALUES (
                        SQ_INTELLINOTES_LOG.NEXTVAL, :event, :model, :input_message, :output_message,
                        :input_tokens, :output_tokens, :duration, :error_message,
                        :user_id, :session_id, :user_rating, :user_feedback, :created_date, :custom_prompt
                    )
                """, {
                    "event": event,
                    "model": model,
                    "input_message": input_clob if input_message else None,
                    "output_message": output_clob if output_message else None,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "duration": duration,
                    "error_message": error_message,
                    "user_id": user_id,
                    "session_id": session_id,
                    "user_rating": user_rating,
                    "user_feedback": user_feedback,
                    "created_date": created_date or datetime.datetime.now(),
                    "custom_prompt": custom_prompt_clob if custom_prompt else None
                })

                connection.commit()
                self.logger.info(f"Logged entry: {event} with model {model}.")
                return True
        except Exception as e:
            self.logger.error("Failed to log entry", exc_info=True)
            return False
        finally:
            connection.close()

    def log_feedback(self, user_id: int, session_id: int, 
                 user_feedback: str, user_rating: int, created_date=None):
        """
        Logs feedback into the IntelliNotes_Feedback table.

        Args:
            feedback_id (int): The unique feedback ID associated with the feedback entry.
            user_id (int): The ID of the user providing feedback.
            session_id (int): The session ID associated with the feedback entry.
            user_feedback (str): The feedback provided by the user.
            user_rating (int): The rating given by the user (1 to 5).
            created_date (datetime, optional): The date the feedback was created. Defaults to the current datetime.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        connection = self.get_connection()
        if not connection:
            self.logger.error("Failed to log feedback: Database connection error.")
            return False

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO IntelliNotes_Feedback (
                        FEEDBACKID, USERID, SESSIONID, USER_FEEDBACK, USER_RATING, CREATED_DATE
                    ) VALUES (
                        SQ_INTELLINOTES_FEEDBACK.NEXTVAL, :user_id, :session_id, :user_feedback, :user_rating, :created_date
                    )
                """, {
                    "user_id": user_id,
                    "session_id": session_id,
                    "user_feedback": user_feedback,
                    "user_rating": user_rating,
                    "created_date": created_date or datetime.datetime.now(),
                })

                connection.commit()
                self.logger.info(f"Feedback logged successfully for SessionID: {session_id}, UserID: {user_id}.")
                return True
        except Exception as e:
            self.logger.error("Failed to log feedback", exc_info=True)
            return False
        finally:
            connection.close()


    def fetch_templates(self):
        """
        Fetches unique template details where IS_CUSTOM is 0.
        
        Returns:
            list: A list of dictionaries with template details
        """
        connection = self.get_connection()
        if not connection:
            self.logger.error("Failed to fetch templates: Database connection error.")
            return []

        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT NAME, ICON, DESCRIPTION, PROMPT 
                FROM INTELLINOTES_PROMPTS
                ORDER BY NAME
            """)
            
            # Fetch all unique templates
            templates = [
                {
                    "name": row[0],
                    "icon": row[1], 
                    "description": row[2],
                    "prompt": row[3].read() if row[3] is not None else None
                } for row in cursor.fetchall()
            ]
            
            if templates:
                self.logger.info(f"Fetched {len(templates)} unique templates.")
            else:
                self.logger.warning("No unique templates found.")
            
            return templates
        
        except Exception as e:
            self.logger.error("Failed to fetch unique templates", exc_info=True)
            return []
        finally:
            connection.close()



def load_env_variables():
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise EnvironmentError("Google API Key not found in .env file.")
    return google_api_key


def log_tokens(input_text: str, output_text: str, encoding_name: str = "cl100k_base"):
    """
    Calculates token counts for input and output texts.

    Args:
        input_text (str): Input text.
        output_text (str): Output text.
        encoding_name (str): Name of the encoding to use. Default is 'cl100k_base'.

    Returns:
        tuple: A tuple containing the number of input and output tokens.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    input_tokens = len(encoding.encode(input_text))
    output_tokens = len(encoding.encode(output_text))
    return input_tokens, output_tokens
