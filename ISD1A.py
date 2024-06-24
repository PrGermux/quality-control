import mysql.connector
from mysql.connector import Error
#from sqlalchemy import create_engine
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QLineEdit, QSpacerItem
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mticker
from io import StringIO, BytesIO
import os
import pandas as pd
import numpy as np
from numpy import pi, sin, cos, sqrt, arctan
import matplotlib.pyplot as plt
from datetime import datetime
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader

# Database connection parameters
host = 'analyse-db'
database = 'isd1a'
user = 'qp'
password = 'Qptheva4862'

class ISD1A(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Button to initiate database connection
        self.connectButton = QPushButton("Connect to ISD1A Database")
        self.connectButton.clicked.connect(self.connectToDatabase)
        self.layout.addWidget(self.connectButton)

        self.statusLabel = QLabel("Click the button to connect to the database.")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.statusLabel)

        self.label = QLabel("Enter Time Filter Start and Stop from Grafana to proceed.")
        self.label.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.label)

        self.timeFieldStart = QLineEdit("")
        self.timeFieldStart.setPlaceholderText("Enter Time Filter Start (time unix)")
        self.timeFieldStart.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.timeFieldStart)

        self.timeFieldStop = QLineEdit("")
        self.timeFieldStop.setPlaceholderText("Enter Time Filter Stop (time unix)")
        self.timeFieldStop.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.timeFieldStop)

        self.info = QLabel("Enter additionally names of tape ends.")
        self.info.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.info)

        self.endLeft = QLineEdit("")
        self.endLeft.setPlaceholderText("Left")
        self.endLeft.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.endLeft)

        self.endRight = QLineEdit("")
        self.endRight.setPlaceholderText("Right")
        self.endRight.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.endRight)

        self.processButton = QPushButton("Plot")
        self.processButton.clicked.connect(self.processData)
        self.processButton.setVisible(False)
        self.processButton.setEnabled(False)  # Disabled until both files are loaded
        self.layout.addWidget(self.processButton)

        self.results = QLabel("")
        self.layout.addWidget(self.results)
        
        self.initialTextField = QLineEdit("")
        self.initialTextField.setPlaceholderText("Enter your initials")
        self.initialTextField.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.initialTextField)

        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.exportData)
        self.saveButton.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.saveButton)

        self.canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.ax1 = self.canvas.figure.add_subplot(311)
        self.ax2 = self.canvas.figure.add_subplot(312)
        self.ax3 = self.canvas.figure.add_subplot(313)

        plt.style.use('dark_background')
        self.canvas = FigureCanvas(Figure(figsize=(10, 10), facecolor='#434343'))
        self.layout.addWidget(self.canvas)
        self.ax1 = self.canvas.figure.add_subplot(311)
        self.ax2 = self.canvas.figure.add_subplot(312)
        self.ax3 = self.canvas.figure.add_subplot(313)
        self.ax1.set_facecolor('#434343')
        self.ax2.set_facecolor('#434343')
        self.ax3.set_facecolor('#434343')
        self.ax1.axis('off')
        self.ax2.axis('off')
        self.ax3.axis('off')

    def exportData(self):
        if self.export_df is not None:
            try:
                # Define the initial directory based on user's Documents folder
                initial_dir = os.path.join(os.path.expanduser('~'), 'Documents')

                # Prompt user to select directory for saving the files
                save_dir = QFileDialog.getExistingDirectory(self, "Select Directory to Save Files", initial_dir)
                if save_dir:
                    # Define file names based on DataFrame fields
                    base_name = f"{self.df_process['Prozessdaten_Band_ID'].iloc[0]}_{self.df_process['Prozessrezept'].iloc[0]}"
                    data_file_name = os.path.join(save_dir, f"{base_name}.dat")
                    pdf_file_name = os.path.join(save_dir, f"{base_name}.pdf")

                    # Save DataFrame to a .dat file
                    self.export_df.to_csv(data_file_name, sep=',', index=False)
                    QMessageBox.information(self, "Data Save Successful", f"Data saved to {data_file_name}")

                    # Generate and save a PDF report
                    self.exportPDF(pdf_file_name)
                    QMessageBox.information(self, "Report Generation Successful", f"PDF report saved to {pdf_file_name}")
                else:
                    # User cancelled the save operation
                    return

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save data:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "No data available to save. Please load and process data first.")

    def exportPDF(self, pdf_file_name, dpi=300):
        process_name = self.df_process['Prozessrezept'].iloc[0]
        tape_name = self.df_process['Prozessdaten_Band_ID'].iloc[0]
        sample_name = self.df_process['AktuelleProzess'].iloc[0]

        title_text = f"Process sheet {process_name}" 
        tape_text = f"Tape: {tape_name}"
        sample_text = f"Sample: {sample_name}"

        # Create a figure with subplots
        plt.style.use('default')
        fig = Figure(figsize=(8, 6), dpi=dpi)
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313)

        ax1.clear()
        ax1.plot(self.df_data['Bandposition'], self.df_data['Druck_Kammer_Messröhre_2'], label='Pressure', linestyle='-', color='black', linewidth=1)
        ax1.set_xlabel('Tape Position [m]')
        ax1.set_ylabel('Pressure [mbar]')
        ax1.set_xlim(0, 1000)
        ax1.set_ylim(2E-4, 1E-3)
        ax1.set_yscale('log')
        ax1.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)  # Grid for both major and minor x ticks
        ax1.grid(True, which='major', axis='y', linestyle='--', linewidth=0.5)  # Grid for only major y ticks
        ax1.set_xticks(np.arange(0, 1050, 100))
        ax1.set_xticks(np.arange(0, 1050, 50), minor=True)
        # Set major and minor ticks on the y-axis
        ax1.set_yticks(np.arange(2E-4, 1.1E-3, 1E-4))
        ax1.set_yticks(np.arange(2E-4, 1.05E-3, 0.25E-4), minor=True)
        # Custom formatter to display ticks in E-4 style
        def custom_formatter(x, pos):
            return f'{x:.0E}'.replace('E-0', 'E-')
        ax1.get_yaxis().set_major_formatter(mticker.FuncFormatter(custom_formatter))
        ax1.tick_params(axis='y', which='minor', labelleft=False)
        ax1.tick_params(axis='x', direction='in', which='both')  # Ticks inside for x-axis
        ax1.tick_params(axis='y', direction='in', which='both')  # Ticks inside for y-axis
        ax1.legend(loc='upper right')  # Add legend to the plot

        ax2.clear()
        ax2.plot(self.df_data['Bandposition'], self.df_data['Filmetrics_DB_C2_Layer1d'], label='Thickness', linestyle='-', color='black', linewidth=1)
        ax2.set_xlabel('Tape Position [m]')
        ax2.set_ylabel('Thickness [nm]')
        ax2.set_xlim(0, 1000)
        ax2.set_ylim(2400, 3600)
        ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax2.set_xticks(np.arange(0, 1050, 100))
        ax2.set_xticks(np.arange(0, 1050, 50), minor=True)
        ax2.set_yticks(np.arange(2400, 3650, 200))
        ax2.set_yticks(np.arange(2400, 3650, 100), minor=True)
        ax2.tick_params(axis='x', direction='in', which='both')  # Ticks inside for x-axis
        ax2.tick_params(axis='y', direction='in', which='both')  # Ticks inside for y-axis
        ax2.legend(loc='upper right')  # Add legend to the plot

        # Draw horizontal lines and fill between
        ax2.axhline(3300, color='green', linestyle='--')
        ax2.axhline(2700, color='green', linestyle='--')
        ax2.fill_between(self.df_data['Bandposition'], 3300, 2700, where=(self.df_data['Filmetrics_DB_C2_Layer1d'] >= 2700) & (self.df_data['Filmetrics_DB_C2_Layer1d'] <= 3300),
                                  color='green', alpha=0.25, hatch='//')
            
        ax3.clear()
        ax3.plot(self.df_data['Bandposition'], self.df_data['Optosurf_DB_Aq'], label='Roughness', linestyle='-', color='black', linewidth=1)
        ax3.set_xlabel('Tape Position [m]')
        ax3.set_ylabel('Roughness')
        ax3.set_xlim(0, 1000)
        ax3.set_ylim(3, 13)
        ax3.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)  # Grid for both major and minor x ticks
        ax3.grid(True, which='major', axis='y', linestyle='--', linewidth=0.5)  # Grid for only major y ticks
        ax3.set_xticks(np.arange(0, 1050, 100))
        ax3.set_xticks(np.arange(0, 1050, 50), minor=True) 
        ax3.set_yticks(np.arange(3, 13.5, 1))
        ax3.set_yticks(np.arange(3, 13.5, 0.5), minor=True)
        ax3.tick_params(axis='x', direction='in', which='both')  # Ticks inside for x-axis
        ax3.tick_params(axis='y', direction='in', which='both')  # Ticks inside for y-axis
        ax3.legend(loc='upper right')  # Add legend to the plot

                # Define the background box properties
        bbox_props = dict(boxstyle="round,pad=0.3", ec="black", fc="white", lw=1)

        # For the left label
        if self.endLeft.text():
            left_label = self.endLeft.text()  # Get text from QLineEdit
            y_pos_ax2 = ax2.get_ylim()[1]  # Get the upper y-limit of ax2
            y_pos_ax3 = ax3.get_ylim()[1]  # Get the upper y-limit of ax3

            # Add the text above the first data point on ax2 with background box
            ax2.text(self.df_data['Bandposition'].iloc[0], y_pos_ax2,
                          left_label, verticalalignment='top', horizontalalignment='left',
                          bbox=bbox_props, color='black')

            # Add the text above the first data point on ax3 with background box
            ax3.text(self.df_data['Bandposition'].iloc[0], y_pos_ax3,
                          left_label, verticalalignment='top', horizontalalignment='left',
                          bbox=bbox_props, color='black')

        # For the right label
        if self.endRight.text():
            right_label = self.endRight.text()  # Get text from QLineEdit
            y_pos_ax2 = ax2.get_ylim()[1]  # Get the upper y-limit of ax2
            y_pos_ax3 = ax3.get_ylim()[1]  # Get the upper y-limit of ax3

            # Add the text above the last data point on ax2 with background box
            ax2.text(self.df_data['Bandposition'].iloc[-1], y_pos_ax2,
                          right_label, verticalalignment='top', horizontalalignment='right',
                          bbox=bbox_props, color='black')

            # Add the text above the last data point on ax3 with background box
            ax3.text(self.df_data['Bandposition'].iloc[-1], y_pos_ax3,
                          right_label, verticalalignment='top', horizontalalignment='right',
                          bbox=bbox_props, color='black')

        # Save to buffer
        fig.tight_layout()
        buf = BytesIO()
        canvas = FigureCanvas(fig)
        canvas.draw()  # Draw the canvas to the buffer
        canvas.print_png(buf)
        buf.seek(0)

        # Create a PDF canvas
        c = pdfcanvas.Canvas(pdf_file_name, pagesize=A4)
        width, height = A4

        c.setFont("Helvetica", 20)
        c.drawCentredString(width/2, height - 100, title_text)  

        # Draw the plots
        img = ImageReader(buf)
        c.drawImage(img, 0, height - 550, width=600, height=400, preserveAspectRatio=True, mask='auto')  # Adjusted to fit the plot

        # Text to draw, properly formatted
        c.setFont("Helvetica", 12)

        c.drawString(50, height - 125, tape_text)
        c.drawString(50, height - 140, sample_text)

        c.drawString(50, height - 580, f'Pressure: ({self.pressure_avg*10000:.2f} ± {self.pressure_std*10000:.2f})E-4 mbar    [{self.pressure_min*10000:.2f}, {self.pressure_max*10000:.2f}]E-4 mbar')
        c.drawString(50, height - 595, f'Thickness: ({self.thickness_avg:.0f} ± {self.thickness_std:.0f}) nm    [{self.thickness_min:.0f}, {self.thickness_max:.0f}] nm')
        c.drawString(50, height - 610, f'Roughness: ({self.roughness_avg:.1f} ± {self.roughness_std:.1f})   [{self.roughness_min:.1f}, {self.roughness_max:.1f}]')

        # Get current date and time
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        initials = self.initialTextField.text()  # Fetch initials from the text field

        # Draw date, time, and initials in the top right corner
        c.drawRightString(width - 10, height - 20, f"Date: {current_date}")
        c.drawRightString(width - 10, height - 35, f"Time: {current_time}")
        c.drawRightString(width - 10, height - 50, f"Initials: {initials}")

        # Save the PDF
        c.showPage()
        c.save()

        #QMessageBox.information(self, "PDF Generated", f"Successfully generated the report at {pdf_file_name}")

    def connectToDatabase(self):
        try:
            # Establish connection to MySQL database
            connection = mysql.connector.connect(host=host, database=database, user=user, password=password)

            if connection.is_connected():
                db_info = connection.get_server_info()
                self.statusLabel.setText(f"Connection to DB ISD1A successful\nDatabase server version : {db_info}")
                connection.close()

        except Error as e:
            self.statusLabel.setText("Failed to connect to database")
            QMessageBox.critical(self, 'Database Connection Failed', f'Error: {e}', QMessageBox.Ok)

        self.label.setVisible(True)
        self.timeFieldStart.setVisible(True)
        self.timeFieldStop.setVisible(True)
        self.info.setVisible(True)
        self.endLeft.setVisible(True)
        self.endRight.setVisible(True)   
        self.processButton.setVisible(True)
        self.processButton.setEnabled(True) 

    def processData(self):
        plt.style.use('dark_background')
        try:
            # Establish connection to MySQL database
            connection = mysql.connector.connect(host=host, database=database, user=user, password=password)

            if connection.is_connected():
                db_info = connection.get_server_info()
                self.statusLabel.setText(f"Connection to DB ISD1A successful\nDatabase server version: {db_info}")
                connection.close()

        except Error as e:
            self.statusLabel.setText("Failed to connect to database")
            QMessageBox.critical(self, 'Database Connection Failed', f'Error: {e}', QMessageBox.Ok)

        start = self.timeFieldStart.text()
        stop = self.timeFieldStop.text()

        left = self.endLeft.text()
        right = self.endRight.text()

        if not start.isdigit() or not stop.isdigit():
            QMessageBox.critical(self, "Error", "Start and Stop times must be integer unix timestamps.")
            return
        
        try:
            connection = mysql.connector.connect(host=host, database=database, user=user, password=password)
            #engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{database}")
            if connection.is_connected():
                data = f"""
                SELECT 
                    isd1a_01.`Time_unix`, 
                    isd1a_01.`Bandposition`, 
                    isd1a_02.`Druck_Kammer_Messröhre_2`,
                    isd1a_02.`Filmetrics_DB_C2_Layer1d`, 
                    isd1a_04.`Optosurf_DB_Aq`
                FROM 
                    isd1a_01
                JOIN 
                    isd1a_02 ON isd1a_01.`Time_unix` = isd1a_02.`Time_unix`
                JOIN 
                    isd1a_04 ON isd1a_01.`Time_unix` = isd1a_04.`Time_unix`
                WHERE 
                    isd1a_01.`Time_unix` BETWEEN {start} AND {stop}
                ORDER BY 
                    isd1a_01.`Time_unix` ASC;
                """

                process = f"""
                SELECT
                    prozess.`Time_unix`,
                    prozess.`AktuelleProzess`,
                    prozess.`Prozessdaten_Band_ID`,
                    prozess.`Prozessdaten_Prozesslänge`,
                    prozess.`Prozessrezept`
                FROM 
                    prozess
                WHERE 
                    prozess.`Time_unix` BETWEEN {start} AND {stop}
                ORDER BY 
                    prozess.`Time_unix` DESC;
                """
                df_data = pd.read_sql(data, connection)
                df_process = pd.read_sql(process, connection)
                connection.close()

            df_data['Bandposition'] = df_data['Bandposition'] - 50 - 42 # -50 m forerun - 42 m winder

            tape_filter = df_process['Prozessdaten_Prozesslänge'].astype(float).iloc[0]
            process_filter = tape_filter + 50 + 42 # 50 m forerun + 42 m winder

            # Filter the DataFrame for pressure based on band position range
            df_data = df_data[(df_data['Bandposition'] >= 0) & (df_data['Bandposition'] < df_data['Bandposition'].iloc[-1] - 5)] # Last -5 m

            # Identify indices where changes in both metrics are minimal and 'Bandposition' is greater than zero
            constant_indices = df_data[(df_data['Bandposition'].diff().abs() < 0.01) & 
                                    (df_data['Optosurf_DB_Aq'].diff().abs() < 0.1) & 
                                    (df_data['Bandposition'] > 0)].index

            if not constant_indices.empty:
                # Find the first index where both 'Bandposition' and 'Optosurf_DB_Aq' do not change significantly
                first_constant_index = constant_indices[0]
                # Truncate the DataFrame up to the index just before the constant value starts
                df_data = df_data.loc[:first_constant_index - 1]

            # Set values to NaN where 'Optosurf_DB_Aq' is less than 2 or greater than 13
            df_data['Optosurf_DB_Aq'] = np.where(
                (df_data['Optosurf_DB_Aq'] <= 13) & (df_data['Optosurf_DB_Aq'] >= 2), 
                df_data['Optosurf_DB_Aq'], 
                np.nan
            )

            self.df_data = df_data
            self.df_process = df_process

            pressure_avg = df_data['Druck_Kammer_Messröhre_2'].mean()
            self.pressure_avg = pressure_avg

            pressure_std = df_data['Druck_Kammer_Messröhre_2'].std()
            self.pressure_std = pressure_std

            pressure_min = df_data['Druck_Kammer_Messröhre_2'].min()
            self.pressure_min = pressure_min

            pressure_max = df_data['Druck_Kammer_Messröhre_2'].max()
            self.pressure_max = pressure_max


            thickness_avg = df_data['Filmetrics_DB_C2_Layer1d'].mean()
            self.thickness_avg = thickness_avg

            thickness_std = df_data['Filmetrics_DB_C2_Layer1d'].std()
            self.thickness_std = thickness_std

            thickness_min = df_data['Filmetrics_DB_C2_Layer1d'].min()
            self.thickness_min = thickness_min

            thickness_max = df_data['Filmetrics_DB_C2_Layer1d'].max()
            self.thickness_max = thickness_max


            roughness_avg = df_data['Optosurf_DB_Aq'].mean()
            self.roughness_avg = roughness_avg

            roughness_std = df_data['Optosurf_DB_Aq'].std()
            self.roughness_std = roughness_std

            roughness_min = df_data['Optosurf_DB_Aq'].min()
            self.roughness_min = roughness_min

            roughness_max = df_data['Optosurf_DB_Aq'].max()
            self.roughness_max = roughness_max

            self.results.setText(
                f'Pressure: <b>({pressure_avg*10000:.2f} ± {pressure_std*10000:.2f})E-4 mbar</b> &nbsp; <b>[{pressure_min*10000:.2f}, {pressure_max*10000:.2f}]E-4 mbar</b><br>'
                f'Thickness: <b>({thickness_avg:.0f} ± {thickness_std:.0f}) nm</b> &nbsp; <b>[{thickness_min:.0f}, {thickness_max:.0f}] nm</b><br>'
                f'Roughness: <b>({roughness_avg:.1f} ± {roughness_std:.1f})</b> &nbsp; <b>[{roughness_min:.1f}, {roughness_max:.1f}]</b>'
                )

            self.ax1.clear()
            self.ax1.plot(df_data['Bandposition'], df_data['Druck_Kammer_Messröhre_2'], label='Pressure', linestyle='-', color='white', linewidth=1)
            self.ax1.set_xlabel('Tape Position [m]')
            self.ax1.set_ylabel('Pressure [mbar]')
            self.ax1.set_xlim(0, 1000)
            self.ax1.set_ylim(2E-4, 1E-3)
            self.ax1.set_yscale('log')
            self.ax1.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)  # Grid for both major and minor x ticks
            self.ax1.grid(True, which='major', axis='y', linestyle='--', linewidth=0.5)  # Grid for only major y ticks
            self.ax1.set_xticks(np.arange(0, 1050, 100))
            self.ax1.set_xticks(np.arange(0, 1050, 50), minor=True)
            # Set major and minor ticks on the y-axis
            self.ax1.set_yticks(np.arange(2E-4, 1.1E-3, 1E-4))
            self.ax1.set_yticks(np.arange(2E-4, 1.05E-3, 0.25E-4), minor=True)
            # Custom formatter to display ticks in E-4 style
            def custom_formatter(x, pos):
                return f'{x:.0E}'.replace('E-0', 'E-')
            self.ax1.get_yaxis().set_major_formatter(mticker.FuncFormatter(custom_formatter))
            self.ax1.tick_params(axis='y', which='minor', labelleft=False)
            self.ax1.tick_params(axis='x', direction='in', which='both')  # Ticks inside for x-axis
            self.ax1.tick_params(axis='y', direction='in', which='both')  # Ticks inside for y-axis
            self.ax1.legend(loc='upper right')  # Add legend to the plot

            self.ax2.clear()
            self.ax2.plot(df_data['Bandposition'], df_data['Filmetrics_DB_C2_Layer1d'], label='Thickness', linestyle='-', color='white', linewidth=1)
            self.ax2.set_xlabel('Tape Position [m]')
            self.ax2.set_ylabel('Thickness [nm]')
            self.ax2.set_xlim(0, 1000)
            self.ax2.set_ylim(2400, 3600)
            self.ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
            self.ax2.set_xticks(np.arange(0, 1050, 100))
            self.ax2.set_xticks(np.arange(0, 1050, 50), minor=True)
            self.ax2.set_yticks(np.arange(2400, 3650, 200))
            self.ax2.set_yticks(np.arange(2400, 3650, 100), minor=True)
            self.ax2.tick_params(axis='x', direction='in', which='both')  # Ticks inside for x-axis
            self.ax2.tick_params(axis='y', direction='in', which='both')  # Ticks inside for y-axis
            self.ax2.legend(loc='upper right')  # Add legend to the plot

            # Draw horizontal lines and fill between
            self.ax2.axhline(3300, color='green', linestyle='--')
            self.ax2.axhline(2700, color='green', linestyle='--')
            self.ax2.fill_between(df_data['Bandposition'], 3300, 2700, where=(df_data['Filmetrics_DB_C2_Layer1d'] >= 2700) & (df_data['Filmetrics_DB_C2_Layer1d'] <= 3300),
                                  color='green', alpha=0.25, hatch='//')
            
            self.ax3.clear()
            self.ax3.plot(df_data['Bandposition'], df_data['Optosurf_DB_Aq'], label='Roughness', linestyle='-', color='white', linewidth=1)
            self.ax3.set_xlabel('Tape Position [m]')
            self.ax3.set_ylabel('Roughness')
            self.ax3.set_xlim(0, 1000)
            self.ax3.set_ylim(3, 13)
            self.ax3.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)  # Grid for both major and minor x ticks
            self.ax3.grid(True, which='major', axis='y', linestyle='--', linewidth=0.5)  # Grid for only major y ticks
            self.ax3.set_xticks(np.arange(0, 1050, 100))
            self.ax3.set_xticks(np.arange(0, 1050, 50), minor=True) 
            self.ax3.set_yticks(np.arange(3, 13.5, 1))
            self.ax3.set_yticks(np.arange(3, 13.5, 0.5), minor=True)
            self.ax3.tick_params(axis='x', direction='in', which='both')  # Ticks inside for x-axis
            self.ax3.tick_params(axis='y', direction='in', which='both')  # Ticks inside for y-axis
            self.ax3.legend(loc='upper right')  # Add legend to the plot

            # Define the background box properties
            bbox_props = dict(boxstyle="round,pad=0.3", ec="black", fc="white", lw=1)

            # For the left label
            if self.endLeft.text():
                left_label = self.endLeft.text()  # Get text from QLineEdit
                y_pos_ax2 = self.ax2.get_ylim()[1]  # Get the upper y-limit of ax2
                y_pos_ax3 = self.ax3.get_ylim()[1]  # Get the upper y-limit of ax3

                # Add the text above the first data point on ax2 with background box
                self.ax2.text(self.df_data['Bandposition'].iloc[0], y_pos_ax2,
                            left_label, verticalalignment='top', horizontalalignment='left',
                            bbox=bbox_props, color='black')

                # Add the text above the first data point on ax3 with background box
                self.ax3.text(self.df_data['Bandposition'].iloc[0], y_pos_ax3,
                            left_label, verticalalignment='top', horizontalalignment='left',
                            bbox=bbox_props, color='black')

            # For the right label
            if self.endRight.text():
                right_label = self.endRight.text()  # Get text from QLineEdit
                y_pos_ax2 = self.ax2.get_ylim()[1]  # Get the upper y-limit of ax2
                y_pos_ax3 = self.ax3.get_ylim()[1]  # Get the upper y-limit of ax3

                # Add the text above the last data point on ax2 with background box
                self.ax2.text(self.df_data['Bandposition'].iloc[-1], y_pos_ax2,
                            right_label, verticalalignment='top', horizontalalignment='right',
                            bbox=bbox_props, color='black')

                # Add the text above the last data point on ax3 with background box
                self.ax3.text(self.df_data['Bandposition'].iloc[-1], y_pos_ax3,
                            right_label, verticalalignment='top', horizontalalignment='right',
                            bbox=bbox_props, color='black')

            self.canvas.draw()
               
        except Error as e:
            QMessageBox.critical(self, 'Database Connection Failed', f'Error: {e}', QMessageBox.Ok)

        try:
            # Export data
            self.export_df = pd.DataFrame({
                'Process Position [m]': df_data['Bandposition'],
                'Pressure [mbar]': df_data['Druck_Kammer_Messröhre_2'],
                'Tape Position [m]': df_data['Bandposition'],
                'Thickness [nm]': df_data['Filmetrics_DB_C2_Layer1d'],
                'Roughness': df_data['Optosurf_DB_Aq']
            })

            self.initialTextField.setVisible(True)
            self.saveButton.setVisible(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read the database:\n{str(e)}")
            self.label.setText("Failed to plot data.")