import io
import base64
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from db import get_events, get_event_stats

class NoiseReport(FPDF):
    def __init__(self, from_date=None, to_date=None):
        super().__init__()
        self.from_date = from_date
        self.to_date = to_date
        self.events = get_events(from_date=from_date, to_date=to_date)
        self.stats = get_event_stats(from_date=from_date, to_date=to_date)

    def header(self):
        if self.page_no() > 1:  # No header on cover page
            self.set_font('Arial', 'B', 10)
            self.cell(0, 10, 'Noise Disturbance Report', 0, 1, 'R')
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_cover_page(self):
        """Add the cover page with title and date range."""
        self.add_page()
        self.ln(40)

        # Title
        self.set_font('Arial', 'B', 24)
        self.cell(0, 15, 'Noise Disturbance Report', 0, 1, 'C')
        self.ln(10)

        # Subtitle
        self.set_font('Arial', '', 14)
        self.cell(0, 10, 'Evidence Documentation for JMB/MC Complaint', 0, 1, 'C')
        self.ln(20)

        # Date range
        self.set_font('Arial', '', 12)
        if self.from_date and self.to_date:
            self.cell(0, 10, f'Report Period: {self.from_date} to {self.to_date}', 0, 1, 'C')
        else:
            self.cell(0, 10, 'Report Period: All Recorded Events', 0, 1, 'C')
        self.ln(10)

        # Generated date
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.ln(30)

        # Device ID
        if self.events:
            self.cell(0, 10, f'Device ID: {self.events[0]["device_id"]}', 0, 1, 'C')

    def add_summary_table(self):
        """Add summary statistics table."""
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Summary Statistics', 0, 1, 'L')
        self.ln(5)

        if not self.stats:
            self.set_font('Arial', '', 12)
            self.cell(0, 10, 'No events recorded in the selected period.', 0, 1, 'L')
            return

        # Table header
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(200, 200, 200)
        self.cell(100, 10, 'Metric', 1, 0, 'L', True)
        self.cell(90, 10, 'Value', 1, 1, 'L', True)

        # Table rows
        self.set_font('Arial', '', 11)
        self.cell(100, 10, 'Total Noise Events', 1, 0, 'L')
        self.cell(90, 10, str(self.stats['total_events']), 1, 1, 'L')

        self.cell(100, 10, 'Average Noise Level (dB)', 1, 0, 'L')
        self.cell(90, 10, f"{self.stats['avg_db']:.1f}", 1, 1, 'L')

        self.cell(100, 10, 'Peak Noise Level (dB)', 1, 0, 'L')
        self.cell(90, 10, f"{self.stats['peak_db']:.1f}", 1, 1, 'L')

        self.cell(100, 10, 'Total Duration (seconds)', 1, 0, 'L')
        self.cell(90, 10, str(self.stats['total_duration_sec']), 1, 1, 'L')

        self.cell(100, 10, 'Average Duration per Event (seconds)', 1, 0, 'L')
        avg_duration = self.stats['total_duration_sec'] / self.stats['total_events']
        self.cell(90, 10, f"{avg_duration:.1f}", 1, 1, 'L')

    def add_timeline_chart(self):
        """Add timeline chart showing events over time."""
        if not self.events:
            return

        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Noise Event Timeline', 0, 1, 'L')
        self.ln(5)

        # Create matplotlib chart
        fig, ax = plt.subplots(figsize=(8, 4))

        timestamps = [datetime.fromisoformat(e['timestamp']) for e in self.events]
        peak_dbs = [e['peak_db'] for e in self.events]

        ax.bar(timestamps, peak_dbs, color='#3498db', alpha=0.7)
        ax.set_xlabel('Time')
        ax.set_ylabel('Peak dB SPL')
        ax.set_title('Noise Events Over Time')
        ax.grid(True, alpha=0.3)

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Save chart to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150)
        img_buffer.seek(0)

        # Add chart to PDF
        img_data = img_buffer.getvalue()
        self.image(io.BytesIO(img_data), x=10, w=190)

        plt.close(fig)

    def add_top_incidents(self):
        """Add table of top 10 worst incidents."""
        if not self.events:
            return

        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Top 10 Worst Noise Incidents', 0, 1, 'L')
        self.ln(5)

        # Sort by peak_db descending
        sorted_events = sorted(self.events, key=lambda e: e['peak_db'], reverse=True)[:10]

        # Table header
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(200, 200, 200)
        self.cell(15, 10, '#', 1, 0, 'C', True)
        self.cell(75, 10, 'Timestamp', 1, 0, 'L', True)
        self.cell(40, 10, 'Peak dB', 1, 0, 'L', True)
        self.cell(40, 10, 'Duration (s)', 1, 0, 'L', True)
        self.cell(20, 10, 'Device', 1, 1, 'L', True)

        # Table rows
        self.set_font('Arial', '', 9)
        for i, event in enumerate(sorted_events, 1):
            self.cell(15, 8, str(i), 1, 0, 'C')
            self.cell(75, 8, event['timestamp'][:19], 1, 0, 'L')
            self.cell(40, 8, f"{event['peak_db']:.1f}", 1, 0, 'L')
            self.cell(40, 8, str(event['duration_sec']), 1, 0, 'L')
            self.cell(20, 8, event['device_id'][-3:], 1, 1, 'L')

    def add_legal_reference(self):
        """Add legal reference box."""
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Legal Reference', 0, 1, 'L')
        self.ln(5)

        # Box background
        self.set_fill_color(240, 248, 255)
        self.rect(10, self.get_y(), 190, 80, 'F')

        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Strata Management Act 2013 (Act 757)', 0, 1, 'L')

        self.set_font('Arial', '', 10)
        self.ln(2)
        self.multi_cell(0, 6,
            'Third Schedule - By-laws for the management and maintenance of a building\n\n'
            'By-law 4: Noise\n\n'
            '(1) A proprietor or occupier of a parcel shall not make or permit to be made any '
            'noise or vibration likely to interfere with the peaceful enjoyment of the '
            'proprietor or occupier of any other parcel or of any common property.\n\n'
            '(2) A proprietor or occupier of a parcel shall not permit any musical instrument, '
            'television set, radio, gramophone, or other sound-producing device to be operated '
            'in the parcel in such a manner as to cause annoyance or discomfort to the '
            'proprietor or occupier of any other parcel.'
        )

    def add_footer_info(self):
        """Add footer information."""
        self.ln(10)
        self.set_font('Arial', 'I', 8)
        self.multi_cell(0, 5,
            'This report was automatically generated by Noise Logger v1.0.\n'
            'All measurements are approximate and should be verified with professional equipment for legal proceedings.\n'
            f'Device ID: {self.events[0]["device_id"] if self.events else "N/A"}'
        )

    def generate(self):
        """Generate the complete PDF report."""
        if not self.events:
            # Empty report
            self.add_page()
            self.set_font('Arial', '', 14)
            self.cell(0, 10, 'No noise events recorded in the selected period.', 0, 1, 'C')
            return self.output(dest='S').encode('latin-1')

        self.add_cover_page()
        self.add_summary_table()
        self.add_timeline_chart()
        self.add_top_incidents()
        self.add_legal_reference()
        self.add_footer_info()

        return self.output(dest='S').encode('latin-1')
