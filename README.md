## Title
Academic Insights & Research Progression

## Purpose

Using the help of this Dash application, users may examine and contrast various colleges and their focus areas using a comprehensive database of the Academic World and a series of interactive widgets. This application's target users include academic institutions, researchers, and other stakeholders who are interested in academic productivity, different universities' research interests, and publications from these institutions.

This application's main goal is to provide users with an interactive interface that exposes a wide variety of academic output, allowing them to explore and get insights into the research landscape of universities. Users can also add newly published articles and adjust university rankings when they change with this program. A thorough and comprehensive picture of the academic world is provided by the application's widgets, each of which has a distinct function.

## Video Demo

Watch a demo of the dashboard below:

https://mediaspace.illinois.edu/media/t/1_cbmtpij7

## Installation

Assuming you have already installed MySQL, MongoDB, and Neo4j DBMSs and have already created the `academicworld` database and populated it, you'll need to run some additional commands for the MySQL and MongoDB databases.

### MySQL

Run the following MySQL commands to set up the `academicworld` database for the Dash application:

```sql
USE academicworld;
    
-- Add new column `publication_count` to `faculty` table
ALTER TABLE faculty
ADD COLUMN publication_count INT DEFAULT 0;

-- Update the `publication_count` column 
-- with the number of publications for each faculty
UPDATE faculty f
LEFT JOIN (
  SELECT faculty_id, COUNT(DISTINCT publication_id) AS cnt 
  FROM faculty_publication 
  GROUP BY faculty_id
) fp ON fp.faculty_id = f.id
SET publication_count = cnt;

-- Create TRIGGER to update the `publication_count` column 
-- when a new publication is added for the faculty
CREATE TRIGGER tg_update_pub_count 
AFTER INSERT ON faculty_publication 
FOR EACH ROW
UPDATE faculty 
SET publication_count = publication_count + 1 
WHERE id = NEW.faculty_id;

-- Add new column `created_at` to `publication` table
-- to keep track of the creation time of each new publication
ALTER TABLE publication 
ADD COLUMN created_at TIMESTAMP;

-- Add new column `university_rank` to `university` table
-- each university is ranked based on the citations per faculty metric
ALTER TABLE university 
ADD COLUMN university_rank INT;
```

### MongoDB

Create the following indexes using the mongo shell to speed up the queries for the _Keywords Trends Over Time_ widget:

```bash
use academicworld
db.publications.createIndex({"keywords.name": 1});
db.publications.createIndex({"year": 1});
```

### Neo4j

As previously mentioned, we assume that the Neo4j database has been set up and populated with the `academicworld` data. No additional setup or configuration is required for Neo4j in this application.

___

## Usage

1. Clone the project files from the GitHub repository to your local machine using the following command:

```bash
git clone https://github.com/CS411DSO-SP24/Srishti_Sruthi.git
```

2. Set up a new virtual environment to manage dependencies for the project.

**Linux and macOS:**

```bash
python3 -m venv awd_venv
source awd_venv/bin/activate
```

**Windows:**

```bash
python -m venv awd_venv
awd_venv\Scripts\activate
```

3. Install all necessary dependencies using the following command:

```bash
pip install -r requirements.txt
```

4. Edit the _mysql_config.py_, _neo4j_config.py_, and _mongodb_config.py_ files with your database credentials, including username, password, database name, and hostnames.


5. Run the application using the following command:

```bash
python app.py
```

6. Once the application is running, open your web browser and navigate to http://127.0.0.1:8050/ to view the application interface and explore the Academic World.

___

### Design

The main components and their corresponding files in the project structure are as follows:

The main components and their corresponding files in the project structure are as follows:

- **Configuration** (_config_ folder):

  - `mongodb_config.py`: Contains MongoDB connection settings
  - `neo4j_config.py`: Contains Neo4j connection settings
  - `mysql_config.py`: Contains MySQL connection settings

The configuration files store the necessary credentials and connection settings for the respective databases.

- **Data Retrieval** (_services_ folder):

  - `mongodb_service.py`: Handles data retrieval from MongoDB
  - `neo4j_service.py`: Handles data retrieval from Neo4j
  - `mysql_service.py`: Handles data retrieval from MySQL
  
These customized Python scripts handle the data extraction process for each database type, ensuring seamless integration.

- **Data Processing and Visualization** (_components_ folder):

  - `collaboration_viewer.py`: Implements the _Faculty Publication Collaboration Viewer_ widget
  - `keyword_trends.py`: Implements the _Keyword Trends Over Time_ widget
  - `new_publications.py`: Implements the _Enter New Publications_ widget
  - `top_keywords.py`: Implements the _Top Keywords in Different Universities_ widget
  - `university_rankings.py`: Implements the _University Rankings based on Citations per Faculty_ widget
  - `yearly_rankings.py`: Implements the _Yearly Ranking: Top 10 Universities by Faculty and Publications_ widget

Each Python script in the components folder processes the retrieved data, formats it for visualization, and creates the respective widget using the Dash Plotly library.

- **Datasets** (_data_ folder):

  - `2023 QS World University Rankings V2.1 (For qs.com)`
  - `2022_QS_World_University_Rankings_Results_public_version.xlsx`
 
Users can upload these Excel files via the _University Rankings based on Citations per Faculty_ widget to update the rankings data in the Dash application.
 
- **Static Resources** (_static_ folder):

  - `custom_theme.css`: Contains custom styling for the application
  - `no_image_available.png`: Placeholder image for unavailable faculty portrait photos

