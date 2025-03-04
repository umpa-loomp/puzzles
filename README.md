# Puzzle Project

## Задача

Скласти найбільший однорядний цифровий пазл.
Чи любите ви пазли? Давайте складемо з вами цифровий пазл, де елементами з'єднання будуть перші або останні ДВІ цифри. Для спрощення завдання будемо використовувати однорядний пазл, де його фрагменти можуть розміщуватись тільки слідуючи один за одним.

Наприклад, маємо такі рядки із числами:
608017, 248460, 962282, 994725, 177092

Рішення:

Аналізуючи кінцеві частини, можна скласти такий ланцюжок:
248460 & 608017 & 177092 -> 2484(60)80(17)7092

Таким чином найбільша послідовність і відповідь буде: 24846080177092

Текстовий файл має 142 фрагменти, що повинні складатися тільки із цифр! Визначте найбільшу (найдовшу) послідовність для цих фрагментів. Файл можна завантажити за посиланням.

Кожен фрагмент має бути використаний тільки 1 раз.

## Обмеження

Існують лише такі обмеження, які слід враховувати при виборі способу вирішення задачі:

### Обмеження #1

Будь-яка людина повинна мати можливість скористатися вашим методом.
Це означає, наприклад, якщо для вирішення завдання Ви використовували свою власну програму, то будь-яка інша людина повинна мати можливість її скомпілювати/запустити і т.д.; якщо Ви використовували сторонні програми/утиліти, то будь-яка людина повинна мати можливість їх також встановити та користуватися; також будь-яка людина може взяти файл із зовсім іншим набором фрагментів і отримати із них відповідну послідовність;

### Обмеження #2:

При вирішенні задачі не можна використовувати нелегальне програмне забезпечення (пропрієтарне ПЗ, яке зазнало злому, піратські копії ПЗ, тощо). Також якщо ви запозичили ідею рішення, ПЗ або вихідні джерела (або якусь їх частину) у друга/колеги/в інтернеті/де-завгодно, то згадайте джерело.

## About This Project

This project is a Puzzle Chain Finder application built with a Python/Flask backend and HTML/JavaScript frontend. It helps you find the longest possible chain of puzzle pieces where each piece connects to the next through matching numbers.

### Features

- Load and parse puzzle datasets from various files
- Find the longest possible chain of puzzles using optimized algorithms
- Visualize the chain and connections between puzzles
- Export chain results to JSON for sharing or further analysis
- Identify branch points where alternate paths could be taken
- Display statistics about datasets and chains

## How to Run the Application

### Using Docker (Recommended)

#### Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your system

#### Running the Application

**On Windows:**
Simply double-click the `start.bat` file or run:
start.bat

**On Linux/Mac:**
Make the start script executable and run it:
chmod +x start.sh start.sh

The application will be available at: http://localhost:5000

#### Stopping the Application

To stop the application:
docker-compose down

### Manual Installation (Alternative)

#### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- A web browser

#### Backend Setup

1. Navigate to the backend directory
2. Install the required packages:
   pip install -r requirements.txt

3. Start the Flask server:
   python src/main.py

#### Frontend Setup

The frontend is static HTML/JS and is served by the Flask application.

## Using the Application

1. **Load a Dataset**:

- The application will automatically load the `source.txt` file on startup
- Use the dropdown to select other predefined datasets
- Click "Load Dataset" to switch to a different dataset

2. **Find the Longest Chain**:

- Set the timeout value (in seconds) to limit the search time
- Click "Find Longest Chain" to begin the search
- The results will be displayed in the "Puzzle Chain" section

3. **Analyze the Chain**:

- View statistics about the chain length, coverage, and connections
- Click "Show Branch Points" to identify potential alternative paths
- Use "Export Chain" to save the current chain as a JSON file

4. **View All Puzzles**:

- The "All Puzzles" section shows all loaded puzzle pieces
- Statistics about the dataset are shown at the top

## Creating Your Own Puzzle Files

You can create your own puzzle files to solve with this application:

1. Create a text file with one puzzle per line
2. Each puzzle should be a 6-digit number
3. Place the file in the root directory or in `backend/data/`
4. Load it through the UI or add it to the datasets in `main.py`

## Algorithm Description

The application uses a depth-first search algorithm optimized for finding the longest path in a directed graph. In this case:

1. Each puzzle piece becomes a node in the graph
2. Connections between pieces (where the "gives" of one piece matches the "takes" of another) become directed edges
3. The algorithm tries various starting points and traverses the graph to find the longest possible chain
4. Branch points are identified where multiple valid paths could be taken

The search is bounded by a configurable timeout to prevent excessive resource usage with large datasets.

## Folder Structure

puzzles/ ├── backend/ │ ├── data/ # Test datasets │ │ └── ... │ ├── exports/ # Exported chain files │ │ └── ... │ ├── requirements.txt # Python dependencies │ └── src/ # Backend Python code │ ├── main.py # Main Flask application │ ├── puzzle.py # Puzzle class definition │ └── ... ├── frontend/ │ ├── Dockerfile # Frontend Docker config │ └── public/ # Static frontend files │ ├── index.html # Main application UI │ └── ... ├── docker-compose.yml # Docker configuration ├── Dockerfile # Backend Docker config ├── README.md # This documentation ├── run_docker.sh # Script to run with Docker (Linux/Mac) ├── run-docker.bat # Script to run with Docker (Windows) ├── source.txt # Main puzzle dataset ├── start.bat # Easy start script (Windows) └── start.sh # Easy start script (Linux/Mac)

## Docker Configuration

The project uses Docker for easy deployment and includes the following configuration:

```yaml
version: '3'

services:
  puzzle-finder:
    build: .
    ports:
      - "0.0.0.0:5000:5000" # Explicitly bind to all interfaces
    volumes:
      - ./backend/data:/app/data
      - ./frontend/public:/app/public # Mount frontend
      - ./exports:/app/exports
    environment:
      - TIMEOUT=3600
      - FLASK_RUN_HOST=0.0.0.0
      - FLASK_ENV=development # For better error messages
    restart: unless-stopped
```

This configuration ensures that:

The application is accessible on port 5000
Data files and exports are persisted
Frontend files are served correctly
The application restarts automatically if it crashes
License
This project is available for use under open-source terms.

Credits
Algorithm implementation based on depth-first search and optimization techniques for finding the longest path in a directed graph.