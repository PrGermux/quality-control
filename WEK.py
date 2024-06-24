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

class WEK(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.csv_file_name = None
        self.dat_file_name = None

        self.openCSVButton = QPushButton("Open CSV File")
        self.openCSVButton.clicked.connect(self.loadCSVFile)
        self.layout.addWidget(self.openCSVButton)

        self.openDATButton = QPushButton("Open DAT File")
        self.openDATButton.clicked.connect(self.loadDATFile)
        self.layout.addWidget(self.openDATButton)

        self.processButton = QPushButton("Fit")
        self.processButton.clicked.connect(self.processData)
        self.processButton.setEnabled(False)  # Disabled until both files are loaded
        self.layout.addWidget(self.processButton)

        self.label = QLabel("Choose CSV and DAT files to proceed.")
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
        self.ax1 = self.canvas.figure.add_subplot(211)
        self.ax2 = self.canvas.figure.add_subplot(212)

        plt.style.use('dark_background')
        self.canvas = FigureCanvas(Figure(figsize=(10, 10), facecolor='#434343'))
        self.layout.addWidget(self.canvas)
        self.ax1 = self.canvas.figure.add_subplot(211)
        self.ax2 = self.canvas.figure.add_subplot(212)
        self.ax1.set_facecolor('#434343')
        self.ax2.set_facecolor('#434343')
        self.ax1.axis('off')
        self.ax2.axis('off')

    def loadCSVFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if fileName:
            self.csv_file_name = fileName
            self.label.setText(f"CSV File Loaded: {fileName}")
            self.checkFilesLoaded()

    def loadDATFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Open DAT File", "", "DAT Files (*.dat);;All Files (*)", options=options)
        if fileName:
            self.dat_file_name = fileName
            self.label.setText(f"DAT File Loaded: {fileName}")
            self.checkFilesLoaded()

    def checkFilesLoaded(self):
        if self.csv_file_name and self.dat_file_name:
            self.processButton.setEnabled(True)
            self.label.setText(
                f"CSV File loaded: {self.csv_file_name}<br>"
                f"DAT File loaded: {self.dat_file_name}<br>"
                "Ready to fit."
                )

    def processData(self):
        if self.csv_file_name and self.dat_file_name:
            self.fit(self.csv_file_name, self.dat_file_name)
        else:
            QMessageBox.warning(self, "Error", "Please load both a CSV and a DAT file before processing.")

    def exportData(self):
        if self.export_df is not None and self.csv_file_name and self.dat_file_name:
            try:
                # Determine the directory of the CSV file
                process_folder_path = os.path.dirname(self.csv_file_name)  # Get the folder path of the csv file
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
        process_folder_path = os.path.dirname(self.csv_file_name)  # Get the folder path of the csv file
        process_folder_name = os.path.basename(os.path.dirname(os.path.dirname(process_folder_path)))  # Get the second back folder name
        tape_folder_name = os.path.basename(os.path.dirname(process_folder_path))
        sample_folder_name = os.path.basename(process_folder_path)

        title_text = f"Process sheet {process_folder_name}"  # Set the title text with the folder name
        tape_text = f"Tape: {tape_folder_name}"
        sample_text = f"Sample: {sample_folder_name}"

        # Create a figure with subplots
        plt.style.use('default')
        fig = Figure(figsize=(8, 6), dpi=dpi)
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)

        # Update plots for Sabre vs Position
        ax1.clear()
        ax1.plot(self.df['Position'], self.df['Sabre'], label='Sabre', linestyle='-', color='black', linewidth=1)
        ax1.plot(self.df['Position'], self.df['Sabre_MA'], label='Sabre 250 MA', linestyle='-', color='red')
        ax1.set_xlabel('Position [m]')
        ax1.set_ylabel('Sabre [mm/m]')
        ax1.set_xlim(0, 1400)
        ax1.set_ylim(-2.5, 2.5)
        ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax1.set_xticks(np.arange(0, 1450, 100))
        ax1.set_xticks(np.arange(0, 1450, 50), minor=True) 
        ax1.set_yticks(np.arange(-2.5, 3, 0.5))
        ax1.tick_params(axis='x', which='both', direction='in')
        ax1.tick_params(axis='y', which='both', direction='in')
        ax1.legend(loc='upper right')

        ax1.axhline(1.5, color='green', linestyle='--')
        ax1.axhline(-1.5, color='green', linestyle='--')
        ax1.fill_between(self.df['Position'], 1.5, -1.5, where=(self.df['Sabre'] >= -1.5) & (self.df['Sabre'] <= 1.5), color='green', alpha=0.25, hatch='//')

        # Update plots for Width vs Position
        ax2.clear()
        ax2.plot(self.df['Position'], self.df['Width'], label='Band width', linestyle='-', color='black', linewidth=1)
        ax2.plot(self.df['Position'], self.df['Width_MA'], label='Band width 250 MA', linestyle='-', color='red')
        ax2.set_xlabel('Position [m]')
        ax2.set_ylabel('Band width [mm]')
        ax2.set_xlim(0, 1400)
        ax2.set_ylim(11.98, 12.12)
        ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax2.set_xticks(np.arange(0, 1450, 100))
        ax2.set_xticks(np.arange(0, 1450, 50), minor=True) 
        ax2.set_yticks(np.arange(11.98, 12.14, 0.02))
        ax2.tick_params(axis='x', which='both', direction='in')
        ax2.tick_params(axis='y', which='both', direction='in')
        ax2.legend(loc='upper right')

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

        c.drawString(50, height - 580, f"Median band speed: {self.speed:.4f} m/s")
        c.drawString(50, height - 595, f"Sabre 250 MA: ({self.sabre_ma_avg:.2f} ± {self.sabre_ma_std:.2f}) mm/m  [{self.sabre_ma_min:.2f}, {self.sabre_ma_max:.2f}] mm/m")
        c.drawString(50, height - 610, f"Band width 250 MA: ({self.width_ma_avg:.2f} ± {self.width_ma_std:.2f})  [{self.width_ma_min:.2f}, {self.width_ma_max:.2f}] mm/m")

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

    def fit(self, CSVFileName, DATFileName):
        plt.style.use('dark_background')
        try:
            # Load data without parsing dates initially
            df_speed = pd.read_csv(DATFileName, delimiter=r'\s+', decimal=',', dtype={'"Date Time"': 'object'})

            # Strip quotes from column names
            df_speed.columns = df_speed.columns.str.strip('"')

            # Convert 'Date Time' to datetime after loading
            df_speed['Date Time'] = pd.to_datetime(df_speed['Date Time'].str.strip('"'), format='%d.%m.%Y %H:%M:%S,%f')

            # Calculate differences in 'Encoder_Pos_[m]'
            df_speed['Encoder_Pos_[m]'] = np.where(df_speed['Encoder_Pos_[m]'] < 0, np.nan, df_speed['Encoder_Pos_[m]'])
            # Calculate differences in 'Encoder_Pos_[m]'
            df_speed['Pos_Diff'] = df_speed['Encoder_Pos_[m]'].diff()
            # Filter out non-positive differences
            df_speed['Pos_Diff'] = np.where(df_speed['Pos_Diff'] <= 0, np.nan, df_speed['Pos_Diff'])

            # Calculate differences in 'Date Time' in seconds
            df_speed['Time_Diff'] = df_speed['Date Time'].diff().dt.total_seconds()
            # Filter out zero or negative time differences
            df_speed['Time_Diff'] = np.where(df_speed['Time_Diff'] <= 0, np.nan, df_speed['Time_Diff'])

            # Calculate speed in m/s, handling infinities and NaN
            df_speed['Speed'] = df_speed['Pos_Diff'] / df_speed['Time_Diff']
            df_speed['Speed'] = df_speed['Speed'].replace([np.inf, -np.inf], np.nan)

            # Calculate median speed, ignoring NaN values
            speed = np.nanmedian(df_speed['Speed'])

            self.speed = speed

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process the DAT file:\n{str(e)}")

        try:
            # Adjust the separator and correct handling of the decimal separator
            with open(CSVFileName, 'r', encoding='utf-8') as file:
                data = file.read().replace(',', '.')  # Correctly replace all commas

            df = pd.read_csv(StringIO(data), sep=';', usecols=['Zeit kleiner Sekunde', 'OUT1', 'OUT2'])
        
            # Ensuring numeric types and handling missing or incorrect data
            df['Zeit kleiner Sekunde'] = pd.to_numeric(df['Zeit kleiner Sekunde'], errors='coerce').fillna(0)
            df['OUT1'] = pd.to_numeric(df['OUT1'], errors='coerce').fillna(1)  # Ensure no division by zero
            df['OUT2'] = pd.to_numeric(df['OUT2'], errors='coerce').fillna(0)

            # Calculate differences for 'Position'
            time_diff = df['Zeit kleiner Sekunde'].diff().fillna(0)
            indices = np.arange(len(df))
            df['Position'] = np.where(time_diff > 0,
                                      time_diff * indices * speed,
                                      (1 + time_diff) * indices * speed)

            # Calculate 'Sabre' column
            condition_1 = df['OUT1'] > 0
            condition_2 = df['OUT2'] > 0
            df['angle'] = np.arctan2(df['OUT2'], df['OUT1']) * 180 / np.pi  # Use arctan2 for better angle calculation
            df['Sabre'] = np.where(condition_1 & condition_2, (((df['angle'] - 45) * 1.25 + 0.25) + 0.5) / 11.78 * 0.935, np.nan)

            df['Sabre_MA'] = df['Sabre'].rolling(window=250, min_periods=1).mean()  # Moving average for Sabre
            # Identify the last valid index of the original 'Sabre' data
            last_valid_index_sabre = df['Sabre'].last_valid_index()

            # Truncate the moving average series at the last valid data point
            df['Sabre_MA'] = df['Sabre_MA'].iloc[:last_valid_index_sabre + 1]

            sabre_ma_avg = abs(df['Sabre_MA']).mean()
            self.sabre_ma_avg = sabre_ma_avg

            sabre_ma_std = abs(df['Sabre_MA']).std()
            self.sabre_ma_std = sabre_ma_std

            sabre_ma_min = abs(df['Sabre_MA']).min()
            self.sabre_ma_min = sabre_ma_min

            sabre_ma_max = abs(df['Sabre_MA']).max()
            self.sabre_ma_max = sabre_ma_max

            # Calculate 'Width'
            df['Width'] = np.where(condition_1 & condition_2, 
                                   np.sqrt((df['OUT1'] - 0.1 * np.sin(df['angle'] * pi / 180))**2 + 
                                           (df['OUT2'] - 0.1 * np.cos(df['angle'] * pi / 180))**2), np.nan)

            df['Width_MA'] = df['Width'].rolling(window=250, min_periods=1).mean()  # Moving average for Width

            # Identify the last valid index of the original 'Sabre' data
            last_valid_index_width = df['Width'].last_valid_index()

            # Truncate the moving average series at the last valid data point
            df['Width_MA'] = df['Width_MA'].iloc[:last_valid_index_width + 1]
            
            width_ma_avg = df['Width_MA'].mean()
            self.width_ma_avg = width_ma_avg

            width_ma_std = df['Width_MA'].std()       
            self.width_ma_std = width_ma_std

            width_ma_min = df['Width_MA'].min()
            self.width_ma_min = width_ma_min

            width_ma_max = df['Width_MA'].max()
            self.width_ma_max = width_ma_max

            self.df = df

            self.label.setText(
                f"CSV File Loaded: {CSVFileName}<br>"
                f"DAT File Loaded: {DATFileName}"
                )

            max_valid_position = df['Position'][df['Sabre'].notna()].max()
            self.max_valid_position = max_valid_position

            # Update plots for Sabre vs Position
            self.ax1.clear()
            self.ax1.plot(df['Position'], df['Sabre'], label='Sabre', linestyle='-', color='white', linewidth=1)
            self.ax1.plot(df['Position'], df['Sabre_MA'], label='Sabre 250 MA', linestyle='-', color='red')
            self.ax1.set_xlabel('Position [m]')
            self.ax1.set_ylabel('Sabre [mm/m]')
            self.ax1.set_xlim(0, 1400)
            self.ax1.set_ylim(-2.5, 2.5)
            self.ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
            self.ax1.set_xticks(np.arange(0, 1450, 100))
            self.ax1.set_xticks(np.arange(0, 1450, 50), minor=True) 
            self.ax1.set_yticks(np.arange(-2.5, 3, 0.5))
            self.ax1.tick_params(axis='x', direction='in', which='both')  # Ticks inside for x-axis
            self.ax1.tick_params(axis='y', direction='in', which='both')  # Ticks inside for y-axis
            self.ax1.legend(loc='upper right')  # Add legend to the plot

            # Draw horizontal lines and fill between
            self.ax1.axhline(1.5, color='green', linestyle='--')
            self.ax1.axhline(-1.5, color='green', linestyle='--')
            self.ax1.fill_between(df['Position'], 1.5, -1.5, where=(df['Sabre'] >= -1.5) & (df['Sabre'] <= 1.5),
                                  color='green', alpha=0.25, hatch='//')

            # Update plots for Width vs Position
            self.ax2.clear()
            self.ax2.plot(df['Position'], df['Width'], label='Band width', linestyle='-', color='white', linewidth=1)
            self.ax2.plot(df['Position'], df['Width_MA'], label='Band width 250 MA', linestyle='-', color='red')
            self.ax2.set_xlabel('Position [m]')
            self.ax2.set_ylabel('Band width [mm]')
            self.ax2.set_xlim(0, 1400)
            self.ax2.set_ylim(11.98, 12.12)
            self.ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
            self.ax2.set_xticks(np.arange(0, 1450, 100))
            self.ax2.set_xticks(np.arange(0, 1450, 50), minor=True)
            self.ax2.set_yticks(np.arange(11.98, 12.14, 0.02))
            self.ax2.tick_params(axis='x', direction='in', which='both')  # Ticks inside for x-axis
            self.ax2.tick_params(axis='y', direction='in', which='both')  # Ticks inside for y-axis
            self.ax2.legend(loc='upper right')  # Add legend to the plot

            self.canvas.draw()

            # Export data
            self.export_df = pd.DataFrame({
                'Position [m]': df['Position'],
                'Sabre [mm/m]': df['Sabre'],
                'Band width [mm]': df['Width'],
            })

            self.initialTextField.setVisible(True)
            self.saveButton.setVisible(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read the file:\n{str(e)}")
            self.label.setText("Failed to load data.")
        
        self.results.setText(
            f'Median band speed: <b>{speed:.4f} m/s</b> <br>'
            f'Sabre 250 MA: <b>({sabre_ma_avg:.2f} ± {sabre_ma_std:.2f}) mm/m</b> &nbsp; <b>[{sabre_ma_min:.2f}, {sabre_ma_max:.2f}] mm/m</b><br>'
            f'Band width 250 MA: <b>({width_ma_avg:.2f} ± {width_ma_std:.2f}) mm</b> &nbsp; <b>[{width_ma_min:.2f}, {width_ma_max:.2f}] mm<b>'
            )