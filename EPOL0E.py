from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QLineEdit, QSpacerItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
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

class EPOL0E(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.camera_csv_file_name = None
        self.process_csv_file_name = None

        self.openCameraCSVButton = QPushButton("Open Camera CSV File")
        self.openCameraCSVButton.clicked.connect(self.loadCameraCSVFile)
        self.layout.addWidget(self.openCameraCSVButton)

        self.openProcessCSVButton = QPushButton("Open Process CSV File")
        self.openProcessCSVButton.clicked.connect(self.loadProcessCSVFile)
        self.layout.addWidget(self.openProcessCSVButton)

        self.processButton = QPushButton("Fit")
        self.processButton.clicked.connect(self.processData)
        self.processButton.setEnabled(False)  # Disabled until both files are loaded
        self.layout.addWidget(self.processButton)

        self.label = QLabel("Choose Camera and Process CSV files to proceed.")
        self.layout.addWidget(self.label)

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
        self.ax1 = self.canvas.figure.add_subplot(221)
        self.ax2 = self.canvas.figure.add_subplot(222)
        self.ax3 = self.canvas.figure.add_subplot(223)
        self.ax4 = self.canvas.figure.add_subplot(224)

        plt.style.use('dark_background')
        self.figure = Figure(figsize=(12, 12), facecolor='#434343')
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.ax1 = self.figure.add_subplot(221)  # Top-left
        self.ax2 = self.figure.add_subplot(222)  # Top-right
        self.ax3 = self.figure.add_subplot(223)  # Bottom-left
        self.ax4 = self.figure.add_subplot(224)  # Bottom-right

        self.ax1.set_facecolor('#434343')
        self.ax2.set_facecolor('#434343')
        self.ax3.set_facecolor('#434343')
        self.ax4.set_facecolor('#434343')

        self.ax1.axis('off')
        self.ax2.axis('off')
        self.ax3.axis('off')
        self.ax4.axis('off')

    def loadCameraCSVFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if fileName:
            self.camera_csv_file_name = fileName
            self.label.setText(f"Camera CSV File Loaded: {fileName}")
            self.checkFilesLoaded()

    def loadProcessCSVFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "DAT Files (*.csv);;All Files (*)", options=options)
        if fileName:
            self.process_csv_file_name = fileName
            self.label.setText(f"Process CSV File Loaded: {fileName}")
            self.checkFilesLoaded()

    def checkFilesLoaded(self):
        if self.camera_csv_file_name and self.process_csv_file_name:
            self.processButton.setEnabled(True)
            self.label.setText(
                f"Camera CSV File loaded: {self.camera_csv_file_name}<br>"
                f"Process CSV File loaded: {self.process_csv_file_name}<br>"
                "Ready to fit."
                )

    def processData(self):
        if self.camera_csv_file_name and self.process_csv_file_name:
            self.fit(self.camera_csv_file_name, self.process_csv_file_name)
        else:
            QMessageBox.warning(self, "Error", "Please load both Camera and Process CSV file before processing.")

    def exportData(self):
        if self.export_df is not None and self.camera_csv_file_name and self.process_csv_file_name:
            try:
                # Determine the directory of the CSV file
                process_folder_path = os.path.dirname(self.camera_csv_file_name)  # Get the folder path of the csv file
                tape_folder_name = os.path.basename(os.path.dirname(process_folder_path))
                sample_folder_name = os.path.basename(process_folder_path)
                data_file_name = os.path.join(process_folder_path, f"{tape_folder_name}_fitted.dat")
                
                # Save DataFrame to a .dat file
                self.export_df.to_csv(data_file_name, sep='\t', index=False, float_format='%.2f')
                QMessageBox.information(self, "Data Save Successful", f"Data saved to {data_file_name}")

                pdf_file_name = os.path.join(process_folder_path, f"{tape_folder_name}_report.pdf")
                self.exportPDF(pdf_file_name)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save data:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "No data available to save. Please process the data first.")

    def exportPDF(self, pdf_file_name, dpi=300):
        process_folder_path = os.path.dirname(self.camera_csv_file_name)  # Get the folder path of the csv file
        process_folder_name = os.path.basename(os.path.dirname(os.path.dirname(process_folder_path)))  # Get the second back folder name
        tape_folder_name = os.path.basename(os.path.dirname(process_folder_path))
        sample_folder_name = os.path.basename(process_folder_path)

        title_text = f"Process sheet {process_folder_name}"  # Set the title text with the folder name
        tape_text = f"Tape: {tape_folder_name}"
        sample_text = f"Sample: {sample_folder_name}"

        # Create a figure with subplots
        plt.style.use('default')
        fig = Figure(figsize=(8, 6), dpi=dpi)
        ax1 = fig.add_subplot(221)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(223)
        ax4 = fig.add_subplot(224)

        ax1.clear()
        ax2.clear()
        ax3.clear()
        ax4.clear()

        # Plot 'Intensity' vs 'Position'
        ax1.plot(self.df['Position'], self.df['Int'], label='Intensity', color='black', linestyle='-', linewidth=1)
        ax1.set_xlim(0, self.max_valid_position)
        ax1.set_ylim(0, 50)
        ax1.tick_params(axis='x', direction='in', which='both')
        ax1.tick_params(axis='y', direction='in', which='both') 
        ax1.set_xlabel('Position [m]')
        ax1.set_ylabel('Intensity')
        ax1.legend()
        ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

        # Draw horizontal lines and fill between
        ax1.axhline(10, color='green', linestyle='--')
        ax1.axhline(0, color='green', linestyle='--')
        ax1.fill_between(self.df['Position'], 10, 0, where=(self.df['Int'] >= 0) & (self.df['Int'] <= 10), 
                              color='green', alpha=0.25, hatch='//')    

        # Plot 'Area' vs 'Position'
        ax2.scatter(self.df['Position'], self.df['Area'], label='Area', color='black', s=3)
        ax2.set_xlim(0, self.max_valid_position)
        ax2.set_ylim(0, 200)
        ax2.tick_params(axis='x', direction='in', which='both')
        ax2.tick_params(axis='y', direction='in', which='both')
        ax2.set_xlabel('Position [m]')
        ax2.set_ylabel('Int_Area')
        ax2.legend()
        ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

        # Draw horizontal lines and fill between
        ax2.axhline(15, color='green', linestyle='--')
        ax2.axhline(0, color='green', linestyle='--')
        ax2.fill_between(self.df['Position'], 15, 0, where=(self.df['Int'] >= 0) & (self.df['Int'] <= 15), 
                              color='green', alpha=0.25, hatch='//')  

        # Plot 'Int_Edge1' and 'Int_Edge2' vs 'Position'
        ax3.plot(self.df['Position'], self.df['Int_Edge1'], label='Int_Edge1', color='red', linestyle='-', linewidth=1)
        ax3.plot(self.df['Position'], self.df['Int_Edge2'], label='Int_Edge2', color='blue', linestyle='-', linewidth=1)
        ax3.set_xlim(0, self.max_valid_position)
        ax3.set_ylim(0, 50)
        ax3.tick_params(axis='x', direction='in', which='both')
        ax3.tick_params(axis='y', direction='in', which='both')
        ax3.set_xlabel('Position [m]')
        ax3.set_ylabel('Int_Edge')
        ax3.legend()
        ax3.grid(True, which='both', linestyle='--', linewidth=0.5)

        # Draw horizontal lines and fill between
        ax3.axhline(15, color='green', linestyle='--')
        ax3.axhline(0, color='green', linestyle='--')
        ax3.fill_between(self.df['Position'], 15, 0, where=(self.df['Int_Edge1'] >= 0) & (self.df['Int_Edge1'] <= 15), 
                              color='green', alpha=0.25, hatch='//')  
        
        # Plot 'Sensor1' and 'Sensor2' vs 'Position'
        ax4.scatter(self.df['Sensor_Position'], self.df['Sensor1'], label='Sensor1', color='purple', s=3)
        ax4.scatter(self.df['Sensor_Position'], self.df['Sensor2'], label='Sensor2', color='orange', s=3)
        ax4.tick_params(axis='x', direction='in', which='both')
        ax4.tick_params(axis='y', direction='in', which='both')
        ax4.set_xlabel('Position [m]')
        ax4.set_ylabel('Temperature [°C]')
        ax4.legend()
        ax4.grid(True, which='both', linestyle='--', linewidth=0.5)

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

        c.drawString(50, height - 580, f'Average speed: {self.speed} m/h')
        c.drawString(50, height - 595, f'Intensity: ({self.int_avg:.2f} ± {self.int_std:.2f}) [{self.int_min:.2f}, {self.int_max:.2f}]')
        c.drawString(50, height - 610, f'Int_Area: ({self.area_avg:.2f} ± {self.area_std:.2f})  [{self.area_min:.2f}, {self.area_max:.2f}]')
        c.drawString(50, height - 625, f'Int_Edge1: ({self.int_edge1_avg:.2f} ± {self.int_edge1_std:.2f})   [{self.int_edge1_min:.2f}, {self.int_edge1_max:.2f}]')
        c.drawString(50, height - 640, f'Int_Edge2: ({self.int_edge2_avg:.2f} ± {self.int_edge2_std:.2f})   [{self.int_edge2_min:.2f}, {self.int_edge2_max:.2f}]')
        c.drawString(50, height - 655, f'Sensor1: ({self.sensor1_avg:.2f} ± {self.sensor1_std:.2f}) °C [{self.sensor1_min:.2f}, {self.sensor1_max:.2f}] °C')
        c.drawString(50, height - 670, f'Sensor2: ({self.sensor2_avg:.2f} ± {self.sensor2_std:.2f}) °C [{self.sensor2_min:.2f}, {self.sensor2_max:.2f}] °C')

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

    def fit(self, CameraCSVFileName, ProcessCSVFileName):
        plt.style.use('dark_background')
        try:
            # Correctly use a raw string for the regular expression delimiter
            df_camera = pd.read_csv(CameraCSVFileName, sep=r'\s+', header=0,
                                    names=['Hour', 'Minute', 'Sec', 'Int', 'Int_Max', 'Int_Sa', 'Area', 'Edges', 'Edge_Position', 'Int_Edge1', 'Int_Edge2'],
                                    dtype={'Hour': 'int', 'Minute': 'int', 'Sec': 'int', 'Int': 'int', 'Int_Max': 'int',
                                        'Int_Sa': 'int', 'Area': 'int', 'Edges': 'int', 'Edge_Position': 'float',
                                        'Int_Edge1': 'float', 'Int_Edge2': 'float'})

            # Calculate total time in minutes
            df_camera['Time'] = df_camera['Hour'] + df_camera['Minute'] / 60 + df_camera['Sec'] / 3600 # Time in h

            self.df = pd.DataFrame()
            self.df['Time'] = df_camera['Time']
            self.df['Area'] = np.where(df_camera['Area'] > 1000, np.nan, df_camera['Area'])
            self.df['Int'] = np.where(df_camera['Area'] > 1000, np.nan, df_camera['Int'])
            self.df['Int_Edge1'] = np.where(df_camera['Area'] > 1000, np.nan, df_camera['Int_Edge1'])
            self.df['Int_Edge2'] = np.where(df_camera['Area'] > 1000, np.nan, df_camera['Int_Edge2'])

            int_avg = self.df['Int'].mean()
            self.int_avg = int_avg
            int_std = self.df['Int'].std()
            self.int_std = int_std
            int_min = self.df['Int'].min()
            self.int_min = int_min
            int_max = self.df['Int'].max()
            self.int_max = int_max

            int_edge1_avg = self.df['Int_Edge1'].mean()
            self.int_edge1_avg = int_edge1_avg
            int_edge1_std = self.df['Int_Edge1'].std()
            self.int_edge1_std = int_edge1_std
            int_edge1_min = self.df['Int_Edge1'].min()
            self.int_edge1_min = int_edge1_min
            int_edge1_max = self.df['Int_Edge1'].max()
            self.int_edge1_max = int_edge1_max

            int_edge2_avg = self.df['Int_Edge2'].mean()
            self.int_edge2_avg = int_edge2_avg
            int_edge2_std = self.df['Int_Edge2'].std()
            self.int_edge2_std = int_edge2_std
            int_edge2_min = self.df['Int_Edge2'].min()
            self.int_edge2_min = int_edge2_min
            int_edge2_max = self.df['Int_Edge2'].max()
            self.int_edge2_max = int_edge2_max

            area_avg = self.df['Area'].mean()
            self.area_avg = area_avg
            area_std = self.df['Area'].std()
            self.area_std = area_std
            area_min = self.df['Area'].min()
            self.area_min = area_min
            area_max = self.df['Area'].max()
            self.area_max = area_max

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process the Camera CSV file:\n{str(e)}")
            return

        try:
            df_process = pd.read_csv(ProcessCSVFileName, sep=';', decimal=',', encoding='ISO-8859-1')
            df_process['VarValue'] = df_process['VarValue'].astype(str)  # Ensure VarValue is treated as string

            valid_speeds = df_process[(df_process['VarName'] == 'Istgeschwindigkeit') & (df_process['VarValue'].str.replace(',', '.').astype(float) > 0)]
            speed = int(np.mean(pd.to_numeric(valid_speeds['VarValue'].str.replace(',', '.'), errors='coerce').dropna()))
            self.speed = speed # Speed in m/h

            self.df['Position'] = self.df['Time'] * self.speed

            # Shift all positions so that the minimum position value is 0
            min_position = self.df['Position'].min()
            self.df['Position'] -= min_position

            self.df['Sensor_Position'] = pd.to_numeric(df_process[df_process['VarName'] == 'Bandposition']['VarValue'].str.replace(',', '.'), errors='coerce').dropna().reset_index(drop=True)
            self.df['Sensor1'] = pd.to_numeric(df_process[df_process['VarName'] == 'Poliertank_Sensor_1']['VarValue'].str.replace(',', '.'), errors='coerce').dropna().reset_index(drop=True)
            self.df['Sensor2'] = pd.to_numeric(df_process[df_process['VarName'] == 'Poliertank_Sensor_2']['VarValue'].str.replace(',', '.'), errors='coerce').dropna().reset_index(drop=True)

            sensor1_avg = self.df['Sensor1'].mean()
            self.sensor1_avg = sensor1_avg
            sensor1_std = self.df['Sensor1'].std()
            self.sensor1_std = sensor1_std
            sensor1_min = self.df['Sensor1'].min()
            self.sensor1_min = sensor1_min
            sensor1_max = self.df['Sensor1'].max()
            self.sensor1_max = sensor1_max

            sensor2_avg = self.df['Sensor2'].mean()
            self.sensor2_avg = sensor2_avg
            sensor2_std = self.df['Sensor2'].std()
            self.sensor2_std = sensor2_std
            sensor2_min = self.df['Sensor2'].min()
            self.sensor2_min = sensor2_min
            sensor2_max = self.df['Sensor2'].max()
            self.sensor2_max = sensor2_max

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read the Process CSV file:\n{str(e)}")
            self.label.setText("Failed to load data.")

        max_valid_position = self.df['Position'].max()
        self.max_valid_position = max_valid_position

        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()

        # Plot 'Intensity' vs 'Position'
        self.ax1.plot(self.df['Position'], self.df['Int'], label='Intensity', color='white', linestyle='-', linewidth=1)
        self.ax1.set_xlim(0, max_valid_position)
        self.ax1.set_ylim(0, 50)
        self.ax1.tick_params(axis='x', direction='in', which='both')
        self.ax1.tick_params(axis='y', direction='in', which='both') 
        self.ax1.set_xlabel('Position [m]')
        self.ax1.set_ylabel('Intensity')
        self.ax1.legend()
        self.ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

        # Draw horizontal lines and fill between
        self.ax1.axhline(10, color='green', linestyle='--')
        self.ax1.axhline(0, color='green', linestyle='--')
        self.ax1.fill_between(self.df['Position'], 10, 0, where=(self.df['Int'] >= 0) & (self.df['Int'] <= 10), 
                              color='green', alpha=0.25, hatch='//')    

        # Plot 'Area' vs 'Position'
        self.ax2.scatter(self.df['Position'], self.df['Area'], label='Area', color='white', s=3)
        self.ax2.set_xlim(0, max_valid_position)
        self.ax2.set_ylim(0, 200)
        self.ax2.tick_params(axis='x', direction='in', which='both')
        self.ax2.tick_params(axis='y', direction='in', which='both') 
        self.ax2.set_xlabel('Position [m]')
        self.ax2.set_ylabel('Int_Area')
        self.ax2.legend()
        self.ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

        # Draw horizontal lines and fill between
        self.ax2.axhline(15, color='green', linestyle='--')
        self.ax2.axhline(0, color='green', linestyle='--')
        self.ax2.fill_between(self.df['Position'], 15, 0, where=(self.df['Int'] >= 0) & (self.df['Int'] <= 15), 
                              color='green', alpha=0.25, hatch='//')  

        # Draw horizontal lines and fill between
        self.ax3.axhline(15, color='green', linestyle='--')
        self.ax3.axhline(0, color='green', linestyle='--')
        self.ax3.fill_between(self.df['Position'], 15, 0, where=(self.df['Int_Edge1'] >= 0) & (self.df['Int_Edge1'] <= 15),
                              color='green', alpha=0.25, hatch='//')  

        # Plot 'Int_Edge1' and 'Int_Edge2' vs 'Position'
        self.ax3.plot(self.df['Position'], self.df['Int_Edge1'], label='Int_Edge1', color='red', linestyle='-', linewidth=1)
        self.ax3.plot(self.df['Position'], self.df['Int_Edge2'], label='Int_Edge2', color='blue', linestyle='-', linewidth=1)
        self.ax3.set_xlim(0, max_valid_position)
        self.ax3.set_ylim(0, 50)
        self.ax3.tick_params(axis='x', direction='in', which='both')
        self.ax3.tick_params(axis='y', direction='in', which='both') 
        self.ax3.set_xlabel('Position [m]')
        self.ax3.set_ylabel('Int_Edge')
        self.ax3.legend()
        self.ax3.grid(True, which='both', linestyle='--', linewidth=0.5)
        
        # Plot 'Sensor1' and 'Sensor2' vs 'Position'
        self.ax4.scatter(self.df['Sensor_Position'], self.df['Sensor1'], label='Sensor1', color='purple', s=3)
        self.ax4.scatter(self.df['Sensor_Position'], self.df['Sensor2'], label='Sensor2', color='orange', s=3)
        self.ax4.tick_params(axis='x', direction='in', which='both')
        self.ax4.tick_params(axis='y', direction='in', which='both') 
        self.ax4.set_xlabel('Position [m]')
        self.ax4.set_ylabel('Temperature [°C]')
        self.ax4.legend()
        self.ax4.grid(True, which='both', linestyle='--', linewidth=0.5)

        self.canvas.draw() 

        self.initialTextField.setVisible(True)
        self.saveButton.setVisible(True)

        self.export_df = pd.DataFrame({
            'Position [m]': self.df['Position'],
            'Intensity': self.df['Int'],
            'Int_Area': self.df['Area'],
            'Int_Edge1': self.df['Int_Edge1'],
            'Int_Edge2': self.df['Int_Edge2'],
            'Position Sensor [m]': self.df['Sensor_Position'],
            'Temperature Sensor 1 [°C]': self.df['Sensor1'],
            'Temperature Sensor 2 [°C]': self.df['Sensor2']
        })

        self.results.setText(
            f'Average speed: <b>{speed} m/h</b><br>'
            f'Intensity: <b>({int_avg:.2f} ± {int_std:.2f})</b> &nbsp; <b>[{int_min:.2f}, {int_max:.2f}]</b><br>'
            f'Int_Area: <b>({area_avg:.2f} ± {area_std:.2f})</b> &nbsp; <b>[{area_min:.2f}, {area_max:.2f}]</b><br>'
            f'Int_Edge1: <b>({int_edge1_avg:.2f} ± {int_edge1_std:.2f})</b> &nbsp; <b>[{int_edge1_min:.2f}, {int_edge1_max:.2f}]</b><br>'
            f'Int_Edge2: <b>({int_edge2_avg:.2f} ± {int_edge2_std:.2f})</b> &nbsp; <b>[{int_edge2_min:.2f}, {int_edge2_max:.2f}]</b><br>'
            f'Sensor1: <b>({sensor1_avg:.2f} ± {sensor1_std:.2f}) °C</b> &nbsp; <b>[{sensor1_min:.2f}, {sensor1_max:.2f}] °C</b><br>'
            f'Sensor2: <b>({sensor2_avg:.2f} ± {sensor2_std:.2f}) °C</b> &nbsp; <b>[{sensor2_min:.2f}, {sensor2_max:.2f}] °C</b><br>'
            )    