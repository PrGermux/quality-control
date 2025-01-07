# Quality Control

This Python project is a comprehensive data analysis and visualization tool built with Python, leveraging PyQt5 for the graphical user interface and Matplotlib for data plotting. The application is specifically designed to manage, aggregate, and visualize production data from various machines, offering both tabular and graphical representations of the data.

### Key Features:
- **Multi-Tabi Interface**: The application has multiple tabs for different views of data analysis.
- **Data Aggregation and Filtering**: It supports filtering data by various parameters and aggregating the metrics from different machines.
- **Dynamic Plotting**: Utilizes Matplotlib to create dynamic, interactive plots with annotations showing the statistical metrics of the data.
- **Customizable Plots**: The plot customization includes setting colors, grid configurations, and dynamic legends for clarity and better user understanding.
- **Data Integration**: Combines data from CSV, DAT files, and directly from programmable logic controller (PLC) Database via SQL, ensuring comprehensive analysis across different data sources.

### Usage
This tool is highly useful for quality control managers, data analysts, and engineers who need to monitor, analyze, and report on machine performance and production efficiency. By providing both numerical summaries and graphical visualizations, the application helps in identifying trends, inefficiencies, and areas for improvement in production processes.

### Python Branch and Complexity
- **Python Branch**: This project utilizes several advanced Python libraries, including PyQt5 for GUI development, Pandas for data manipulation, and Matplotlib for plotting. These libraries indicate a high-level proficiency in Python, especially in data analysis and visualization domains.
- **Complexity**: The project is moderately complex, involving GUI design, data processing, and dynamic plotting. The integration of multiple data sources and the need for interactive and annotated visualizations add to its complexity. The code demonstrates good practices in object-oriented programming and modular design.

### Code Structure
- **Main Interface**: The main GUI is structured using QTabWidget to separate different views.
- **Data Handling**: Data is read from multiple file formats, cleaned, and aggregated using Pandas.
- **Plotting**: Matplotlib is used extensively for creating detailed plots with annotations and custom legends.

### Future Enhancements
- **Real-Time Data Integration**: Incorporate real-time data fetching and updating mechanisms.
- **Enhanced Customization**: Allow users to customize plots and reports further through the GUI.
- **Additional Data Sources**: Extend support for other data formats and sources, such as databases or APIs.

This repository is a valuable resource for professionals in manufacturing and production environments, providing powerful tools for data-driven decision-making and operational efficiency improvements.

### Screenshots:

![grafik](https://github.com/user-attachments/assets/f9bda81d-a10b-42f5-aa1c-39b0b11c351d)
![grafik](https://github.com/user-attachments/assets/c29b55b1-ba7b-48af-8ba4-f2d538fd98f5)
![grafik](https://github.com/user-attachments/assets/cd9e9f90-e99c-4829-adbf-79e4fee7bf05)

## Installation
1. Clone the repository:
```sh
git clone https://github.com/PrGermux/quality-control.git
cd quality-control
```
2. Install the required packages:
```sh
pip install -r requirements.txt
```

## Usage
**WARNING:** This program works only with specific data files. The user must adjust each tab to his/her needs with respect to the structure of the input file.

Run the main application:
```sh
python main.py
```

## Freezing
Run the code in a command line:
```sh
pyinstaller --onefile --windowed --icon=icon.png --add-data "icon.png;." --hidden-import=scipy.special._cdflib --name "Quality Control" main.py
```

## Dependencies
- Python 3.x
- PyQt5
- Pandas
- Matplotlib

## License
This project is licensed under the MIT License for non-commercial use.


