import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# Define the data folder path
app_path = os.path.dirname(os.path.abspath(__file__))

data_folder = os.path.join(app_path, '../data')
charts_folder = os.path.join(app_path, '../webserver/static/')

# Function to parse JSON files
def parse_json_files(data_folder):
    json_files = [f for f in os.listdir(data_folder) if f.endswith('.json')]
    data = []

    for file in json_files:
        with open(os.path.join(data_folder, file), 'r') as f:
            json_data = json.load(f)
            json_data['filename'] = file  # Add filename to json data
            data.append(json_data)

    return data

# Function to process data
def process_data(data) -> pd.DataFrame:
    worker_stats = []

    for entry in data:
        # Extract timestamp from filename
        timestamp_str = entry['filename'].replace('.json', '').replace('_', ' ').replace('.', ':')
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        workers = entry.get('workers', {})

        for worker, stats in workers.items():
            worker_stats.append({
                'timestamp': timestamp,
                'worker': worker,
                'connected': "Connected" if stats['connected'] else "Not Connected",
                'hash_rate': stats['hash_rate']
            })

    return pd.DataFrame(worker_stats)

# Function to generate placeholder image
def generate_placeholder_image(filename, message="Insufficient Data Available"):
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color=(73, 109, 137))
    draw = ImageDraw.Draw(image)

    try:
        # Use a truetype font if available
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        # Use default font
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), message, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) / 2
    text_y = (height - text_height) / 2
    draw.text((text_x, text_y), message, font=font, fill=(255, 255, 255))

    image.save(filename)

# Function to generate charts
def generate_charts(worker_stats: pd.DataFrame):
    # Convert timestamps to datetime
    worker_stats['timestamp'] = pd.to_datetime(worker_stats['timestamp'])

    # Ensure the static folder exists
    if not os.path.exists(charts_folder):
        os.makedirs(charts_folder)

    # Pie chart for worker uptime
    uptime_counts = worker_stats['connected'].value_counts()
    
    if not uptime_counts.empty:
        plt.figure(figsize=(8, 6))
        plt.pie(uptime_counts, labels=uptime_counts.index, autopct='%1.1f%%', startangle=140)
        plt.title('Worker Uptime')
        plt.savefig(os.path.join(charts_folder, 'worker_uptime_pie_chart.png'))
        plt.close()
    else:
        generate_placeholder_image(os.path.join(charts_folder, 'worker_uptime_pie_chart.png'))

    # Bar chart for number of workers connected
    total_workers = worker_stats['worker'].nunique()
    hourly_stats = worker_stats.groupby([worker_stats['timestamp'].dt.floor('h'), 'connected'])['worker'].count().unstack(fill_value=0)
    
    workers_connected = hourly_stats['Connected'] if 'Connected' in hourly_stats.columns else pd.Series(0, index=hourly_stats.index)

    # Ensure all hours are present in the index
    if not workers_connected.empty:
        all_hours = pd.date_range(start=workers_connected.index.min(), end=workers_connected.index.max(), freq='h')
        workers_connected = workers_connected.reindex(all_hours, fill_value=0)

        
        plt.figure(figsize=(10, 6))
        workers_connected.plot(kind='bar')
        plt.xlabel('Time (Hourly)')
        plt.ylabel('Number of Workers Connected')
        plt.title('Number of Workers Connected')
        plt.ylim(0, total_workers)  # Set y-axis limit to the total number of workers
        plt.xticks(rotation=45)
        plt.tight_layout()  # Ensure the x-labels fit into the plot
        plt.savefig(os.path.join(charts_folder, 'workers_connected_bar_chart.png'))
        plt.close()
    else:
        generate_placeholder_image(os.path.join(charts_folder, 'workers_connected_bar_chart.png'))

    # Line graph for average, max, and min hashrate over 24 hours
    now = datetime.now()
    last_24_hours = now - timedelta(hours=24)
    hashrate_stats = worker_stats[worker_stats['timestamp'] > last_24_hours]
    
    # Group by hour and calculate statistics
    hashrate_stats = hashrate_stats.groupby(pd.Grouper(key='timestamp', freq='h'))['hash_rate'].agg(['mean', 'max', 'min'])

    # Ensure all hours are present in the index
    if not hashrate_stats.empty:
        all_hours = pd.date_range(start=hashrate_stats.index.min(), end=hashrate_stats.index.max(), freq='h')
        hashrate_stats = hashrate_stats.reindex(all_hours, fill_value=0)

        # Fill NaN values with zeros
        hashrate_stats = hashrate_stats.fillna(0)

        

        if not hashrate_stats.empty:
            plt.figure(figsize=(12, 8))
            hashrate_stats['mean'].plot(label='Average Hashrate')
            hashrate_stats['max'].plot(label='Max Hashrate')
            hashrate_stats['min'].plot(label='Min Hashrate')
            plt.xlabel('Hour')
            plt.ylabel('Hashrate')
            plt.title('Hashrate Statistics Over Last 24 Hours')
            plt.legend()
            plt.savefig(os.path.join(charts_folder, 'hashrate_stats_line_graph.png'))
            plt.close()
        else:
            generate_placeholder_image(os.path.join(charts_folder, 'hashrate_stats_line_graph.png'))
    else:
        generate_placeholder_image(os.path.join(charts_folder, 'hashrate_stats_line_graph.png'))

def parse_data_generate_charts():
    data = parse_json_files(data_folder)
    worker_stats = process_data(data)
    
    generate_charts(worker_stats)

def main():
    parse_data_generate_charts()

if __name__ == "__main__":
    main()