The _static_ folder houses files such as stylesheets and images that support the application's appearance and functionality.

- **Web Interface**: The application is served as a web-based interface, making it accessible through a web browser; this enables users to interact with the widgets and explore the academic data without requiring any additional software installation.

## Implementation

This Dash application leverages various robust tools, libraries, and frameworks to create an interactive and responsive data visualization platform. Key components of the implementation include:

- **Python**: The application is built using Python, a versatile and widely-used programming language that offers extensive support for data processing, analysis, and visualization.


- **Dash**: Dash is a Python framework for building analytical web applications. It provides a flexible and efficient way to create interactive and responsive widgets, making it the backbone of the application's user interface. Specific Dash modules used in the _components_ include:

  - `dash.dcc`: For core components like dropdowns, sliders, and graphs
  - `dash.html`: For HTML components to structure the layout
  - `dash_bootstrap_components`: For incorporating [Bootstrap components] enabling a responsive design


- **Plotly**: The Plotly library creates interactive and visually appealing charts and graphs. It offers a wide range of chart types and customization options, enabling the visualization of complex data relationships. Specific Plotly modules used in the components include:

  - `plotly.express`: For creating high-level, expressive visualizations
  - `plotly.graph_objects`: For creating more fine-grained, customizable visualizations


- **Data Processing and Analysis Libraries**:

  - `pandas`: Used for data manipulation and analysis. The `pd` alias is commonly used for importing this library.
  - `sqlalchemy`: Used to interact with the MySQL database through its `create_engine`, `text` and `exc` modules.

- **Database Connectors**: The application retrieves data from three different databases: MongoDB, Neo4j, and MySQL. 

    - `pymongo`: For connecting  MongoDB
    - `neo4j`: For connecting  Neo4j
    - `mysql-connector-python`: For connecting  MySQL

- **Virtual Environment**: A virtual environment (`awd_venv`) is used to manage dependencies and isolate the application's environment; this ensures compatibility and stability across different development and deployment settings.

- ## Database Techniques

This Dash application implements several database techniques to enhance performance, maintain data integrity, and ensure smooth operation. The following techniques have been employed in the application:

- **DEFAULT constraint**: A `DEFAULT` constraint is applied to the `publication_count` column in the `faculty` table. When a new faculty record is inserted, this constraint ensures that the `publication_count` is automatically set to `0`, reflecting that the faculty member has not yet published any papers.

- **TRIGGER**: A `TRIGGER` automatically updates the `publication_count` column for a faculty member when a new publication is added to the database; this ensures that the publication count remains accurate and up-to-date without requiring manual intervention.

- **TRANSACTION**: The application employs database transactions in its Python code to manage the execution of a series of database operations. Transactions are used to guarantee data consistency and integrity by committing via `trans.commit()` or rolling back via `trans.rollback()` operations as a single unit.

- **INDEX**: An index is created in the MongoDB database to improve query performance for the Publications collection. The index is built on the `keywords.name` and `year` fields of the `publications` collection, enabling faster and more efficient searches for publications based on these criteria.

- ## Extra-Credit Capabilities

We have introduced a unique feature called the **Upload Rankings Data** tab to make the Dashboard more interactive. This enhancement improves the overall user experience and adds an exclusive functionality that allows you to easily update university ranking information by uploading a specific Excel file.

The **Upload Rankings Data** tab is equipped with an Upload File widget, which is designed to accept the `2023 QS World University Rankings V2.1 (For qs.com).xlsx` file. This file contains the latest university rankings data based on citations per faculty metric in the `cpf_rank` column, which is used to update the `university_rank` column in the `university` table in the MySQL `academicworld` database.

Initially, the `university_rank` column does not contain any values. Upon uploading the `2023 QS World University Rankings V2.1 (For qs.com).xlsx` file, the `handle_file_upload` function is triggered to process the file and update the ranking information. This function is specifically designed to work with the previously mentioned Excel file and will not be compatible with other files or formats.

In specific, the `handle_file_upload` function performs the following tasks:

1. Decodes the contents of the uploaded file.
2. Reads the XLSX file and filters the necessary columns.
3. Processes the data according to the specific structure of the `2023 QS World University Rankings V2.1 (For qs.com).xlsx` file.
4. Updates the `university_rank` column in the `university` table using the uploaded file's ranking data from the `cpf_rank` column.

we have made it more engaging, interactive, and practical for users who wish to update the university ranking information easily.

## Contributions

The development of this Dash application was a collaborative effort of a team of 2 members. Each team member contributed in various ways to the application's development, testing, and documentation.

### Team Members and Tasks

**Srishti Sharma**:

  - Developed widgets: University Rankings, New Publications, Collaboration Viewer, Yearly Rankings, Top Keywords, and Keyword Trends.
  - Mentored on Python-related questions.
  - Created CSS stylesheets and applied inline styles to various bootstrap components.
  - Implemented database changes.
  - Conducted peer review, testing, and quality assurance.

**Sruthi Jaganathan**:

- Added comments to the code for readability.
- Created CSS stylesheets
- Contributed to the documentation
- Conducted peer review, testing, and quality assurance.
- Created the video demo.

### Time Spent

Each team member spent approximately 40 hours on the overall project. The team discussed and brainstormed ideas to implement various widgets and finally decided on the above mentioned six widgets. Throughout the project, both team members contributed to refining the functionality of the Dashboard, ensuring a high-quality user experience.
